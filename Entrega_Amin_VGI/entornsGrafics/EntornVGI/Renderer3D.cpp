#include "pch.h"
#include "Renderer3D.h"
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
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
        normalLocation=uniform("normalMatrix");tintLocation=uniform("tint");eyeLocation=uniform("eye");emissionLocation=uniform("emission");
        models.initialize();hud.initialize();
    }catch(...){if(v)glDeleteShader(v);if(f)glDeleteShader(f);release();throw;}
}
void Renderer3D::release(){hud.release();models.release();if(program)glDeleteProgram(program);program=0;}
void Renderer3D::begin3D(){
    glDisable(GL_BLEND);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LESS);glDepthMask(GL_TRUE);
    glEnable(GL_CULL_FACE);glCullFace(GL_BACK);glFrontFace(GL_CCW);glUseProgram(program);draws=0;
    glUniformMatrix4fv(viewLocation,1,GL_FALSE,glm::value_ptr(view));
    glUniformMatrix4fv(projectionLocation,1,GL_FALSE,glm::value_ptr(projection));
    glUniform3fv(eyeLocation,1,glm::value_ptr(eye));
}
void Renderer3D::camera(bool menu){
    if(menu){eye={0,0,12};view=glm::lookAt(eye,glm::vec3(0),glm::vec3(0,1,0));projection=glm::ortho(-6.4f,6.4f,-3.6f,3.6f,.1f,40.f);}
    else{eye={0,-4.5f,22};view=glm::lookAt(eye,glm::vec3(0,1,0),glm::vec3(0,1,0));projection=glm::perspective(glm::radians(40.f),1280.f/720.f,.1f,100.f);}
}
void Renderer3D::instance(const Mesh3D& mesh,const glm::mat4& model,glm::vec4 tint,float emission){
    // No vertex uploads here. The same VAO/VBO is reused by every instance.
    const glm::mat3 normal=glm::transpose(glm::inverse(glm::mat3(model)));
    glUniformMatrix4fv(modelLocation,1,GL_FALSE,glm::value_ptr(model));
    glUniformMatrix3fv(normalLocation,1,GL_FALSE,glm::value_ptr(normal));
    glUniform4fv(tintLocation,1,glm::value_ptr(tint));glUniform1f(emissionLocation,emission);
    mesh.draw();++draws;
}
void Renderer3D::draw(const Game3D& g,int width,int height){
    if(width<=0||height<=0||!program)return;
    hud.background(g,width,height);camera(g.phase==Phase::Menu);begin3D();
    if(g.phase==Phase::Menu){
        for(int i=0;i<3;++i){
            glm::mat4 model=glm::translate(glm::mat4(1),glm::vec3((i-1)*3.f,-.08f,0));
            model=glm::rotate(model,glm::radians(-18.f),glm::vec3(1,0,0));
            model=glm::rotate(model,glm::radians(i==g.selectedShip?20.f:-12.f),glm::vec3(0,1,0));
            model=glm::scale(model,glm::vec3(1.35f));
            instance(models.ships[i],model);
        }
    }else{
        for(const auto& e:g.enemies)if(e.alive&&e.timer>=0){
            float dx=e.pos.x-e.previous.x,dy=e.pos.y-e.previous.y;
            float angle=(e.phase==EnemyPhase::Diving||e.phase==EnemyPhase::Returning||e.phase==EnemyPhase::Entering)&&dx*dx+dy*dy>.00001f?std::atan2(dx,-dy):0;
            auto model=transform({e.pos.x,e.pos.y,e.z},glm::vec3(1),angle);
            // A small pitch exposes the thickness of the insect wings during flight.
            if(e.phase==EnemyPhase::Diving)model=glm::rotate(model,.28f*std::sin(e.timer*3),glm::vec3(1,0,0));
            float warning=e.phase==EnemyPhase::Warning?.25f+.2f*std::sin(g.time*24):0;
            instance(models.enemies[e.type%2],model,glm::vec4(1),warning);
        }
        for(const auto& b:g.bullets){
            auto model=transform({b.pos.x,b.pos.y,b.z});
            if(!b.ally)model=glm::rotate(model,std::atan2(-b.velocityZ,4.f),glm::vec3(1,0,0));
            instance(b.ally?models.shot:models.enemyShot,model,glm::vec4(1),.55f);
        }
        for(const auto& s:g.sparks)for(int i=0;i<12;++i){
            float a=i*6.2831853f/12,r=.12f+s.age*3.4f,scale=.095f*(1-s.age/.45f);
            if(scale<=0)continue;
            auto model=transform({s.pos.x+std::cos(a)*r,s.pos.y+std::sin(a)*r,s.z+std::sin(i*3.f)*r},glm::vec3(scale),a+s.age*9);
            instance(models.particle,model,s.player?glm::vec4(.35f,.8f,1,1):glm::vec4(1,.6f,.15f,1),.8f);
        }
        if(g.respawn==0&&(g.invulnerable<=0||int(g.time*12)%2==0)){
            // The player has one degree of freedom: world X. No bank or plane switch.
            instance(models.ships[g.selectedShip],transform({g.player.x,g.player.y,0}));
            if(g.phase==Phase::Playing){
                float length=.16f+.06f*std::sin(g.time*32);
                for(float x:{-.31f,.31f})instance(models.particle,transform({g.player.x+x,g.player.y-.72f,0},glm::vec3(.07f,length,.07f)),glm::vec4(1,.45f,.12f,1),1);
            }
        }
    }
    glBindVertexArray(0);hud.overlay(g,width,height);
}
bool Renderer3D::verifyGpu(std::ostream& report) const{
    GLint linked=0;glGetProgramiv(program,GL_LINK_STATUS,&linked);
    bool ok=linked&&models.verifyGpu()&&models.uploadCount()==9&&modelLocation>=0&&viewLocation>=0&&projectionLocation>=0;
    report<<(ok?"PASS ":"FAIL ")<<"3D GPU meshes: "<<models.uploadCount()<<" static uploads, "<<models.vertexCount()/3
          <<" triangles; VAO attributes 0/1/2/3; model/view/projection uniforms active\n";
    return ok;
}
void Renderer3D::modelGallery(int width,int height,float angle){
    Game3D menu;hud.background(menu,width,height);camera(true);begin3D();
    for(int i=0;i<6;++i){
        auto model=glm::translate(glm::mat4(1),glm::vec3((i%3-1)*3.4f,i<3?1.5f:-1.5f,0));
        model=glm::rotate(model,glm::radians(-24.f),glm::vec3(1,0,0));
        model=glm::rotate(model,angle,glm::vec3(0,1,0));model=glm::scale(model,glm::vec3(1.6f));
        instance(i<3?models.ships[i]:models.enemies[i-3],model);
    }
    glBindVertexArray(0);glUseProgram(0);
}
}
