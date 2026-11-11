#include "pch.h"
#include "EntornVGIDoc.h"
#include "EntornVGIView.h"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <stdexcept>

// /verify-render exercises the real shader/VAO/VBO pipeline in an offscreen FBO.
// No desktop screenshots or synthetic OS input; MFC handlers are invoked directly.
bool CEntornVGIView::VerifyDemoRendering() {
    auto folder=galaga::Renderer2D::executableDirectory()/L"verification";
    std::filesystem::create_directories(folder);
    std::ofstream report(folder/L"render-report.txt");
    GLuint fbo=0,color=0,depth=0;
    auto cleanup=[&]{
        glBindFramebuffer(GL_FRAMEBUFFER,0);
        if(fbo)glDeleteFramebuffers(1,&fbo);if(color)glDeleteTextures(1,&color);if(depth)glDeleteRenderbuffers(1,&depth);
        wglMakeCurrent(nullptr,nullptr);
    };
    try {
        if(!gameRendererReady)throw std::runtime_error("renderer not initialized");
        wglMakeCurrent(m_pDC->GetSafeHdc(),m_hRC);
        report<<"OpenGL: "<<glGetString(GL_VERSION)<<"\nRenderer: "<<glGetString(GL_RENDERER)<<"\n";
        if(!gameRenderer.verifyGpu(report))throw std::runtime_error("invalid GPU model buffers");
        const auto uploads=gameRenderer.uploadCount();
        glGenFramebuffers(1,&fbo);glGenTextures(1,&color);glGenRenderbuffers(1,&depth);glBindFramebuffer(GL_FRAMEBUFFER,fbo);
        auto target=[&](int width,int height){
            glBindTexture(GL_TEXTURE_2D,color);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,nullptr);
            glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,color,0);
            glBindRenderbuffer(GL_RENDERBUFFER,depth);glRenderbufferStorage(GL_RENDERBUFFER,GL_DEPTH_COMPONENT24,width,height);
            glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_RENDERBUFFER,depth);
            if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)throw std::runtime_error("incomplete framebuffer");
        };
        target(64,64);
        if(!gameRenderer.verifyLighting(report))throw std::runtime_error("GL-6 lighting verification failed");
        auto capture=[&](const char* name,int width,int height,bool gallery=false,float angle=0.f,bool wireframe=false) {
            target(width,height);
            if(!gallery && game.phase==galaga::Phase::Playing && !gameRenderer.verifyFraming(game,report))
                throw std::runtime_error("gameplay framing is unreadable or clipped");
            if(gallery)gameRenderer.modelGallery(width,height,angle,wireframe);else gameRenderer.draw(game,width,height);
            glFinish();
            auto error=glGetError();if(error!=GL_NO_ERROR)throw std::runtime_error("OpenGL error "+std::to_string(error));
            std::vector<unsigned char> data(size_t(width)*height*4),flipped(data.size());
            glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,data.data());
            for(int y=0;y<height;++y)memcpy(flipped.data()+size_t(y)*width*4,data.data()+size_t(height-1-y)*width*4,size_t(width)*4);
            // Captures represent an opaque window, including blended HUD glyphs.
            for(size_t pixel=3;pixel<flipped.size();pixel+=4)flipped[pixel]=255;
            if(!gallery&&width==1280&&height==720&&game.phase==galaga::Phase::Playing){
                size_t visibleScore=0;
                for(int y=18;y<80;++y)for(int x=30;x<220;++x){const auto* p=flipped.data()+(size_t(y)*width+x)*4;if(std::max({p[0],p[1],p[2]})>150)++visibleScore;}
                if(visibleScore<300)throw std::runtime_error("HUD score missing from framebuffer");
            }
            if(!SOIL_save_image((folder/(std::string(name)+".png")).string().c_str(),SOIL_SAVE_TYPE_PNG,width,height,4,flipped.data()))throw std::runtime_error("could not write PNG");
            std::vector<float> z(size_t(width)*height);glReadPixels(0,0,width,height,GL_DEPTH_COMPONENT,GL_FLOAT,z.data());
            size_t samples=std::count_if(z.begin(),z.end(),[](float v){return v<.99999f;});
            if(gameRenderer.drawCount()>0&&samples<30)throw std::runtime_error("solid meshes did not write depth");
            unsigned long long hash=1469598103934665603ull;for(auto c:data)hash=(hash^c)*1099511628211ull;
            report<<"PASS "<<name<<" "<<width<<"x"<<height<<"; "<<samples<<" depth pixels\n";
            return hash;
        };
        auto key=[&](UINT code){GameKeyDown(code,0);OnKeyUp(code,1,0);};
        // Exercise the MFC interception path, including the new flight axes.
        for(UINT code:{UINT('W'),UINT('S'),UINT(VK_UP),UINT(VK_DOWN),UINT('Q')}){
            MSG message{};message.message=WM_KEYDOWN;message.wParam=code;
            if(!PreTranslateMessage(&message)||!gameKeys[code])throw std::runtime_error("flight input not routed to game");
            message.message=WM_KEYUP;
            if(!PreTranslateMessage(&message)||gameKeys[code])throw std::runtime_error("flight input release was lost");
        }
        key('M');if(!gameAudio.isMuted())throw std::runtime_error("audio toggle failed");key('M');
        game=galaga::Game3D{};capture("01-menu",1280,720);
        key('2');if(game.selectedShip!=1)throw std::runtime_error("ship selection failed");
        capture("02-delta-selected",1280,720);
        key('3');if(game.selectedShip!=2)throw std::runtime_error("third ship selection failed");
        key(VK_RETURN);if(game.phase!=galaga::Phase::Playing||game.selectedShip!=2)throw std::runtime_error("Enter did not preserve selected ship");
        for(int i=0;i<220;++i)game.update({});
        capture("03-combat",1280,720);capture("04-combat-4x3",1024,768);
        game.selectedShip=0;capture("03-combat-flecha",1280,720);
        game.selectedShip=1;capture("03-combat-delta",1280,720);game.selectedShip=2;
        auto placePlayer=[&](float x,float z){
            game.player.x=x;game.previousPlayer=game.player;game.playerZ=game.previousPlayerZ=z;
        };
        placePlayer(-7.68f,0);capture("04-left-limit",1280,720);
        placePlayer(7.68f,0);capture("04-right-limit",1280,720);
        placePlayer(galaga::Game3D::PlayerLimitX,galaga::Game3D::PlayerMaxZ);
        capture("04-upper-right-limit",1280,720);
        placePlayer(-galaga::Game3D::PlayerLimitX,galaga::Game3D::PlayerMinZ);
        capture("04-lower-left-limit",1280,720);placePlayer(0,0);
        bool hasNear=false,hasFar=false;
        for(const auto& e:game.enemies){hasNear|=e.pos.y<17;hasFar|=e.pos.y>23&&e.z>3;}
        if(!hasNear||!hasFar)throw std::runtime_error("missing persistent enemy depth levels");
        auto still=capture("05-depth-levels",1280,720);
        if(still!=capture("05-static-repeat",1280,720))throw std::runtime_error("static scene changed without simulation");
        auto savedGame=game;
        placePlayer(game.enemies[1].pos.x,game.enemies[1].z);
        capture("11-aligned-shot",1280,720);
        game.update({false,false,true});
        for(int step=0;step<20;++step)game.update({});
        capture("12-shot-in-flight",1280,720);
        for(int step=0;step<17;++step)game.update({});
        if(game.kills!=1)throw std::runtime_error("selected target was not hit");
        capture("13-confirmed-hit",1280,720);
        for(int weapon=0;weapon<4;++weapon){
            game=savedGame;key(UINT('1'+weapon));
            if(int(game.weapon)!=weapon)throw std::runtime_error("weapon hotkey failed");
            game.update({false,false,true});
            for(int step=0;step<12;++step)game.update({});
            capture(("15-weapon-"+std::to_string(weapon+1)).c_str(),1280,720);
        }
        game=savedGame;
        for(int step=0;step<210;++step)game.update({});
        capture("16-enemy-dive",1280,720);
        game=savedGame;
        for(auto& e:game.enemies)e.alive=false;
        game.update({});
        if(game.stage!=galaga::Stage::Evasion)throw std::runtime_error("cockpit stage did not start");
        for(int step=0;step<180;++step)game.update({});
        capture("17-cockpit-evasion",1280,720);capture("17-cockpit-4x3",1024,768);
        game=savedGame;game.wave=3;
        for(auto& e:game.enemies)e.alive=false;
        game.update({});
        for(int step=0;step<190;++step)game.update({});
        capture("18-boss",1280,720);
        game=savedGame;
        key('P');float time=game.time;for(int i=0;i<180;++i)game.update({false,true,true});
        if(game.time!=time||game.phase!=galaga::Phase::Paused)throw std::runtime_error("pause integration failed");
        capture("06-pause",1280,720);key('P');
        if(game.phase!=galaga::Phase::Playing)throw std::runtime_error("resume integration failed");
        OnKillFocus(nullptr);
        if(game.phase!=galaga::Phase::Paused)throw std::runtime_error("focus loss did not pause");
        key(VK_ESCAPE);if(game.phase!=galaga::Phase::Menu)throw std::runtime_error("return to selection failed");
        key('1');key(VK_RETURN);
        game.phase=galaga::Phase::Victory;game.score=2100;for(auto& e:game.enemies)e.alive=false;
        capture("07-victory-fixture",1280,720);
        key('R');if(game.remaining()!=12||game.score!=0||game.lives!=3)throw std::runtime_error("restart integration failed");
        game.phase=galaga::Phase::Defeat;game.lives=0;game.score=750;
        capture("08-defeat-fixture",1280,720);
        auto front=capture("09-models-front",1280,720,true,.25f);
        auto side=capture("10-models-side",1280,720,true,1.05f);
        if(front==side)throw std::runtime_error("model matrix rotation did not alter rendering");
        capture("14-models-wireframe",1280,720,true,.25f,true);
        report<<"PASS model matrix: rotated solid meshes produce different frames\n";
        game.reset();for(int i=0;i<220;++i)game.update({});
        for(int benchmarkWidth:{1280,960}){
            const int benchmarkHeight=benchmarkWidth*9/16;
            target(benchmarkWidth,benchmarkHeight);
            for(int warmup=0;warmup<3;++warmup){gameRenderer.draw(game,benchmarkWidth,benchmarkHeight);glFinish();}
            auto start=std::chrono::steady_clock::now();
            for(int i=0;i<60;++i){gameRenderer.draw(game,benchmarkWidth,benchmarkHeight);glFinish();}
            auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/60;
            report<<"Average render (60 frames, "<<benchmarkWidth<<"x"<<benchmarkHeight<<"): "<<ms<<" ms\n";
        }
        if(gameRenderer.uploadCount()!=uploads||!gameRenderer.verifyGpu(report))throw std::runtime_error("mesh buffers changed across frames");
        if(glGetError()!=GL_NO_ERROR)throw std::runtime_error("OpenGL error after verification");
        report<<"PASS MFC handlers: XYZ flight keys / 4 weapons / audio / 3 ships / start / pause / resume / focus loss / menu / restart\n";
        report<<"PASS static meshes reused through all captures and 60 frames; XYZ depth buffer active\n";
        cleanup();return true;
    }catch(const std::exception& e){report<<"FAIL "<<e.what()<<"\n";}
    cleanup();return false;
}
