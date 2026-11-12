#include "pch.h"
#include "Renderer2D.h"
#include <gl/SOIL2.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
namespace galaga {
std::filesystem::path Renderer2D::executableDirectory() {
    wchar_t path[32768]{};GetModuleFileNameW(nullptr,path,32768);
    return std::filesystem::path(path).parent_path();
}
void Renderer2D::initialize() {
    const char* vs=R"(#version 330 core
layout(location=0) in vec2 position;
layout(location=1) in vec2 uv;
layout(location=2) in vec4 color;
out vec2 texCoord;out vec4 tint;
void main(){gl_Position=vec4(position.x/640.0-1.0,1.0-position.y/360.0,0,1);texCoord=uv;tint=color;})";
    const char* fs=R"(#version 330 core
in vec2 texCoord;in vec4 tint;out vec4 outColor;uniform sampler2D image;
void main(){outColor=texture(image,texCoord)*tint;})";
    auto compile=[](GLenum type,const char* source) {
        GLuint sh=glCreateShader(type);glShaderSource(sh,1,&source,nullptr);glCompileShader(sh);
        GLint ok=0;glGetShaderiv(sh,GL_COMPILE_STATUS,&ok);
        if(!ok){char log[2048]{};glGetShaderInfoLog(sh,2048,nullptr,log);glDeleteShader(sh);throw std::runtime_error(log);}return sh;
    };
    GLuint v=compile(GL_VERTEX_SHADER,vs),f=compile(GL_FRAGMENT_SHADER,fs);
    program=glCreateProgram();glAttachShader(program,v);glAttachShader(program,f);glLinkProgram(program);
    glDeleteShader(v);glDeleteShader(f);
    GLint ok=0;glGetProgramiv(program,GL_LINK_STATUS,&ok);
    if(!ok)throw std::runtime_error("No se ha podido enlazar el shader HUD.");
    glGenVertexArrays(1,&vao);glGenBuffers(1,&vbo);
    glBindVertexArray(vao);glBindBuffer(GL_ARRAY_BUFFER,vbo);
    glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),nullptr);
    glEnableVertexAttribArray(1);glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)(2*sizeof(float)));
    glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)(4*sizeof(float)));
    auto texture=[](GLuint& id,int w,int h,const unsigned char* data){
        glGenTextures(1,&id);glBindTexture(GL_TEXTURE_2D,id);
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,data);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
    };
    unsigned char pixel[]={255,255,255,255};texture(white,1,1,pixel);
    // Original 5x7 glyph atlas generated once. No installed-font dependency.
    const char* glyphs="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:/.-+[]!<>";
    const unsigned char rows[][7]={
      {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{15,16,16,16,16,16,15},
      {30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
      {15,16,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},
      {7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
      {17,27,21,21,17,17,17},{17,25,25,21,19,19,17},{14,17,17,17,17,17,14},
      {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
      {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
      {17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
      {17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
      {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
      {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
      {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},{14,17,17,15,1,1,14},
      {0,4,4,0,4,4,0},{1,1,2,4,8,16,16},{0,0,0,0,0,6,6},{0,0,0,31,0,0,0},
      {0,4,4,31,4,4,0},{14,8,8,8,8,8,14},{14,2,2,2,2,2,14},{4,4,4,4,4,0,4},
      {2,4,8,16,8,4,2},{8,4,2,1,2,4,8}};
    std::array<unsigned char,128*64*4> atlas{};
    for(int i=0;glyphs[i];++i){unsigned ch=unsigned(glyphs[i]);int x=(ch%16)*8,y=(ch/16)*8;
        for(int r=0;r<7;++r)for(int c=0;c<5;++c)if(rows[i][r]&(1<<(4-c))){auto p=((y+r)*128+x+c)*4;atlas[p]=atlas[p+1]=atlas[p+2]=atlas[p+3]=255;}}
    texture(font,128,64,atlas.data());glBindVertexArray(0);
}
void Renderer2D::release(){if(scoreLabel)glDeleteTextures(1,&scoreLabel);if(font)glDeleteTextures(1,&font);if(white)glDeleteTextures(1,&white);if(vbo)glDeleteBuffers(1,&vbo);if(vao)glDeleteVertexArrays(1,&vao);if(program)glDeleteProgram(program);scoreLabel=font=white=vbo=vao=program=0;}
void Renderer2D::begin(int width,int height){
    glDisable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);glDepthMask(GL_TRUE);glDisable(GL_CULL_FACE);glPolygonMode(GL_FRONT_AND_BACK,GL_FILL);
    float s=std::min(width/1280.f,height/720.f);int vw=int(1280*s),vh=int(720*s);glViewport((width-vw)/2,(height-vh)/2,vw,vh);
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
    glUseProgram(program);glUniform1i(glGetUniformLocation(program,"image"),0);glActiveTexture(GL_TEXTURE0);
    glBindVertexArray(vao);glBindBuffer(GL_ARRAY_BUFFER,vbo);
}
void Renderer2D::finish(){
    flush();
    // One upload for the complete HUD pass; retain draw ordering for overlays.
    glBufferData(GL_ARRAY_BUFFER,vertices.size()*sizeof(Vertex),vertices.data(),GL_STREAM_DRAW);
    for(const auto& batch:batches){glBindTexture(GL_TEXTURE_2D,batch.texture);glDrawArrays(GL_TRIANGLES,batch.first,batch.count);}
    vertices.clear();batches.clear();pendingStart=0;
    glBindVertexArray(0);glUseProgram(0);glDisable(GL_BLEND);
}
void Renderer2D::flush(unsigned int texture){
    int count=int(vertices.size())-pendingStart;if(count<=0)return;
    batches.push_back({texture?texture:white,pendingStart,count});pendingStart+=count;
}
void Renderer2D::quad(float x,float y,float w,float h,Color c,float u1,float v1,float u2,float v2){
    Vertex a{x,y,u1,v1,c.r,c.g,c.b,c.a},b{x+w,y,u2,v1,c.r,c.g,c.b,c.a},d{x,y+h,u1,v2,c.r,c.g,c.b,c.a},e{x+w,y+h,u2,v2,c.r,c.g,c.b,c.a};vertices.insert(vertices.end(),{a,b,e,a,e,d});
}
void Renderer2D::image(unsigned int texture,float x,float y,float w,float h){
    flush();quad(x,y,w,h,{1,1,1,1});flush(texture);
}
void Renderer2D::border(float x,float y,float w,float h,Color c){quad(x,y,w,2,c);quad(x,y+h-2,w,2,c);quad(x,y,2,h,c);quad(x+w-2,y,2,h,c);}
void Renderer2D::text(const std::string& value,float x,float y,int height,Color c,bool center){
    flush();float unit=height/7.f,advance=unit*6;if(center)x-=(value.size()*advance-unit)*.5f;
    for(unsigned char ch:value){if(ch>='a'&&ch<='z')ch-=32;if(ch>127)ch=' ';float u=float((ch%16)*8)/128,v=float((ch/16)*8)/64;quad(x,y,unit*5,float(height),c,u,v,u+5.f/128,v+7.f/64);x+=advance;}flush(font);
}
void Renderer2D::background(const Game3D& g,int width,int height){
    begin(width,height);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    quad(0,0,1280,720,{0,0,0});
    if(g.phase==Phase::Menu){for(int i=0;i<3;++i){float x=215+i*300.f;bool selected=i==g.selectedShip;quad(x,257,250,242,selected?Color{.055f,.06f,.07f}:Color{.025f,.028f,.032f});border(x,257,250,242,selected?Color{1,.8f,.25f}:Color{.15f,.17f,.19f});if(selected)quad(x,257,250,3,{1,.8f,.25f});}}
    finish();
}
void Renderer2D::overlay(const Game3D& g,int width,int height){
    begin(width,height);
    const Color whiteC{.91f,.94f,.98f},yellow{1,.83f,.25f},red{1,.3f,.22f},blue{.43f,.83f,.95f},muted{.53f,.59f,.65f};
    const char* ships[]={"FLECHA","DELTA","DOBLE MOTOR"};
    if(g.phase==Phase::Menu){
        text("GALAGA 3D",640,71,52,whiteC,true);text("SECTOR ORBITAL",640,148,17,yellow,true);
        text("ELIGE TU NAVE",640,216,18,whiteC,true);
        for(int i=0;i<3;++i){float x=340+i*300.f;text(std::to_string(i+1),x-100,277,14,i==g.selectedShip?yellow:muted);text(ships[i],x,461,17,i==g.selectedShip?yellow:whiteC,true);}
        text("1 / 2 / 3  SELECCIONAR",640,530,14,muted,true);
        text("ENTER  EMPEZAR",640,578,24,yellow,true);
        text("WASD / FLECHAS  VOLAR     ESPACIO  DISPARAR     1-4  ARMAS",640,637,12,whiteC,true);
        text("3 COMBATES + 2 ESQUIVAS + JEFE FINAL    Q MISIL    P PAUSA    M AUDIO    F2 MALLA",640,678,10,muted,true);
    }else{
        // One quiet information band; no target boxes or aim overlay.
        quad(0,0,1280,83,{.012f,.016f,.02f,.8f});
        text("PUNTOS",30,19,11,muted);text(std::to_string(g.score),30,42,22,whiteC);
        if(g.multiplier>1)text("X"+std::to_string(g.multiplier),185,48,14,yellow);
        const std::string stage=g.stage==Stage::Combat?"COMBATE "+std::to_string(g.wave)+" / 3":g.stage==Stage::Evasion?"ESQUIVA "+std::to_string(g.wave)+" / 2":"JEFE FINAL";
        text(stage,640,20,14,whiteC,true);
        if(g.stage==Stage::Evasion)
            text("RESISTE  "+std::to_string(std::max(0,int(std::ceil(g.stageDuration-g.stageTime))))+" S",640,49,12,yellow,true);
        else text(g.stage==Stage::Boss?"ACORAZADO":"HOSTILES  "+std::to_string(g.remaining()),640,49,11,muted,true);
        text("VIDAS",1000,19,11,muted);
        for(int i=0;i<3;++i)quad(1062+i*18.f,18,11,12,i<g.lives?blue:Color{.16f,.19f,.21f});
        const char* weapons[]={"SIMPLE","DOBLE","TRIPLE","MISIL"};
        text(g.stage==Stage::Evasion?"MODO  CABINA":"ARMA  "+std::string(weapons[int(g.weapon)]),1000,46,12,whiteC);
        if(g.lives>0){
            if(g.respawn>0)text("REAPARECIENDO",1000,67,9,red);
            else if(g.invulnerable>0)text("ESCUDO  "+std::to_string(int(std::ceil(g.invulnerable)))+" S",1000,67,9,blue);
        }
        if(g.stage==Stage::Boss){
            quad(460,88,360,5,{.2f,.13f,.11f});
            quad(460,88,360.f*std::max(0,g.bossHealth)/std::max(1,g.bossMaxHealth),5,red);
        }
        quad(0,688,1280,32,{.012f,.016f,.02f,.75f});
        text(g.stage==Stage::Evasion?"WASD / FLECHAS  ESQUIVAR":"WASD VOLAR   ESPACIO DISPARAR   1-4 ARMAS",30,700,10,muted);
        text("P PAUSA   M AUDIO   F2 MALLA",640,700,10,muted,true);
        const std::string special=g.specialCooldown<=0?"Q  MISIL LISTO":"Q  RECARGA "+std::to_string(int(std::ceil(g.specialCooldown)))+" S";
        text(g.stage==Stage::Evasion?"ARMAS EN ESPERA":special,1062,700,10,g.stage!=Stage::Evasion&&g.specialCooldown<=0?yellow:muted);
        if(g.stageTime<(g.stage==Stage::Evasion?2.4f:1.6f)&&g.phase==Phase::Playing){
            text(g.stage==Stage::Evasion?"CABINA - BUSCA LOS HUECOS":g.stage==Stage::Boss?"ACORAZADO EN APROXIMACION":"FORMACION EN APROXIMACION",640,111,15,yellow,true);
        }
        if(g.damageFlash>0&&g.phase==Phase::Playing){
            const Color damage{1,.19f,.08f,.8f*g.damageFlash/.35f};
            quad(0,83,1280,5,damage);quad(0,683,1280,5,damage);
            quad(0,88,5,595,damage);quad(1275,88,5,595,damage);
        }
        if(g.phase==Phase::Paused||g.phase==Phase::Victory||g.phase==Phase::Defeat){
            quad(0,83,1280,605,{0,0,0,.65f});quad(320,205,640,340,{.035f,.04f,.048f,.97f});border(320,205,640,340,{.24f,.28f,.31f});
            text(g.phase==Phase::Paused?"PAUSA":g.phase==Phase::Victory?"SECTOR LIBERADO":"NAVE DESTRUIDA",640,247,30,g.phase==Phase::Defeat?red:yellow,true);
            text(g.phase==Phase::Paused?"WASD / FLECHAS  MOVER EN X Y ALTURA":"PUNTOS  "+std::to_string(g.score),640,316,14,whiteC,true);
            const bool evasionPause=g.phase==Phase::Paused&&g.stage==Stage::Evasion;
            text(g.phase==Phase::Paused?(evasionPause?"BUSCA UN HUECO ENTRE LOS ASTEROIDES":"1 SIMPLE   2 DOBLE   3 TRIPLE   4 MISIL"):"BAJAS  "+std::to_string(g.kills)+"    TIEMPO  "+std::to_string(int(g.time))+" S",640,356,12,muted,true);
            text(g.phase==Phase::Paused?(evasionPause?"ARMAS EN ESPERA DURANTE LA ESQUIVA":"ESPACIO DISPARAR   Q MISIL ESPECIAL"):"RECORD  "+std::to_string(std::max(g.bestScore,g.score)),640,391,12,muted,true);
            text(g.phase==Phase::Paused?"P  CONTINUAR":"R  VOLVER A JUGAR",640,452,18,whiteC,true);text("ESC  ELEGIR NAVE",640,503,12,muted,true);
        }
    }
    finish();
}
}
