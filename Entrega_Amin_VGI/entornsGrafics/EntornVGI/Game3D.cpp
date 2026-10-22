#include "Game3D.h"
#include <algorithm>
#include <cmath>

namespace galaga {
namespace {
Vec2 mix(Vec2 a, Vec2 b, float t) { return {a.x+(b.x-a.x)*t, a.y+(b.y-a.y)*t}; }
Vec2 bezier(Vec2 a, Vec2 b, Vec2 c, Vec2 d, float t) {
    return mix(mix(mix(a,b,t),mix(b,c,t),t),mix(mix(b,c,t),mix(c,d,t),t),t);
}
}
void Game3D::reset() {
    const int ship = selectedShip, record = std::max(bestScore, score);
    *this = Game3D{};
    selectedShip = std::clamp(ship, 0, 2); bestScore = record;
    phase = Phase::Playing;
    for (int i=0; i<18; ++i) {
        Enemy e; e.id=i; e.type=i<12?0:1;
        e.slot={(i%6-2.5f)*1.6f,6.0f-(i/6)*1.25f};
        e.start={i%2?-9.0f:9.0f,8.5f}; e.pos=e.previous=e.start;
        e.z=e.previousZ=-3.0f;
        e.timer=-i*.25f; enemies.push_back(e);
    }
}
void Game3D::returnToMenu() {
    const int ship = selectedShip, record = std::max(bestScore, score);
    *this = Game3D{};
    selectedShip = std::clamp(ship, 0, 2); bestScore = record;
}
void Game3D::selectShip(int ship) {
    if (phase==Phase::Menu && ship>=0 && ship<3) selectedShip=ship;
}
void Game3D::pause() {
    if (phase==Phase::Playing) phase=Phase::Paused;
    else if (phase==Phase::Paused) phase=Phase::Playing;
}
int Game3D::remaining() const {
    return static_cast<int>(std::count_if(enemies.begin(),enemies.end(),[](const Enemy& e){return e.alive;}));
}
float Game3D::hitTime(Vec2 a0, Vec2 a1, Vec2 b0, Vec2 b1, float r) {
    return hitTime3D(a0,a1,0,0,b0,b1,0,0,r);
}
float Game3D::hitTime3D(Vec2 a0, Vec2 a1, float za0, float za1,
    Vec2 b0, Vec2 b1, float zb0, float zb1, float r) {
    const float x=a0.x-b0.x,y=a0.y-b0.y,z=za0-zb0;
    const float vx=a1.x-a0.x-b1.x+b0.x,vy=a1.y-a0.y-b1.y+b0.y,vz=za1-za0-zb1+zb0;
    const float c=x*x+y*y+z*z-r*r, a=vx*vx+vy*vy+vz*vz;
    if(c<=0) return 0;
    if(a<1e-10f) return -1;
    const float b=2*(x*vx+y*vy+z*vz),d=b*b-4*a*c;
    if(d<0) return -1;
    const float t=(-b-std::sqrt(d))/(2*a);
    return t>=0 && t<=1?t:-1;
}
void Game3D::clearCombo() { hitStreak=0; multiplier=1; }
void Game3D::damage() {
    if(invulnerable>0 || respawn>0 || lives<=0) return;
    --lives; sparks.push_back({player,0,true,0}); clearCombo();
    respawn=.75f; invulnerable=1.5f;
}
void Game3D::update(const Input& input,float dt) {
    if(phase!=Phase::Playing || dt<=0) return;
    time+=dt;
    for(auto& s:sparks) s.age+=dt;
    sparks.erase(std::remove_if(sparks.begin(),sparks.end(),[](const Spark& s){return s.age>.45f;}),sparks.end());
    previousPlayer=player;
    if(respawn>0) {
        respawn=std::max(0.0f,respawn-dt);
        if(respawn==0) player=previousPlayer={0,-4};
    } else {
        invulnerable=std::max(0.0f,invulnerable-dt);
        player.x=std::clamp(player.x+6.0f*dt*(int(input.right)-int(input.left)),-7.68f,7.68f);
        fireClock=std::max(0.0f,fireClock-dt);
        const auto active=std::count_if(bullets.begin(),bullets.end(),[](const Bullet& b){return b.alive&&b.ally;});
        if(input.fire && fireClock==0 && active<4) {
            Vec2 p{player.x,player.y+.5f}; bullets.push_back({nextId++,true,true,p,p});
            fireClock=.22f; ++shots;
        }
    }
    bool entering=false,busy=false;
    for(auto& e:enemies) {
        if(!e.alive) continue;
        e.previous=e.pos; e.previousZ=e.z; e.timer+=dt;
        Vec2 slot{e.slot.x+.45f*std::sin(time*1.5707963f),e.slot.y};
        switch(e.phase) {
        case EnemyPhase::Entering:
            entering=true;
            if(e.timer>=0) {
                float u=std::min(e.timer/1.2f,1.0f);
                e.pos=bezier(e.start,{e.start.x,3},{slot.x,8},slot,u);
                e.z=-3.0f*(1.0f-u*u*(3.0f-2.0f*u));
                if(u>=1) {e.phase=EnemyPhase::Formation;e.timer=0;}
            } break;
        case EnemyPhase::Formation: e.pos=slot;e.z=0;break;
        case EnemyPhase::Warning:
            busy=true; e.pos=slot;e.z=0;
            if(e.timer>=.65f) {e.start=e.pos;e.targetX=player.x;e.timer=0;e.shot=false;e.phase=EnemyPhase::Diving;}
            break;
        case EnemyPhase::Diving: {
            busy=true;
            float u=std::min(e.timer/2.5f,1.0f);
            float side=e.start.x>=0?1.0f:-1.0f;
            e.pos=bezier(e.start,{e.start.x+side*(e.type?3.0f:1.8f),e.start.y-1},{e.targetX,-2},{e.targetX,-6},u);
            // A genuine 3D arc, returning to z=0 before crossing the player.
            // This preserves lateral-only controls and a reachable dodge path.
            const float progress=std::clamp((e.start.y-e.pos.y)/std::max(.01f,e.start.y+4.0f),0.0f,1.0f);
            const float arc=std::sin(3.14159265f*progress);
            e.z=progress>=1?0.0f:2.0f*arc*arc;
            if(u>=.4f && !e.shot) {
                const float flight=std::max(.2f,(e.pos.y+4.0f)/4.0f);
                bullets.push_back({nextId++,false,true,e.pos,e.pos,3.5f,e.z,e.z,-e.z/flight});
                e.shot=true;
            }
            if(u>=1) {e.phase=EnemyPhase::Returning;e.timer=0;e.start=e.pos;}
            break; }
        case EnemyPhase::Returning: {
            busy=true; float u=std::min(e.timer/2.0f,1.0f);
            float side=e.slot.x>=0?9.2f:-9.2f;
            e.pos=bezier(e.start,{side,-6},{side,9},slot,u);
            const float arc=std::sin(3.14159265f*u);
            e.z=-3.0f*arc*arc;
            if(u>=1) {e.phase=EnemyPhase::Formation;e.timer=0;e.z=0;}
            break; }
        }
    }
    if(!entering) {
        attackClock-=dt;
        if(!busy && attackClock<=0 && !enemies.empty()) {
            for(size_t n=0;n<enemies.size();++n) {
                auto& e=enemies[(nextAttacker+n)%enemies.size()];
                if(e.alive && e.phase==EnemyPhase::Formation) {
                    nextAttacker=(e.id+1)%int(enemies.size());e.phase=EnemyPhase::Warning;e.timer=0;attackClock=2.4f;break;
                }
            }
        }
    }
    for(auto& b:bullets) {
        b.previous=b.pos;
        b.previousZ=b.z;
        const float activeTime=std::min(dt,std::max(0.0f,b.ttl));
        b.pos.y+=(b.ally?18.0f:-4.0f)*activeTime;
        b.z+=b.velocityZ*activeTime;b.ttl-=dt;
    }
    // Resolve swept contacts chronologically, then by stable IDs. Never erase while iterating.
    struct Contact {float t;int bullet,enemy,id;};
    std::vector<Contact> contacts;
    for(int i=0;i<int(bullets.size());++i) {
        const auto& b=bullets[i];
        if(b.ally) {
            for(int j=0;j<int(enemies.size());++j) {
                const auto& e=enemies[j]; if(!e.alive||e.timer<0)continue;
                float t=hitTime3D(b.previous,b.pos,b.previousZ,b.z,e.previous,e.pos,e.previousZ,e.z,.46f);
                if(t>=0)contacts.push_back({t,i,j,e.id});
            }
        } else if(respawn==0) {
            float t=hitTime3D(b.previous,b.pos,b.previousZ,b.z,previousPlayer,player,0,0,.42f);
            if(t>=0)contacts.push_back({t,i,-1,b.id});
        }
    }
    std::sort(contacts.begin(),contacts.end(),[](const Contact& a,const Contact& b){
        if(a.t!=b.t)return a.t<b.t;if(a.id!=b.id)return a.id<b.id;return a.bullet<b.bullet;
    });
    for(const auto& c:contacts) {
        auto& b=bullets[c.bullet];if(!b.alive)continue;
        if(c.enemy<0) {b.alive=false;damage();}
        else {
            auto& e=enemies[c.enemy]; if(!e.alive)continue;
            b.alive=false;e.alive=false;++kills;
            ++hitStreak;multiplier=std::min(3,1+hitStreak/3);
            int points=e.type?150:100;
            score+=(e.phase==EnemyPhase::Diving?points*3/2:points)*multiplier;
            bestScore=std::max(bestScore,score);
            sparks.push_back({e.pos,0,false,e.z});
        }
    }
    if(respawn==0) for(auto& e:enemies) {
        if(e.alive && e.timer>=0 && hitTime3D(e.previous,e.pos,e.previousZ,e.z,previousPlayer,player,0,0,.68f)>=0) {
            e.alive=false;sparks.push_back({e.pos,0,false,e.z});damage();
        }
    }
    for(const auto& b:bullets) {
        if(b.ally && b.alive && (b.ttl<=0||b.pos.y>9||b.pos.y<-7)) clearCombo();
    }
    bullets.erase(std::remove_if(bullets.begin(),bullets.end(),[](const Bullet& b){
        return !b.alive||b.ttl<=0||b.pos.y>9||b.pos.y<-7;
    }),bullets.end());
    if(lives==0) phase=Phase::Defeat;
    else if(remaining()==0) phase=Phase::Victory;
    if(phase!=Phase::Playing) bullets.clear();
}
}
