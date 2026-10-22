#include "pch.h"
#include "Renderer2D.h"
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
void Renderer2D::release(){if(font)glDeleteTextures(1,&font);if(white)glDeleteTextures(1,&white);if(vbo)glDeleteBuffers(1,&vbo);if(vao)glDeleteVertexArrays(1,&vao);if(program)glDeleteProgram(program);font=white=vbo=vao=program=0;}
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
void Renderer2D::border(float x,float y,float w,float h,Color c){quad(x,y,w,2,c);quad(x,y+h-2,w,2,c);quad(x,y,2,h,c);quad(x+w-2,y,2,h,c);}
void Renderer2D::text(const std::string& value,float x,float y,int height,Color c,bool center){
    flush();float unit=height/7.f,advance=unit*6;if(center)x-=(value.size()*advance-unit)*.5f;
    for(unsigned char ch:value){if(ch>='a'&&ch<='z')ch-=32;if(ch>127)ch=' ';float u=float((ch%16)*8)/128,v=float((ch/16)*8)/64;quad(x,y,unit*5,float(height),c,u,v,u+5.f/128,v+7.f/64);x+=advance;}flush(font);
}
void Renderer2D::background(const Game3D& g,int width,int height){
    begin(width,height);glClearColor(.005f,.007f,.015f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    quad(0,0,1280,720,{.003f,.004f,.011f});
    for(int i=0;i<140;++i){float x=float((i*137+71)%1260+10),y=std::fmod(i*79.f+g.time*(i%3+1)*3,720.f);Color c=i%5==0?Color{.35f,.5f,1,.6f}:i%7==0?Color{1,.3f,.25f,.6f}:Color{.8f,.85f,.9f,.45f};quad(x,y,i%4?1.3f:2.f,i%4?1.3f:2.f,c);}
    if(g.phase==Phase::Menu){for(int i=0;i<3;++i){float x=215+i*300.f;bool selected=i==g.selectedShip;quad(x,257,250,242,selected?Color{.043f,.055f,.083f,.94f}:Color{.022f,.029f,.045f,.9f});border(x,257,250,242,selected?Color{1,.8f,.18f}:Color{.16f,.20f,.27f});if(selected)quad(x,257,250,4,{1,.8f,.18f});}}
    finish();
}
void Renderer2D::overlay(const Game3D& g,int width,int height){
    begin(width,height);
    const Color whiteC{.91f,.94f,1},yellow{1,.83f,.16f},red{1,.22f,.28f},blue{.3f,.7f,1},muted{.44f,.51f,.63f};
    const char* ships[]={"FLECHA","DELTA","DOBLE MOTOR"};
    if(g.phase==Phase::Menu){
        text("GALAGA",640,65,70,yellow,true);text("3 D",640,154,28,blue,true);
        text("ELIGE TU NAVE",640,216,18,whiteC,true);
        for(int i=0;i<3;++i){float x=340+i*300.f;text(std::to_string(i+1),x-100,277,14,i==g.selectedShip?yellow:muted);text(ships[i],x,461,17,i==g.selectedShip?yellow:whiteC,true);}
        text("1 / 2 / 3  SELECCIONAR",640,530,14,muted,true);
        text("ENTER  EMPEZAR",640,578,24,yellow,true);
        text("A/D MOVER   ESPACIO DISPARAR   P PAUSA",640,643,12,whiteC,true);
        text("UNA RONDA - 18 ENEMIGOS - 3 VIDAS",640,682,11,muted,true);
    }else{
        quad(0,0,1280,99,{.003f,.004f,.011f,.94f});
        text("1UP",65,25,16,red);text(std::to_string(g.score),65,55,24,whiteC);
        text("HIGH SCORE",640,25,16,red,true);text(std::to_string(std::max(g.score,g.bestScore)),640,55,24,whiteC,true);
        text("RONDA",1120,25,14,muted,true);text("01 / 01",1120,56,20,yellow,true);
        text(ships[g.selectedShip],65,127,12,muted);
        text("ENEMIGOS",1120,134,11,muted,true);text(std::to_string(g.remaining()),1120,162,22,whiteC,true);
        text("COMBO",1120,245,11,muted,true);text("X"+std::to_string(g.multiplier),1120,275,24,yellow,true);
        quad(0,622,1280,98,{.003f,.004f,.011f,.94f});
        text("VIDAS",65,647,12,muted);text(std::to_string(g.lives),65,675,20,yellow);
        for(int i=0;i<g.lives;++i){float x=102+i*26.f;quad(x+8,670,4,20,whiteC);quad(x,680,20,5,whiteC);quad(x,677,3,13,red);quad(x+17,677,3,13,red);}
        text("A/D MOVER   ESPACIO DISPARAR   P PAUSA",760,659,12,whiteC,true);
        if(g.invulnerable>0&&g.respawn==0&&g.phase==Phase::Playing)text("ESCUDO",640,607,10,blue,true);
        if(g.phase==Phase::Paused||g.phase==Phase::Victory||g.phase==Phase::Defeat){
            quad(0,100,1280,522,{0,0,.015f,.73f});quad(360,240,560,252,{.025f,.035f,.06f,.96f});border(360,240,560,252,{.24f,.3f,.4f});
            text(g.phase==Phase::Paused?"PAUSA":g.phase==Phase::Victory?"RONDA SUPERADA":"GAME OVER",640,278,30,g.phase==Phase::Defeat?red:yellow,true);
            text(g.phase==Phase::Paused?"TU NAVE TE ESPERA":"PUNTOS  "+std::to_string(g.score),640,345,17,whiteC,true);
            text(g.phase==Phase::Paused?"P  CONTINUAR":"R  VOLVER A JUGAR",640,412,16,whiteC,true);text("ESC  ELEGIR NAVE",640,453,12,muted,true);
        }
    }
    finish();
}
}
