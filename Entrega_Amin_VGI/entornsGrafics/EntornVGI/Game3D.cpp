#include "Game3D.h"
#include <algorithm>
#include <cmath>

namespace galaga {
float Bullet::forwardSpeed() const {
    return velocityY != 0 ? velocityY : (ally ? Game3D::PlayerShotSpeed : -Game3D::EnemyShotSpeed);
}

const Enemy* Game3D::aimTarget() const {
    const Enemy* target = nullptr;
    for (const auto& enemy : enemies) {
        if (!enemy.alive || enemy.pos.y <= player.y + .85f)
            continue;
        if (std::abs(enemy.pos.x - player.x) > AimTolerance)
            continue;
        if (!target || enemy.pos.y < target->pos.y)
            target = &enemy;
    }
    return target;
}

void Game3D::reset() {
    const int ship = selectedShip, record = std::max(bestScore, score);
    *this = Game3D{};
    selectedShip = std::clamp(ship, 0, 2); bestScore = record;
    phase = Phase::Playing;
    for (int i=0; i<18; ++i) {
        Enemy e; e.id=i; e.type=i<12?0:1;
        e.slot={(i%6-2.5f)*2.6f,14.0f+(i/6)*4.0f};
        e.phase=EnemyPhase::Formation;
        e.pos=e.previous=e.slot;
        // Three persistent world depths, not camera layers or selectable planes.
        e.z=e.previousZ=float(i/6-1)*2.5f;
        enemies.push_back(e);
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
    --lives; clearCombo();
    respawn=.75f; invulnerable=1.5f;
}
void Game3D::update(const Input& input,float dt) {
    if(phase!=Phase::Playing || dt<=0) return;
    time+=dt;
    sparks.clear();
    previousPlayer=player;
    if(respawn>0) {
        respawn=std::max(0.0f,respawn-dt);
        if(respawn==0) player=previousPlayer={0,-4};
    } else {
        invulnerable=std::max(0.0f,invulnerable-dt);
        player.x=std::clamp(player.x+6.0f*dt*(int(input.right)-int(input.left)),-7.68f,7.68f);
        fireClock=std::max(0.0f,fireClock-dt);
        const auto active=std::count_if(bullets.begin(),bullets.end(),[](const Bullet& b){return b.alive&&b.ally;});
        if(input.fire && fireClock==0 && active<8) {
            Vec2 p{player.x,player.y+.85f};
            Bullet shot{nextId++,true,true,p,p};
            if (const Enemy* target = aimTarget()) {
                const float dx = target->pos.x - p.x;
                const float dy = target->pos.y - p.y;
                const float dz = target->z;
                const float flight = std::sqrt(dx*dx + dy*dy + dz*dz) / PlayerShotSpeed;
                shot.velocityX = dx / flight;
                shot.velocityY = dy / flight;
                shot.velocityZ = dz / flight;
            }
            bullets.push_back(shot);
            fireClock=.22f; ++shots;
        }
    }
    // Basic AI: stationary formation; one enemy fires at a time.
    for(auto& e:enemies) {e.previous=e.pos;e.previousZ=e.z;}
    attackClock-=dt;
    if(attackClock<=0 && !enemies.empty()) {
        for(size_t n=0;n<enemies.size();++n) {
            const size_t index=(nextAttacker+n)%enemies.size();
            const auto& e=enemies[index];if(!e.alive)continue;
            const float dx = player.x - e.pos.x;
            const float dy = player.y - e.pos.y;
            const float flight = std::sqrt(dx*dx + dy*dy + e.z*e.z) / EnemyShotSpeed;
            Bullet shot{nextId++,false,true,e.pos,e.pos,flight+1.f,e.z,e.z,-e.z/flight};
            // Aim once on emission; no tracking after the shot has left.
            shot.velocityX=(player.x-e.pos.x)/flight;
            shot.velocityY=dy/flight;
            bullets.push_back(shot);nextAttacker=int((index+1)%enemies.size());break;
        }
        attackClock=1.2f;
    }
    for(auto& b:bullets) {
        if (!b.alive || b.ttl <= 0) {
            b.alive = false;
            continue;
        }
        b.previous=b.pos;
        b.previousZ=b.z;
        const float activeTime=std::min(dt,std::max(0.0f,b.ttl));
        b.pos.y+=b.forwardSpeed()*activeTime;
        b.pos.x+=b.velocityX*activeTime;
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
                float t=hitTime3D(b.previous,b.pos,b.previousZ,b.z,e.previous,e.pos,e.previousZ,e.z,EnemyHitRadius);
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

        }
    }
    if(respawn==0) for(auto& e:enemies) {
        if(e.alive && e.timer>=0 && hitTime3D(e.previous,e.pos,e.previousZ,e.z,previousPlayer,player,0,0,.68f)>=0) {
            e.alive=false;damage();
        }
    }
    for(const auto& b:bullets) {
        if(b.ally && b.alive && (b.ttl<=0||b.pos.y>28||b.pos.y<-7)) clearCombo();
    }
    bullets.erase(std::remove_if(bullets.begin(),bullets.end(),[](const Bullet& b){
        // Retire missed enemy shots immediately after they pass the player.
        return !b.alive||b.ttl<=0||b.pos.y>28||b.pos.y<-4.8f;
    }),bullets.end());
    if(lives==0) phase=Phase::Defeat;
    else if(remaining()==0) phase=Phase::Victory;
    if(phase!=Phase::Playing) bullets.clear();
}
}
