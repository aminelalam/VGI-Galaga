#include "../EntornVGI/Game3D.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace galaga;
static int checks=0;
void check(bool result,const char* name){if(!result)throw std::runtime_error(name);++checks;std::cout<<"PASS "<<name<<'\n';}
Game3D fixture(){Game3D g;g.reset();g.enemies.clear();Enemy e;e.slot=e.pos=e.previous={30,6};e.phase=EnemyPhase::Formation;g.enemies.push_back(e);return g;}
void ticks(Game3D& g,int n,Input input={}){for(int i=0;i<n;++i)g.update(input);}
void killTarget(Game3D& g,int id) {
    Enemy e;e.id=id;e.slot=e.pos=e.previous={0,0};e.phase=EnemyPhase::Formation;
    g.enemies.push_back(e);
    g.bullets.push_back({id+1000,true,true,{0,-.1f},{0,-.1f}});
    g.update({});
}
Input simplePilot(const Game3D& g) {
    // Only regular inputs: aim at a formation ship and hold fire. The small
    // lead follows its observed lateral motion during the bullet flight.
    const Enemy* target=nullptr;float bestDistance=1000;
    for(const auto& e:g.enemies) {
        if(!e.alive||e.phase!=EnemyPhase::Formation)continue;
        const float distance=std::abs(e.pos.x-g.player.x);
        if(distance<bestDistance){target=&e;bestDistance=distance;}
    }
    if(!target)return {};
    const float flight=(target->pos.y-g.player.y-.5f)/18.0f;
    const float aim=target->pos.x+(target->pos.x-target->previous.x)/Game3D::Step*flight;
    return {g.player.x>aim+.05f,g.player.x<aim-.05f,true};
}
int main(){try {
    Game3D g;g.reset();check(g.remaining()==18&&g.lives==3&&g.score==0,"fresh round");
    for(const auto& e:g.enemies)if(e.z!=-3||e.previousZ!=-3)throw std::runtime_error("entry depth");
    check(true,"enemies enter from real depth behind formation");
    g=Game3D{};g.selectShip(2);g.selectShip(3);g.selectShip(-1);g.bestScore=500;g.reset();
    check(g.selectedShip==2&&g.bestScore==500,"valid ship selection and record survive start");
    g.selectShip(0);check(g.selectedShip==2,"cannot change model during combat");
    g.score=900;g.hitStreak=6;g.multiplier=3;g.reset();
    check(g.selectedShip==2&&g.bestScore==900&&g.score==0&&g.multiplier==1&&g.hitStreak==0,"restart preserves model and record, clears combat");
    g.returnToMenu();g.selectShip(1);
    check(g.phase==Phase::Menu&&g.selectedShip==1&&g.bestScore==900&&g.enemies.empty(),"return to menu clears world and allows another model");
    g=fixture();ticks(g,60,{false,true,false});check(std::abs(g.player.x-6)<.001f,"movement 6 units per second");
    ticks(g,120,{false,true,false});check(std::abs(g.player.x-7.68f)<.001f,"right bound");
    ticks(g,240,{true,false,false});check(std::abs(g.player.x+7.68f)<.001f,"left bound");
    check(g.player.y==-4&&g.previousPlayer.y==-4,"player movement is exclusively left and right");
    g=fixture();ticks(g,60,{true,true,false});check(g.player.x==0,"opposite keys cancel");
    g=fixture();ticks(g,120,{false,false,true});check(g.shots==9,"held fire cadence: 9 shots in 2 seconds");
    check(g.bullets.size()<=4,"four allied bullets maximum");
    float time=g.time,x=g.player.x;g.pause();ticks(g,180,{false,true,true});check(g.time==time&&g.player.x==x,"pause freezes simulation");
    g.pause();g.update({false,true,false});check(g.time>time&&g.player.x>x,"resume advances one step");
    check(Game3D::hitTime({0,-2},{0,2},{0,0},{0,0},.46f)>=0,"swept bullet crossing");
    check(Game3D::hitTime({2,-2},{2,2},{0,0},{0,0},.46f)<0,"swept near miss");
    check(Game3D::hitTime({.5f,0},{.5f,0},{0,0},{0,0},.5f)==0,"contact at boundary");
    check(Game3D::hitTime3D({0,-2},{0,2},2,2,{0,0},{0,0},0,0,.46f)<0,"overlapping projection is not a 3D hit at different depth");
    check(Game3D::hitTime3D({0,0},{0,0},-2,2,{0,0},{0,0},0,0,.46f)>=0,"swept collision catches crossing entirely in depth");
    check(Game3D::hitTime3D({0,0},{0,0},-2,2,{0,0},{0,0},2,-2,.46f)>=0,"swept collision uses relative motion in depth");
    g=fixture();g.enemies[0].slot=g.enemies[0].pos=g.enemies[0].previous={0,0};
    g.bullets={{100,true,true,{0,-.1f},{0,-.1f}},{101,true,true,{0,-.1f},{0,-.1f}}};g.update({});
    check(g.score==100&&g.kills==1&&g.hitStreak==1&&g.phase==Phase::Victory,"single death, combo credit and score for two bullets, victory");
    g=fixture();g.invulnerable=0;g.bullets={{100,false,true,g.player,g.player},{101,false,true,g.player,g.player}};g.update({});
    check(g.lives==2&&g.respawn>0,"simultaneous hostile hits cost one life");
    ticks(g,46);check(g.respawn==0&&g.invulnerable>1.4f&&g.player.x==0,"respawn and protection");
    g.bullets={{102,false,true,g.player,g.player}};g.update({});check(g.lives==2&&g.bullets.empty(),"protected contact consumes bullet");
    g=fixture();g.lives=1;g.invulnerable=0;g.enemies[0].slot=g.enemies[0].pos=g.enemies[0].previous={0,0};
    g.bullets={{100,true,true,{0,-.1f},{0,-.1f}},{101,false,true,g.player,g.player}};g.update({});
    check(g.phase==Phase::Defeat&&g.score==100,"defeat priority on simultaneous last kill");
    g=fixture();g.enemies[0].slot=g.enemies[0].pos=g.enemies[0].previous={0,0};
    g.bullets={{100,true,true,{0,-.1f},{0,-.1f},3.5f,2,2,0}};g.update({});
    check(g.enemies[0].alive&&g.bullets.size()==1&&g.score==0,"allied bullet at different depth passes without consumption");
    g.bullets={{101,true,true,{0,-.1f},{0,-.1f}}};g.update({});
    check(g.phase==Phase::Victory&&g.score==100&&g.sparks[0].z==0,"matching 3D contact wins and keeps explosion position");
    g=fixture();g.invulnerable=0;g.bullets={{100,false,true,g.player,g.player,3.5f,2,2,0}};g.update({});
    check(g.lives==3&&g.bullets.size()==1,"hostile bullet beyond player depth causes no damage");
    g.bullets[0].z=.1f;g.update({});check(g.lives==2&&g.bullets.empty(),"hostile bullet within player sphere causes damage");
    g=fixture();g.invulnerable=0;g.enemies[0].phase=EnemyPhase::Entering;g.enemies[0].z=g.enemies[0].previousZ=-3;
    g.enemies[0].start=g.enemies[0].slot=g.enemies[0].pos=g.enemies[0].previous=g.player;g.update({});
    check(g.lives==3&&g.enemies[0].alive,"overlapping enemy at distant z does not hit player");
    g.enemies[0].phase=EnemyPhase::Formation;g.enemies[0].z=g.enemies[0].previousZ=0;g.update({});
    check(g.lives==2&&!g.enemies[0].alive&&g.score==0,"same depth ship contact costs one life without score");
    g=fixture();g.update({false,false,true});ticks(g,15,{false,true,false});
    check(g.player.y==-4&&g.bullets.size()==1&&g.bullets[0].z==0&&g.bullets[0].velocityZ==0,"lateral movement leaves player shots at z zero");
    g=fixture();g.enemies[0].phase=EnemyPhase::Diving;g.enemies[0].timer=1;
    g.enemies[0].start={0,6};g.update({});
    check(g.enemies[0].z>0&&g.bullets.size()==1&&!g.bullets[0].ally&&g.bullets[0].z>0&&g.bullets[0].velocityZ<0,"diving enemy fires from its true depth toward player depth");
    const auto aimed=g.bullets[0];const float travel=(aimed.pos.y+4)/4;
    check(std::abs(aimed.previousZ-g.enemies[0].z)<.0001f&&std::abs(aimed.z-aimed.previousZ-aimed.velocityZ*Game3D::Step)<.0001f,"new hostile bullet sweep begins at emitter depth");
    check(std::abs(aimed.z+aimed.velocityZ*travel)<.001f,"enemy shot reaches z zero at player height");
    const float frozenZ=g.enemies[0].z,frozenBulletZ=g.bullets[0].z;g.pause();ticks(g,180);
    check(g.enemies[0].z==frozenZ&&g.bullets[0].z==frozenBulletZ,"pause freezes real depth motion");
    g=fixture();for(int i=0;i<3;++i)killTarget(g,100+i);
    check(g.hitStreak==3&&g.multiplier==2&&g.score==400,"third consecutive kill activates double points");
    for(int i=3;i<7;++i)killTarget(g,100+i);
    check(g.hitStreak==7&&g.multiplier==3&&g.score==1400&&g.bestScore==1400,"sixth kill activates triple points and records best");
    g.bullets.push_back({500,true,true,{0,9},{0,9}});g.update({});
    check(g.hitStreak==0&&g.multiplier==1&&g.score==1400,"missed allied shot resets combo but preserves score");
    for(int i=0;i<3;++i)killTarget(g,200+i);g.invulnerable=0;
    g.bullets.push_back({600,false,true,g.player,g.player});g.update({});
    check(g.hitStreak==0&&g.multiplier==1&&g.lives==2,"damage resets combo");
    g=fixture();killTarget(g,100);killTarget(g,101);
    for(int i=0;i<2;++i) {
        Enemy e;e.id=200+i;e.slot=e.pos=e.previous={float(i*2),0};e.phase=EnemyPhase::Formation;g.enemies.push_back(e);
        g.bullets.push_back({1200+i,true,true,{float(i*2),-.1f},{float(i*2),-.1f}});
    }
    g.update({});
    check(g.hitStreak==4&&g.multiplier==2&&g.kills==4&&g.score==600,"two simultaneous kills cross combo threshold exactly once per victim");
    g=fixture();killTarget(g,100);killTarget(g,101);g.invulnerable=0;
    Enemy simultaneous;simultaneous.id=200;simultaneous.phase=EnemyPhase::Formation;
    simultaneous.slot=simultaneous.pos=simultaneous.previous={0,0};g.enemies.push_back(simultaneous);
    g.bullets={{1200,true,true,{0,-.1f},{0,-.1f}},{1400,false,true,g.player,g.player}};g.update({});
    check(g.score==400&&g.kills==3&&g.lives==2&&g.hitStreak==0&&g.multiplier==1,"damage at same instant resets combo after stable ordered kill");
    g.reset();g.player.y=-40;bool sawDive=false,sawReturn=false,sawFormationAfter=false,sawDepthInDive=false,sawDepthInReturn=false;
    bool entryBoundary=false,diveBoundary=false,returnBoundary=false;
    for(int i=0;i<1200;++i){const auto before=g.enemies;g.update({});int busy=0;for(auto& e:g.enemies){if(e.phase==EnemyPhase::Warning||e.phase==EnemyPhase::Diving||e.phase==EnemyPhase::Returning)++busy;}if(busy>1)throw std::runtime_error("multiple attackers");
        sawDive|=g.enemies[0].phase==EnemyPhase::Diving;sawReturn|=g.enemies[0].phase==EnemyPhase::Returning;
        sawFormationAfter|=sawReturn&&g.enemies[0].phase==EnemyPhase::Formation;
        sawDepthInDive|=g.enemies[0].phase==EnemyPhase::Diving&&g.enemies[0].z>1;
        sawDepthInReturn|=g.enemies[0].phase==EnemyPhase::Returning&&g.enemies[0].z<-1;
        for(const auto& e:g.enemies){if(e.phase==EnemyPhase::Formation&&e.z!=0)throw std::runtime_error("formation not at zero depth");
            if(e.phase==EnemyPhase::Diving&&e.pos.y<=-4&&e.z!=0)throw std::runtime_error("dive misses player depth");
            const auto& old=before[e.id];
            if(e.previousZ!=old.z||std::abs(e.z-old.z)>.1f)throw std::runtime_error("depth continuity at route boundary");
            entryBoundary|=old.phase==EnemyPhase::Entering&&e.phase==EnemyPhase::Formation;
            diveBoundary|=old.phase==EnemyPhase::Diving&&e.phase==EnemyPhase::Returning;
            returnBoundary|=old.phase==EnemyPhase::Returning&&e.phase==EnemyPhase::Formation;}
    }
    check(sawDive&&sawReturn&&sawFormationAfter,"entry, dive and return cycle; one attacker");
    check(sawDepthInDive&&sawDepthInReturn,"3D routes pass in front and return behind, joining formation at z zero");
    check(entryBoundary&&diveBoundary&&returnBoundary,"depth and previous depth stay continuous through all route boundaries");
    check(g.remaining()==18&&g.phase==Phase::Playing,"offscreen returning enemies remain alive");
    for(int i=0;i<5;++i){g.reset();ticks(g,200,{false,true,true});g.reset();if(g.lives!=3||g.score!=0||g.shots!=0||!g.bullets.empty()||g.remaining()!=18||g.time!=0)throw std::runtime_error("restart leak");}
    check(true,"five clean restarts");
    g=Game3D{};g.reset();
    for(int i=0;i<60*120&&g.phase==Phase::Playing;++i)g.update(simplePilot(g));
    std::cout<<"PILOT result="<<int(g.phase)<<" time="<<g.time<<" lives="<<g.lives<<" kills="<<g.kills<<" score="<<g.score<<'\n';
    check(g.phase==Phase::Victory&&g.lives>0&&g.kills==18,"complete round won through lateral input and firing, without state overrides");
    g=Game3D{};g.reset();ticks(g,60*120);
    std::cout<<"IDLE result="<<int(g.phase)<<" time="<<g.time<<" lives="<<g.lives<<" kills="<<g.kills<<'\n';
    check(g.phase==Phase::Defeat&&g.lives==0&&g.shots==0&&g.score==0,"idle player naturally loses all three lives");
    std::cout<<checks<<" checks passed\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
