#include "pch.h"
#include "Renderer2D.h"
#include "RendererFont.h"
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
    const auto fontPath=executableDirectory()/L"Recursos_Galaga3D"/L"hud"/L"instrument_font.png";
    int fw=0,fh=0,channels=0;
    auto* pixels=SOIL_load_image(fontPath.string().c_str(),&fw,&fh,&channels,SOIL_LOAD_RGBA);
    if(!pixels)throw std::runtime_error("Falta el atlas de instrumentos del HUD.");
    texture(font,fw,fh,pixels);SOIL_free_image_data(pixels);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
    glGenerateMipmap(GL_TEXTURE_2D);glBindVertexArray(0);
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
    flush();
    const float scale=height/HudCapHeight;
    auto glyph=[](unsigned char ch){if(ch>='a'&&ch<='z')ch-=32;return ch<128?ch:static_cast<unsigned char>(' ');};
    if(center){float length=0;for(unsigned char ch:value)length+=HudAdvance[glyph(ch)];x-=length*scale*.5f;}
    for(unsigned char source:value){
        const unsigned char ch=glyph(source);
        if(ch!=' '){const float u=float((ch%16)*64)/1024,v=float((ch/16)*64)/512;
            quad(x-8*scale,y-8*scale,64*scale,64*scale,c,u,v,u+64.f/1024,v+64.f/512);}
        x+=HudAdvance[ch]*scale;
    }
    flush(font);
}
void Renderer2D::panel(float x,float y,float w,float h,Color accent){
    quad(x,y,w,h,{.012f,.018f,.023f,.88f});
    quad(x,y,w,1,{.24f,.30f,.33f,.65f});
    quad(x,y,28,2,accent);quad(x+w-1,y,1,h,{.16f,.22f,.25f,.45f});
}
void Renderer2D::meter(const std::string& label,float x,float y,float w,float value,float maximum,Color color){
    const float ratio=std::clamp(value/std::max(1.f,maximum),0.f,1.f);
    text(label,x,y,10,{.58f,.65f,.68f});
    text(std::to_string(int(std::round(ratio*100)))+"%",x+w-42,y,11,color);
    quad(x,y+18,w,3,{.12f,.17f,.20f,.9f});quad(x,y+18,w*ratio,3,color);
    for(int i=1;i<4;++i)quad(x+w*i/4.f,y+17,1,5,{.34f,.4f,.43f,.5f});
}
void Renderer2D::background(const Game3D& g,int width,int height){
    begin(width,height);glClearColor(.002f,.004f,.007f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    quad(0,0,1280,720,{.002f,.004f,.007f});
    if(g.phase==Phase::Menu){
        for(int row=0;row<48;++row){const float shade=.018f+.016f*(1.f-row/48.f);
            quad(0,row*15.f,1280,15,{shade*.85f,shade*.96f,shade*1.08f});}
        quad(632,64,1,576,{.17f,.22f,.25f,.7f});
        for(int i=0;i<3;++i){float x=680+i*184.f;
            panel(x,558,166,66,i==g.selectedShip?Color{.86f,.63f,.32f}:Color{.27f,.32f,.35f});
            if(i==g.selectedShip)quad(x,622,166,2,{.86f,.63f,.32f});}
        // Hangar datum marks give the solid preview a quiet frame of reference.
        for(int i=0;i<6;++i)quad(685+i*96.f,516,30,1,{.21f,.26f,.28f,.7f});
    }
    finish();
}
void Renderer2D::overlay(const Game3D& g,int width,int height){
    begin(width,height);
    const Color whiteC{.89f,.92f,.92f},amber{.9f,.67f,.35f},red{1,.36f,.24f},cyan{.41f,.76f,.85f},muted{.54f,.62f,.66f};
    const char* ships[]={"FLECHA","DELTA","DOBLE MOTOR"};
    const char* codes[]={"F-01","D-02","M-03"};
    const char* powerNames[]={"EQUILIBRADA","MOTORES","ARMAS","ESCUDOS"};
    const char* powerNotes[]={"MOVILIDAD / FUEGO / DEFENSA","MAS VELOCIDAD / MENOS DEFENSA","MAS FUEGO / MENOR VELOCIDAD","MAS ESCUDO / MENOS FUEGO"};
    const char* weapons[]={"LASER SIMPLE","DOBLE PARALELO","TRIPLE","MISIL"};
    if(g.phase==Phase::Menu){
        text("VGI / OPERACIONES DE VUELO",64,65,11,muted);
        text("GALAGA",60,111,58,whiteC);text("SECTOR ORBITAL",64,187,17,amber);
        quad(64,226,96,2,amber);
        text("INTERCEPTA LA FORMACION",64,264,23,whiteC);
        text("DOMINA LA ENERGIA. PROTEGE TU CASCO.",64,308,12,muted);
        text("01 / ROMPE LAS OLEADAS",64,364,12,whiteC);
        text("02 / CRUZA EL CAMPO DE RESTOS",64,399,12,whiteC);
        text("03 / NEUTRALIZA EL ACORAZADO",64,434,12,whiteC);
        panel(64,506,490,77,amber);
        text("ENTER",84,526,23,amber);text("INICIAR MISION",205,530,16,whiteC);
        text("TRES CAZAS / UNA MISION",64,615,11,muted);
        text("1 / 2 / 3  SELECCIONAR NAVE",64,642,12,whiteC);
        text("HANGAR / "+std::string(codes[g.selectedShip]),680,71,12,muted);
        text("SISTEMAS LISTOS",1170,71,10,amber,true);
        text(ships[g.selectedShip],896,475,25,whiteC,true);
        for(int i=0;i<3;++i){float x=680+i*184.f;
            text(codes[i],x+14,572,9,i==g.selectedShip?amber:muted);
            text(ships[i],x+14,595,12,i==g.selectedShip?whiteC:muted);}
        text("WASD VOLAR / ESPACIO FUEGO / E ENERGIA / SHIFT IMPULSO / C CABINA",640,692,10,muted,true);
    }else{
        const bool cockpit=g.stage==Stage::Evasion||g.cockpitView;
        // Sparse instruments around the flight view; each reports real simulation state.
        panel(24,20,205,77,amber);
        text("PUNTOS",40,33,9,muted);
        std::string score=std::to_string(g.score);if(score.size()<6)score.insert(0,6-score.size(),'0');
        text(score,38,55,24,whiteC);
        if(g.multiplier>1)text("X"+std::to_string(g.multiplier),178,61,12,amber);
        const std::string stage=g.stage==Stage::Combat?"INTERCEPCION / "+std::to_string(g.wave)+" DE 3":g.stage==Stage::Evasion?"CAMPO DE RESTOS / "+std::to_string(g.wave)+" DE 2":"ACORAZADO / ASALTO FINAL";
        text(stage,640,27,13,whiteC,true);
        text(g.stage==Stage::Evasion?"SALIDA EN "+std::to_string(std::max(0,int(std::ceil(g.stageDuration-g.stageTime))))+" S":g.stage==Stage::Boss?"DESTRUYE LA NAVE DE MANDO":std::to_string(g.remaining())+" CONTACTOS HOSTILES",640,52,10,muted,true);
        if(g.stage==Stage::Boss){quad(480,76,320,3,{.2f,.12f,.09f});quad(480,76,320.f*std::max(0,g.bossHealth)/std::max(1,g.bossMaxHealth),3,amber);}
        panel(986,20,270,77,amber);
        text("E / PRIORIDAD DE ENERGIA",1002,33,9,muted);
        text(powerNames[int(g.powerMode)],1002,54,14,amber);
        for(int i=0;i<4;++i)quad(1162+i*19.f,57,12,4,int(g.powerMode)==i?amber:Color{.19f,.24f,.26f});
        text(powerNotes[int(g.powerMode)],1002,81,9,muted);

        panel(24,555,280,119,cyan);
        text("NAVE / "+std::string(ships[g.selectedShip]),40,570,10,whiteC);
        meter("CASCO",40,593,248,g.hull,Game3D::MaxHull,g.hull<35?red:whiteC);
        meter("ESCUDO",40,630,248,g.shield,Game3D::MaxShield,cyan);

        panel(976,555,280,119,g.overheated?red:amber);
        text(g.stage==Stage::Evasion?"ARMAMENTO / EN ESPERA":"1-4 / "+std::string(weapons[int(g.weapon)]),992,570,10,whiteC);
        meter(g.overheated?"ENFRIANDO LASER":"CALOR DEL LASER",992,593,248,g.weaponHeat,100,g.overheated?red:amber);
        const std::string special=g.stage==Stage::Evasion?"Q / ARMAS EN ESPERA":g.specialCooldown<=0?"Q / MISIL DISPONIBLE":"Q / MISIL EN "+std::to_string(int(std::ceil(g.specialCooldown)))+" S";
        text(special,992,638,11,g.stage!=Stage::Evasion&&g.specialCooldown<=0?cyan:muted);

        meter(g.boosting?"IMPULSO / ARMAS EN ESPERA":"SHIFT + DIRECCION / IMPULSO",454,644,372,g.boostCharge,100,g.boosting?cyan:muted);
        const std::string reserves="RESERVAS "+std::to_string(std::max(0,g.lives-1))+" / "+(cockpit?"CABINA":"CAMARA TRASERA");
        text(reserves,640,618,9,muted,true);
        if(g.respawn>0&&g.lives>0)text("DESPLEGANDO NAVE DE RESERVA",640,126,15,red,true);
        else if(g.invulnerable>.35f)text("PROTECCION DE DESPLIEGUE / "+std::to_string(int(std::ceil(g.invulnerable)))+" S",640,126,11,cyan,true);
        else if(g.stageTime<(g.stage==Stage::Evasion?2.4f:1.6f)&&g.phase==Phase::Playing)
            text(g.stage==Stage::Evasion?"BUSCA EL HUECO. CONSERVA EL IMPULSO.":g.stage==Stage::Boss?"CONTACTO PESADO EN APROXIMACION":"FORMACION EN APROXIMACION",640,126,11,amber,true);

        text(g.stage==Stage::Evasion?"WASD / FLECHAS ESQUIVAR    SHIFT IMPULSO    E ENERGIA    P PAUSA    M AUDIO":"WASD VOLAR    ESPACIO FUEGO    1-4 ARMAS    C CAMARA    P PAUSA    M AUDIO",640,701,10,muted,true);
        const float impact=std::max(g.damageFlash/.35f,g.shieldFlash/.3f);
        if(impact>0&&g.phase==Phase::Playing){
            Color flash=g.damageFlash>0?red:cyan;flash.a=.55f*std::clamp(impact,0.f,1.f);
            quad(0,0,1280,3,flash);quad(0,717,1280,3,flash);quad(0,3,3,714,flash);quad(1277,3,3,714,flash);
        }
        if(g.phase==Phase::Paused||g.phase==Phase::Victory||g.phase==Phase::Defeat){
            quad(0,0,1280,720,{0,0,0,.72f});panel(280,165,720,412,g.phase==Phase::Defeat?red:amber);
            text(g.phase==Phase::Paused?"VUELO EN PAUSA":g.phase==Phase::Victory?"SECTOR ASEGURADO":"MISION INTERRUMPIDA",640,203,28,g.phase==Phase::Defeat?red:whiteC,true);
            if(g.phase==Phase::Paused){
                text("CONTROL DE VUELO",320,263,10,amber);
                text("WASD / FLECHAS   DESPLAZAMIENTO",320,291,11,whiteC);
                text("SHIFT   IMPULSO CON CARGA LIMITADA",320,319,11,whiteC);
                text(g.stage==Stage::Evasion?"VISTA   CABINA DE ESQUIVA":"C   CAMARA / CABINA",320,347,11,whiteC);
                text("M   AUDIO     F2   VER MALLA",320,375,11,muted);
                text("SISTEMAS",700,263,10,amber);
                text("E   PRIORIDAD DE ENERGIA",700,291,11,whiteC);
                text(g.stage==Stage::Evasion?"ESQUIVA   ARMAS EN ESPERA":"ESPACIO   FUEGO POR RAFAGAS",700,319,11,whiteC);
                text("1-4   SIMPLE / DOBLE / TRIPLE / MISIL",700,347,10,muted);
                text("Q   MISIL AUXILIAR",700,375,11,whiteC);
                if(g.stage!=Stage::Evasion)text("SI SE BLOQUEA: ENFRIA HASTA 35%",700,403,10,muted);
                text("P / REANUDAR VUELO",640,459,18,amber,true);
            }else{
                text("PUNTUACION / "+std::to_string(g.score),640,287,21,whiteC,true);
                text(std::to_string(g.kills)+" OBJETIVOS NEUTRALIZADOS / "+std::to_string(int(g.time))+" S DE VUELO",640,334,12,muted,true);
                text("RECORD / "+std::to_string(std::max(g.bestScore,g.score)),640,371,12,muted,true);
                text("R / VOLVER A DESPLEGAR",640,459,18,amber,true);
            }
            text("ESC / VOLVER AL HANGAR",640,532,10,muted,true);
        }
    }
    finish();
}
}
