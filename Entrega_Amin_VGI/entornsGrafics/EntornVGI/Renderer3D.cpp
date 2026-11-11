#include "pch.h"
#include "Renderer3D.h"
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtx/quaternion.hpp>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iterator>
#include <stdexcept>
namespace galaga {
namespace {
GLuint compileFile(GLenum type,const wchar_t* name){
    const auto path=Renderer2D::executableDirectory()/L"shaders"/name;
    std::ifstream input(path,std::ios::binary);
    std::string source((std::istreambuf_iterator<char>(input)),{});
    if(source.empty())throw std::runtime_error("Falta un shader Galaga3D junto al ejecutable.");
    const char* p=source.c_str();GLuint sh=glCreateShader(type);glShaderSource(sh,1,&p,nullptr);glCompileShader(sh);
    GLint ok=0;glGetShaderiv(sh,GL_COMPILE_STATUS,&ok);
    if(!ok){char log[4096]{};glGetShaderInfoLog(sh,sizeof(log),nullptr,log);glDeleteShader(sh);throw std::runtime_error(log);}
    return sh;
}
glm::mat4 transform(glm::vec3 position,glm::vec3 scale=glm::vec3(1),float angle=0){
    // Column vectors: scale locally, rotate locally, translate in world space.
    return glm::translate(glm::mat4(1),position)*glm::rotate(glm::mat4(1),angle,glm::vec3(0,0,1))*glm::scale(glm::mat4(1),scale);
}
}
void Renderer3D::initialize(){
    if(!GLEW_VERSION_3_3)throw std::runtime_error("Falta el motor grafico incluido. Ejecuta build-demo.cmd o usa la carpeta completa dist/Galaga3D, con opengl32.dll.");
    GLuint v=0,f=0;
    try{
        v=compileFile(GL_VERTEX_SHADER,L"galaga3d.vert");f=compileFile(GL_FRAGMENT_SHADER,L"galaga3d.frag");
        program=glCreateProgram();glAttachShader(program,v);glAttachShader(program,f);glLinkProgram(program);
        glDeleteShader(v);v=0;glDeleteShader(f);f=0;
        GLint ok=0;glGetProgramiv(program,GL_LINK_STATUS,&ok);
        if(!ok){char log[4096]{};glGetProgramInfoLog(program,sizeof(log),nullptr,log);throw std::runtime_error(log);}
        auto uniform=[&](const char* name){int loc=glGetUniformLocation(program,name);if(loc<0)throw std::runtime_error(std::string("Uniform no activo: ")+name);return loc;};
        modelLocation=uniform("model");viewLocation=uniform("view");projectionLocation=uniform("projection");
        normalLocation=uniform("normalMatrix");tintLocation=uniform("tint");eyeLocation=uniform("eye");
        emissionLocation=uniform("material.emission");
        ambientLocation=uniform("material.ambient");
        diffuseLocation=uniform("material.diffuse");
        specularLocation=uniform("material.specular");
        shininessLocation=uniform("material.shininess");
        lightPositionLocation=uniform("light.position");
        lightDiffuseLocation=uniform("light.diffuse");
        lightSpecularLocation=uniform("light.specular");
        ambientLightLocation=uniform("ambientLight");
        models.initialize(Renderer2D::executableDirectory()/L"Recursos_Galaga3D"/L"modelos");hud.initialize();
    }catch(...){if(v)glDeleteShader(v);if(f)glDeleteShader(f);release();throw;}
}
void Renderer3D::release(){hud.release();models.release();if(program)glDeleteProgram(program);program=0;}
void Renderer3D::begin3D(){
    glDisable(GL_BLEND);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LESS);glDepthMask(GL_TRUE);
    glEnable(GL_CULL_FACE);glCullFace(GL_BACK);glFrontFace(GL_CCW);glUseProgram(program);draws=0;
    glUniformMatrix4fv(viewLocation,1,GL_FALSE,glm::value_ptr(view));
    glUniformMatrix4fv(projectionLocation,1,GL_FALSE,glm::value_ptr(projection));
    glUniform3fv(eyeLocation,1,glm::value_ptr(eye));
    // One directional source, using the material/light uniforms from GL-6.
    glUniform4f(lightPositionLocation,-.45f,.7f,1.1f,0.f);
    glUniform3f(lightDiffuseLocation,1.f,1.f,1.f);
    glUniform3f(lightSpecularLocation,1.f,1.f,1.f);
    glUniform3f(ambientLightLocation,1.f,1.f,1.f);
}
void Renderer3D::camera(bool menu,float playerX){
    if(menu){eye={0,0,12};view=glm::lookAt(eye,glm::vec3(0),glm::vec3(0,1,0));projection=glm::ortho(-6.4f,6.4f,-3.6f,3.6f,.1f,40.f);}
    else{
        // Behind the ship: +Y is forward and +Z is up in the game world.
        const float follow=playerX*.15f;
        eye={follow,-16,6};
        view=glm::lookAt(eye,glm::vec3(follow,8,0),glm::vec3(0,0,1));
        projection=glm::perspective(glm::radians(38.f),1280.f/720.f,.1f,100.f);
    }
}
void Renderer3D::instance(const Mesh3D& mesh,const glm::mat4& model,glm::vec4 tint,float emission){
    // No vertex uploads here. The same VAO/VBO is reused by every instance.
    const glm::mat3 normal=glm::transpose(glm::inverse(glm::mat3(model)));
    glUniformMatrix4fv(modelLocation,1,GL_FALSE,glm::value_ptr(model));
    glUniformMatrix3fv(normalLocation,1,GL_FALSE,glm::value_ptr(normal));
    glUniform4fv(tintLocation,1,glm::value_ptr(tint));
    const float emissive = std::clamp(emission,0.f,1.f);
    const float reflected = 1.f-emissive;
    glUniform3f(emissionLocation,emissive,emissive,emissive);
    glUniform3f(ambientLocation,.37f*reflected,.37f*reflected,.37f*reflected);
    glUniform3f(diffuseLocation,.63f*reflected,.63f*reflected,.63f*reflected);
    glUniform3f(specularLocation,.16f*reflected,.16f*reflected,.16f*reflected);
    glUniform1f(shininessLocation,32.f);
    mesh.draw();++draws;
}
void Renderer3D::draw(const Game3D& g,int width,int height){
    if(width<=0||height<=0||!program)return;
    hud.background(g,width,height);camera(g.phase==Phase::Menu,g.player.x);begin3D();
    if(g.phase==Phase::Menu){
        for(int i=0;i<3;++i){
            glm::mat4 model=glm::translate(glm::mat4(1),glm::vec3((i-1)*3.f,-.08f,0));
            model=glm::rotate(model,glm::radians(-18.f),glm::vec3(1,0,0));
            model=glm::rotate(model,glm::radians(i==g.selectedShip?20.f:-12.f),glm::vec3(0,1,0));
            model=glm::scale(model,glm::vec3(1.35f));
            instance(models.ships[i],model);
        }
    }else{
        instance(models.scenery,glm::mat4(1));
        for(const auto& e:g.enemies)if(e.alive&&e.timer>=0){
            auto model=transform({e.pos.x,e.pos.y,e.z},glm::vec3(Game3D::EnemyScale));
            // A fixed pitch keeps the silhouette readable from the chase camera.
            model=glm::rotate(model,glm::radians(35.f),glm::vec3(1,0,0));
            instance(models.enemies[e.type%2],model);
        }
        for(const auto& b:g.bullets){
            auto model=transform({b.pos.x,b.pos.y,b.z});
            const glm::vec3 direction = glm::normalize(glm::vec3(b.velocityX,b.forwardSpeed(),b.velocityZ));
            model *= glm::toMat4(glm::rotation(glm::vec3(0,1,0),direction));
            instance(b.ally?models.shot:models.enemyShot,model,glm::vec4(1),1.f);
        }
        if(g.respawn==0)
            instance(models.ships[g.selectedShip],transform({g.player.x,g.player.y,0}));
    }
    glBindVertexArray(0);
    hud.overlay(g,width,height);
}
bool Renderer3D::verifyGpu(std::ostream& report) const{
    GLint linked=0;glGetProgramiv(program,GL_LINK_STATUS,&linked);
    bool ok=linked&&models.verifyGpu()&&models.uploadCount()==10&&modelLocation>=0&&viewLocation>=0&&projectionLocation>=0;
    report<<(ok?"PASS ":"FAIL ")<<"3D GPU meshes: "<<models.uploadCount()<<" static uploads, "<<models.vertexCount()/3
          <<" triangles; VAO attributes 0/1/2/3; model/view/projection uniforms active\n";
    return ok;
}
bool Renderer3D::verifyLighting(std::ostream& report) {
    // The caller supplies a 64x64 RGBA8 framebuffer with a depth attachment.
    // Sample the +Z face of the existing cube under isolated GL-6 terms.
    camera(true);
    glViewport(0,0,64,64);
    begin3D();
    instance(models.particle,glm::scale(glm::mat4(1),glm::vec3(3)));
    struct Sample {
        const char* name;
        float ambient,diffuse,specular,emission,lightZ,expected;
    };
    const Sample samples[] = {
        {"ambient",.25f,0,0,0,1,.25f},
        {"Lambert front",0,.5f,0,0,1,.5f},
        {"unlit back",0,.5f,.5f,0,-1,0},
        {"Phong reflection",0,0,.4f,0,1,.4f},
        {"emissive",0,0,0,.7f,-1,.7f},
        {"additive terms",.2f,.3f,0,.1f,1,.6f}
    };
    const float base[] = {.94f,.96f,1.f};
    bool correct=true;
    for(const auto& sample:samples) {
        glClearColor(0,0,0,1);
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
        glUniform4f(lightPositionLocation,0,0,sample.lightZ,0);
        glUniform3f(ambientLocation,sample.ambient,sample.ambient,sample.ambient);
        glUniform3f(diffuseLocation,sample.diffuse,sample.diffuse,sample.diffuse);
        glUniform3f(specularLocation,sample.specular,sample.specular,sample.specular);
        glUniform3f(emissionLocation,sample.emission,sample.emission,sample.emission);
        models.particle.draw();
        unsigned char pixel[4]{};
        glReadPixels(32,32,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);
        bool matches=true;
        for(int channel=0;channel<3;++channel)
            matches &= std::abs(float(pixel[channel])-255.f*base[channel]*sample.expected)<3.f;
        report<<(matches?"PASS ":"FAIL ")<<"GL-6 shader term "<<sample.name<<"\n";
        correct &= matches;
    }
    glBindVertexArray(0);
    return correct && glGetError()==GL_NO_ERROR;
}
bool Renderer3D::verifyFraming(const Game3D& game,std::ostream& report) {
    camera(false,game.player.x);
    auto project=[&](glm::vec3 point) {
        const glm::vec4 clip=projection*view*glm::vec4(point,1);
        return glm::vec2((clip.x/clip.w+1)*640,(1-clip.y/clip.w)*360);
    };
    float minimumWidth=1280,formationLeft=1280,formationRight=0;
    bool readable=true;
    for(const auto& enemy:game.enemies) {
        if(!enemy.alive)continue;
        const glm::vec3 centre(enemy.pos.x,enemy.pos.y,enemy.z);
        const auto left=project(centre-glm::vec3(Game3D::EnemyHitRadius,0,0));
        const auto right=project(centre+glm::vec3(Game3D::EnemyHitRadius,0,0));
        const auto screen=project(centre);
        minimumWidth=std::min(minimumWidth,right.x-left.x);
        formationLeft=std::min(formationLeft,left.x);
        formationRight=std::max(formationRight,right.x);
        readable &= screen.y>145 && screen.y<480 && left.x>20 && right.x<1260;
    }
    const auto& ship = models.ships[game.selectedShip];
    for(float x:{ship.minimum().x,ship.maximum().x})for(float y:{ship.minimum().y,ship.maximum().y})for(float z:{ship.minimum().z,ship.maximum().z}) {
        const auto corner=project(glm::vec3(game.player.x+x,game.player.y+y,z));
        readable &= corner.x>12 && corner.x<1268 && corner.y>480 && corner.y<640;
    }
    readable &= minimumWidth>=34 && formationRight-formationLeft>=400;
    report<<(readable?"PASS ":"FAIL ")<<"framing at player X="<<game.player.x
          <<"; smallest target "<<minimumWidth<<"px; formation width "<<formationRight-formationLeft<<"px\n";
    return readable;
}
void Renderer3D::modelGallery(int width,int height,float angle,bool wireframe){
    Game3D gallery;gallery.phase=Phase::Playing;hud.background(gallery,width,height);camera(true);begin3D();
    glPolygonMode(GL_FRONT_AND_BACK,wireframe?GL_LINE:GL_FILL);
    for(int i=0;i<6;++i){
        auto model=glm::translate(glm::mat4(1),glm::vec3((i%3-1)*3.4f,i<3?1.5f:-1.5f,0));
        model=glm::rotate(model,glm::radians(-24.f),glm::vec3(1,0,0));
        model=glm::rotate(model,angle,glm::vec3(0,1,0));model=glm::scale(model,glm::vec3(1.6f));
        instance(i<3?models.ships[i]:models.enemies[i-3],model);
    }
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL);
    glBindVertexArray(0);glUseProgram(0);
}
}
