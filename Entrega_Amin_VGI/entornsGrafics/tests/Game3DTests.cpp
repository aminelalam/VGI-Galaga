#include "../EntornVGI/Game3D.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace galaga;
int checks=0;
void check(bool ok,const char* name){if(!ok)throw std::runtime_error(name);++checks;std::cout<<"PASS "<<name<<'\n';}
void ticks(Game3D& g,int n,Input input={}){for(int i=0;i<n;++i)g.update(input);}
Input pilot(const Game3D& g){
 const Enemy* t=nullptr;
 for(const auto& e:g.enemies)if(e.alive&&(!t||std::abs(e.pos.x-g.player.x)<std::abs(t->pos.x-g.player.x)))t=&e;
 if(!t)return {};
 return {g.player.x>t->pos.x+.05f,g.player.x<t->pos.x-.05f,true};
}
int main(){try{
 Game3D g;g.reset();check(g.remaining()==18&&g.lives==3,"fresh round");
 bool levels[3]{};for(const auto& e:g.enemies)levels[int(e.z/2.5f)+1]=true;
 check(levels[0]&&levels[1]&&levels[2],"three persistent world depths");
 auto initial=g.enemies;ticks(g,120);bool stationary=true;
 for(size_t i=0;i<initial.size();++i)stationary&=g.enemies[i].pos.x==initial[i].pos.x&&g.enemies[i].pos.y==initial[i].pos.y&&g.enemies[i].z==initial[i].z;
 check(stationary&&g.sparks.empty(),"static formation without animation");
 g.reset();ticks(g,60,{false,true,false});check(std::abs(g.player.x-6)<.001f,"lateral speed");
 ticks(g,120,{false,true,false});check(g.player.x==7.68f,"right boundary");
 ticks(g,240,{true,false,false});check(g.player.x==-7.68f,"left boundary");
 check(g.player.y==-4,"only lateral player movement");
 g.reset();ticks(g,60,{true,true,false});check(g.player.x==0,"opposite keys cancel");
 g.reset();ticks(g,120,{false,false,true});check(g.shots==9,"fire cooldown");
 float time=g.time;auto bullets=g.bullets;g.pause();ticks(g,120,{false,true,true});check(g.time==time&&g.bullets.size()==bullets.size(),"pause freezes world");
 g.pause();g.update({});check(g.time>time,"resume");
 check(Game3D::hitTime3D({0,-2},{0,2},2,2,{0,0},{0,0},0,0,.46f)<0,"screen overlap at different depths is not a hit");
 check(Game3D::hitTime3D({0,0},{0,0},-2,2,{0,0},{0,0},0,0,.46f)>=0,"swept depth collision");
 for(float z:{-2.5f,0.f,2.5f}){
  g.reset();g.enemies.resize(1);auto& e=g.enemies[0];e.pos=e.previous=e.slot={0,4};e.z=e.previousZ=z;
  ticks(g,60,{false,false,true});check(g.phase==Phase::Victory&&g.kills==1,"aligned enemy reachable at each depth");
 }
 g.reset();ticks(g,146);check(!g.bullets.empty()&&!g.bullets[0].ally,"stationary AI fires");
 auto b=g.bullets[0];float flight=(g.player.y-b.pos.y)/b.forwardSpeed();
 check(std::abs(b.z+b.velocityZ*flight)<.001f&&std::abs(b.pos.x+b.velocityX*flight-g.player.x)<.001f,"enemy shot aims at player in XYZ");
 for (float depth : {-2.5f,0.f,2.5f}) {
  for (float offset : {-.64f,.50f,.64f}) {
   g.reset();g.enemies.resize(1);
   auto& enemy=g.enemies[0];enemy.pos=enemy.previous={offset,14};enemy.z=enemy.previousZ=depth;
   check(g.aimTarget()==&enemy,"target marker and fire share acquisition at margin");
   g.update({false,false,true});
   auto shot=g.bullets[0];
   float speed=std::sqrt(shot.velocityX*shot.velocityX+shot.forwardSpeed()*shot.forwardSpeed()+shot.velocityZ*shot.velocityZ);
   check(std::abs(speed-Game3D::PlayerShotSpeed)<.001f,"constant shot speed in XYZ");
   g.player.x=-5; ticks(g,100);
   check(g.kills==1,"off-centre marked shot hits every depth after player moves");
  }
 }
 g.reset();g.enemies.resize(1);g.enemies[0].pos=g.enemies[0].previous={1.1f,4};g.enemies[0].z=g.enemies[0].previousZ=0;
 check(g.aimTarget()==nullptr,"outside capture margin has no target marker");
 g.update({false,false,true});ticks(g,30);check(g.kills==0,"real near miss does not kill");
 g.reset();g.player.x=g.enemies[0].pos.x;
 check(g.aimTarget()==&g.enemies[0],"front row is targeted first");
 g.enemies[0].alive=false;check(g.aimTarget()==&g.enemies[6],"next depth becomes target after front dies");
 g.reset();g.enemies.resize(1);g.enemies[0].pos=g.enemies[0].previous={0,4};g.enemies[0].z=g.enemies[0].previousZ=0;
 g.bullets={{100,true,true,{0,3.8f},{0,3.8f}},{101,true,true,{0,3.8f},{0,3.8f}}};g.update({});
 check(g.kills==1&&g.score==100,"simultaneous hits award one kill");
 g.reset();g.invulnerable=1;g.bullets={{100,false,true,{2,-4.7f},{2,-4.7f}}};ticks(g,2);
 check(g.bullets.empty(),"missed enemy shot retired behind player before camera");
 g.reset();g.enemies.resize(1);g.enemies[0].pos=g.enemies[0].previous={0,4};g.enemies[0].z=g.enemies[0].previousZ=0;
 g.bullets={{100,true,true,{0,4},{0,4},0}};g.update({});check(g.kills==0,"expired shot cannot cause a fresh hit");
 g.reset();g.invulnerable=0;g.bullets={{100,false,true,g.player,g.player},{101,false,true,g.player,g.player}};g.update({});
 check(g.lives==2&&g.respawn>0,"simultaneous hits cost one life");
 g.reset();g.selectedShip=2;g.score=100;g.reset();check(g.selectedShip==2&&g.bestScore==100&&g.score==0,"restart preserves selection and record");
 for(int i=0;i<5;++i){ticks(g,100,{false,true,true});g.reset();}check(g.remaining()==18&&g.bullets.empty()&&g.time==0&&g.lives==3,"five clean restarts");
 g.returnToMenu();g.selectShip(1);check(g.phase==Phase::Menu&&g.selectedShip==1,"menu selection");
 g.reset();for(int i=0;i<60*120&&g.phase==Phase::Playing;++i)g.update(pilot(g));
 std::cout<<"PILOT lives="<<g.lives<<" kills="<<g.kills<<" seconds="<<g.time<<'\n';
 check(g.phase==Phase::Victory&&g.kills==18,"full round won using ordinary movement and fire");
 g.reset();ticks(g,60*120);check(g.phase==Phase::Defeat&&g.lives==0,"idle player loses naturally");
 std::cout<<checks<<" checks passed\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
