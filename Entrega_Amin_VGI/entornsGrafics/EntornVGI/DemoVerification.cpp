#include "pch.h"
#include "EntornVGIDoc.h"
#include "EntornVGIView.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <stdexcept>

namespace {
// Read the opening from the visible wall; do not predict the spawn sequence.
galaga::Vec2 openingAt(const galaga::Game3D& game, float wallY) {
    std::vector<float> xs, zs;
    for (const auto& obstacle : game.obstacles) {
        if (!obstacle.alive || std::abs(obstacle.pos.y - wallY) > .1f) continue;
        if (std::none_of(xs.begin(), xs.end(), [&](float x) { return std::abs(x - obstacle.pos.x) < .01f; }))
            xs.push_back(obstacle.pos.x);
        if (std::none_of(zs.begin(), zs.end(), [&](float z) { return std::abs(z - obstacle.z) < .01f; }))
            zs.push_back(obstacle.z);
    }
    galaga::Vec2 target{game.player.x, game.playerZ};
    float bestDistance = 1e9f;
    for (float z : zs) for (float x : xs) {
        bool free = true;
        for (const auto& obstacle : game.obstacles) {
            if (!obstacle.alive || std::abs(obstacle.pos.y - wallY) > .1f) continue;
            const float dx = x - obstacle.pos.x, dz = z - obstacle.z;
            const float radius = obstacle.radius + galaga::Game3D::PlayerRadius + .15f;
            if (dx * dx + dz * dz < radius * radius) free = false;
        }
        const float dx = x - game.player.x, dz = z - game.playerZ;
        const float distance = dx * dx + dz * dz;
        if (free && distance < bestDistance) {
            bestDistance = distance;
            target = {x, z};
        }
    }
    return target;
}

// Same ordinary-input pilot used by Game3DTests: no state or collider changes.
galaga::Input campaignInput(const galaga::Game3D& game) {
    float targetX = game.player.x, targetZ = game.playerZ;
    if (game.stage == galaga::Stage::Evasion) {
        float nearestY = 1e9f;
        for (const auto& obstacle : game.obstacles)
            if (obstacle.alive && obstacle.pos.y > game.player.y - obstacle.radius - galaga::Game3D::PlayerRadius)
                nearestY = std::min(nearestY, obstacle.pos.y);
        const auto opening = openingAt(game, nearestY);
        targetX = opening.x;
        targetZ = opening.y;
    } else {
        float closest = 1e9f;
        for (const auto& enemy : game.enemies) {
            if (!enemy.alive || enemy.timer < 0 || enemy.phase == galaga::EnemyPhase::Entering ||
                enemy.phase == galaga::EnemyPhase::Returning) continue;
            const float flight = std::max(0.f, (enemy.pos.y - game.player.y) / galaga::Game3D::PlayerShotSpeed);
            const float x = enemy.pos.x + enemy.velocityX * flight;
            const float z = enemy.z + enemy.velocityZ * flight;
            const float dx = x - game.player.x, dz = z - game.playerZ;
            float distance = dx * dx + dz * dz;
            if (enemy.phase == galaga::EnemyPhase::Diving) distance += 30;
            if (distance < closest) {
                closest = distance;
                targetX = std::clamp(x, -galaga::Game3D::PlayerLimitX, galaga::Game3D::PlayerLimitX);
                targetZ = std::clamp(z, galaga::Game3D::PlayerMinZ, galaga::Game3D::PlayerMaxZ);
            }
        }
        for (const auto& bullet : game.bullets) {
            if (bullet.ally || !bullet.alive || bullet.forwardSpeed() >= 0) continue;
            const float flight = (game.player.y - bullet.pos.y) / bullet.forwardSpeed();
            if (flight < 0 || flight > .75f) continue;
            const float x = bullet.pos.x + bullet.velocityX * flight;
            const float z = bullet.z + bullet.velocityZ * flight;
            const float dx = game.player.x - x, dz = game.playerZ - z;
            if (dx * dx + dz * dz < 1.1f) {
                targetZ = game.playerZ < .7f ? game.playerZ + 1.8f : game.playerZ - 1.8f;
                targetX = game.player.x < 0 ? game.player.x + 1.5f : game.player.x - 1.5f;
            }
        }
    }
    return {game.player.x > targetX + .07f, game.player.x < targetX - .07f,
        game.stage != galaga::Stage::Evasion, game.playerZ < targetZ - .07f,
        game.playerZ > targetZ + .07f, game.stage == galaga::Stage::Boss};
}
}

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
        const char* captureOrigin="fixture: prepared render and control checks";
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
            report<<"PASS "<<name<<" "<<width<<"x"<<height<<"; "<<samples<<" depth pixels; origin="<<captureOrigin<<"\n";
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
        capture("02-doble-motor-selected",1280,720);
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
        auto warningPresent=[&]{return std::any_of(game.enemies.begin(),game.enemies.end(),[](const galaga::Enemy& enemy){return enemy.alive&&enemy.phase==galaga::EnemyPhase::Warning;});};
        for(int step=0;step<240&&!warningPresent();++step)game.update({});
        if(!warningPresent())throw std::runtime_error("enemy warning was never reached");
        capture("19-warning-start",1280,720);
        for(int step=0;step<12;++step)game.update({});
        capture("20-warning-pulse",1280,720);
        game=savedGame;game.invulnerable=0;
        galaga::Bullet incoming;incoming.id=9000;incoming.ally=false;
        incoming.pos=incoming.previous=game.player;incoming.z=incoming.previousZ=game.playerZ;
        game.bullets.push_back(incoming);game.update({});
        if(game.lives!=2||game.damageFlash<=0)throw std::runtime_error("damage feedback was not activated");
        capture("21-damage-combat",1280,720);
        for(int step=0;step<45;++step)game.update({});
        if(game.respawn>0||game.invulnerable<=0||game.damageFlash>0)throw std::runtime_error("respawn protection feedback did not replace damage");
        capture("22-protected-flight",1280,720);capture("22-protected-flight-4x3",1024,768);
        game=savedGame;
        for(auto& e:game.enemies)e.alive=false;
        game.update({});
        if(game.stage!=galaga::Stage::Evasion)throw std::runtime_error("cockpit stage did not start");
        for(int step=0;step<180;++step)game.update({});
        capture("17-cockpit-evasion",1280,720);capture("17-cockpit-4x3",1024,768);
        const auto evasionGame=game;
        galaga::Obstacle collisionRock;collisionRock.id=9001;
        collisionRock.pos=collisionRock.previous=game.player;collisionRock.z=collisionRock.previousZ=game.playerZ;
        game.obstacles.push_back(collisionRock);game.update({});
        if(game.lives!=2||game.damageFlash<=0)throw std::runtime_error("cockpit damage feedback missing");
        capture("23-damage-cockpit",1280,720);
        for(int step=0;step<45;++step)game.update({});
        capture("24-protected-cockpit",1024,768);
        game=evasionGame;key('P');capture("25-cockpit-pause",1280,720);key('P');
        placePlayer(galaga::Game3D::PlayerLimitX,galaga::Game3D::PlayerMaxZ);
        capture("27-cockpit-upper-right",1280,720);
        placePlayer(-galaga::Game3D::PlayerLimitX,galaga::Game3D::PlayerMinZ);
        capture("27-cockpit-lower-left",1280,720);
        game=evasionGame;
        // At the center of the first observed opening; synchronize fixture history.
        placePlayer(-3.95f,-3.175f);
        for(int step=0;step<90;++step)game.update({});
        capture("28-cockpit-opening-close",1280,720);
        game=savedGame;game.update({false,false,false,false,false,true});
        for(int step=0;step<90;++step)game.update({});
        capture("26-special-recharge",1280,720);
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

        // A separate campaign starts at the menu and advances only through inputs.
        // Rendering happens once per stage after two seconds, not at every tick.
        captureOrigin="natural campaign: ordinary inputs, no injected gameplay state";
        game.returnToMenu();
        key('1');key(VK_RETURN);key('3');
        int lastWave=game.wave;
        auto lastStage=game.stage;
        bool capturedStage=false;
        int naturalCaptures=0;
        capture("30-natural-campaign-start",1280,720);
        for(int tick=0;tick<60*300&&game.phase==galaga::Phase::Playing;++tick){
            if(game.stage==galaga::Stage::Boss)game.selectWeapon(1);
            game.update(campaignInput(game));
            if(game.wave!=lastWave||game.stage!=lastStage){
                report<<"PASS natural stage transition: wave="<<game.wave
                      <<" stage="<<int(game.stage)<<" time="<<game.time<<" lives="<<game.lives<<"\n";
                lastWave=game.wave;lastStage=game.stage;capturedStage=false;
            }
            if(game.phase==galaga::Phase::Playing&&!capturedStage&&game.stageTime>=2.f){
                const char* stage=game.stage==galaga::Stage::Evasion?"evasion":
                    game.stage==galaga::Stage::Boss?"boss":"combat";
                const std::string name="31-natural-wave-"+std::to_string(game.wave)+"-"+stage;
                capture(name.c_str(),1280,720);
                capturedStage=true;
                ++naturalCaptures;
            }
        }
        if(game.phase!=galaga::Phase::Victory||game.bossHealth!=0||game.wave!=3||naturalCaptures!=6)
            throw std::runtime_error("ordinary-input campaign did not complete all six stages");
        capture("32-natural-victory",1280,720);
        report<<"PASS natural campaign: "<<game.kills<<" kills, "<<game.lives<<" lives, "
              <<game.score<<" points, "<<game.time<<" simulated seconds; six stages and victory captured\n";

        // Also record the loss condition without preparing a defeat state.
        key('R');
        for(int tick=0;tick<60*90&&game.phase==galaga::Phase::Playing;++tick)game.update({});
        if(game.phase!=galaga::Phase::Defeat||game.lives!=0)
            throw std::runtime_error("idle campaign did not reach a natural defeat");
        captureOrigin="natural idle run: no inputs and no injected gameplay state";
        capture("33-natural-defeat",1280,720);

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
        game.returnToMenu();ClearGameInput();
        cleanup();return true;
    }catch(const std::exception& e){report<<"FAIL "<<e.what()<<"\n";}
    cleanup();return false;
}
