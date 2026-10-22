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
        auto capture=[&](const char* name,int width,int height,bool gallery=false,float angle=0.f) {
            target(width,height);
            if(gallery)gameRenderer.modelGallery(width,height,angle);else gameRenderer.draw(game,width,height);
            glFinish();
            auto error=glGetError();if(error!=GL_NO_ERROR)throw std::runtime_error("OpenGL error "+std::to_string(error));
            std::vector<unsigned char> data(size_t(width)*height*4),flipped(data.size());
            glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,data.data());
            for(int y=0;y<height;++y)memcpy(flipped.data()+size_t(y)*width*4,data.data()+size_t(height-1-y)*width*4,size_t(width)*4);
            if(!gallery&&width==1280&&height==720&&game.phase==galaga::Phase::Playing){
                size_t visibleFooter=0;
                for(int y=640;y<710;++y)for(int x=25;x<1230;++x){const auto* p=flipped.data()+(size_t(y)*width+x)*4;if(std::max({p[0],p[1],p[2]})>150)++visibleFooter;}
                if(visibleFooter<1500)throw std::runtime_error("HUD controls or lives missing from framebuffer");
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
        game=galaga::Game3D{};capture("01-menu",1280,720);
        key('2');if(game.selectedShip!=1)throw std::runtime_error("ship selection failed");
        capture("02-delta-selected",1280,720);
        key('3');if(game.selectedShip!=2)throw std::runtime_error("third ship selection failed");
        key(VK_RETURN);if(game.phase!=galaga::Phase::Playing||game.selectedShip!=2)throw std::runtime_error("Enter did not preserve selected ship");
        for(int i=0;i<390;++i)game.update({});
        capture("03-combat",1280,720);capture("04-combat-4x3",1024,768);
        // A natural dive in XYZ, with no camera- or depth-mode input.
        bool flight=false;
        for(int i=0;i<500&&!flight;++i){game.update({});for(const auto& e:game.enemies)flight|=e.alive&&e.phase==galaga::EnemyPhase::Diving&&e.z>.8f;}
        if(!flight)throw std::runtime_error("no real depth trajectory observed");
        capture("05-depth-flight",1280,720);
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
        key('R');if(game.remaining()!=18||game.score!=0||game.lives!=3)throw std::runtime_error("restart integration failed");
        game.phase=galaga::Phase::Defeat;game.lives=0;game.score=750;
        capture("08-defeat-fixture",1280,720);
        auto front=capture("09-models-front",1280,720,true,.25f);
        auto side=capture("10-models-side",1280,720,true,1.05f);
        if(front==side)throw std::runtime_error("model matrix rotation did not alter rendering");
        report<<"PASS model matrix: rotated solid meshes produce different frames\n";
        game.reset();for(int i=0;i<390;++i)game.update({});
        target(1280,720);
        auto start=std::chrono::steady_clock::now();
        for(int i=0;i<60;++i){gameRenderer.draw(game,1280,720);glFinish();}
        auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/60;
        report<<"Average render (60 frames, 1280x720): "<<ms<<" ms\n";
        if(gameRenderer.uploadCount()!=uploads||!gameRenderer.verifyGpu(report))throw std::runtime_error("mesh buffers changed across frames");
        if(glGetError()!=GL_NO_ERROR)throw std::runtime_error("OpenGL error after verification");
        report<<"PASS MFC handlers: 3 ships / start / pause / resume / focus loss / menu / restart\n";
        report<<"PASS static meshes reused through all captures and 60 frames; XYZ depth buffer active\n";
        cleanup();return true;
    }catch(const std::exception& e){report<<"FAIL "<<e.what()<<"\n";}
    cleanup();return false;
}
