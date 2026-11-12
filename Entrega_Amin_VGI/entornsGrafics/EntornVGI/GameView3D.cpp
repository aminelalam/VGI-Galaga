#include "pch.h"
#include "EntornVGIDoc.h"
#include "EntornVGIView.h"

void CEntornVGIView::ClearGameInput() {
    game.cancelInput();
    gameKeys.fill(false); gameAccumulator=0;gameClock=std::chrono::steady_clock::now();
}
void CEntornVGIView::OnGameDemo() {
    demoMode=true;static_cast<CMainFrame*>(AfxGetMainWnd())->SetDemoLayout(true);ClearGameInput();SetFocus();Invalidate(FALSE);
}
void CEntornVGIView::OnGameEnvironment() {
    if(!GLEW_VERSION_4_6){AfxMessageBox(L"El entorno docente utiliza shaders OpenGL 4.6. La demo 3D sigue disponible en OpenGL 3.3.");return;}
    if(game.phase==galaga::Phase::Playing)game.pause();
    demoMode=false;static_cast<CMainFrame*>(AfxGetMainWnd())->SetDemoLayout(false);ClearGameInput();SetFocus();Invalidate(FALSE);
}
void CEntornVGIView::OnKillFocus(CWnd* next) {
    if(game.phase==galaga::Phase::Playing)game.pause();
    ClearGameInput();CView::OnKillFocus(next);Invalidate(FALSE);
}
BOOL CEntornVGIView::PreTranslateMessage(MSG* message) {
    if(demoMode && (message->message==WM_KEYDOWN||message->message==WM_KEYUP)) {
        UINT key=static_cast<UINT>(message->wParam);
        if(key=='A'||key=='D'||key=='W'||key=='S'||key=='Q'||key=='M'||key=='E'||key=='C'||key==VK_SHIFT||key==VK_F2||
            key==VK_LEFT||key==VK_RIGHT||key==VK_UP||key==VK_DOWN||key==VK_SPACE||key=='P'||key=='R'||
            key=='1'||key=='2'||key=='3'||key=='4'||key==VK_RETURN||key==VK_ESCAPE) {
            if(message->message==WM_KEYDOWN)OnKeyDown(key,1,UINT(message->lParam>>16));
            else OnKeyUp(key,1,UINT(message->lParam>>16));
            return TRUE;
        }
    }
    return CView::PreTranslateMessage(message);
}
void CEntornVGIView::GameKeyDown(UINT key,UINT flags) {
    if(key>=gameKeys.size())return;
    bool fresh=(flags&0x4000)==0 && !gameKeys[key];
    if(fresh && key=='P') {game.pause();ClearGameInput();}
    if(fresh && key>='1' && key<='4') {
        if(game.phase==galaga::Phase::Menu&&key<='3')game.selectShip(int(key-'1'));
        else if(game.phase==galaga::Phase::Playing)game.selectWeapon(int(key-'1'));
    }
    if(fresh && key=='M')gameAudio.setMuted(!gameAudio.isMuted());
    if(fresh && key=='E')game.cyclePower();
    if(fresh && key=='C')game.toggleCockpit();
    if(fresh && key==VK_F2)gameRenderer.toggleWireframe();
    if(fresh && key==VK_ESCAPE) {
        if(game.phase==galaga::Phase::Playing) game.pause();
        else if(game.phase!=galaga::Phase::Menu) game.returnToMenu();
        ClearGameInput();
    }
    if(fresh && ((key==VK_RETURN&&game.phase==galaga::Phase::Menu)||
        (key=='R'&&(game.phase==galaga::Phase::Victory||game.phase==galaga::Phase::Defeat)))) {
        game.reset();ClearGameInput();
    }
    gameKeys[key]=true;Invalidate(FALSE);
}
void CEntornVGIView::GameTick() {
    auto now=std::chrono::steady_clock::now();
    double elapsed=std::chrono::duration<double>(now-gameClock).count();gameClock=now;
    gameAudio.setScene(!demoMode?galaga::MusicScene::Silent:game.phase==galaga::Phase::Menu?
        galaga::MusicScene::Menu:game.phase==galaga::Phase::Playing?galaga::MusicScene::Combat:galaga::MusicScene::Silent);
    gameAudio.tick();
    if(!demoMode||game.phase!=galaga::Phase::Playing) {gameAccumulator=0;return;}
    // An inactive app or an inactive MDI document must never keep simulating.
    if(GetForegroundWindow()!=AfxGetMainWnd() || GetFocus()!=this) {
        game.pause();ClearGameInput();Invalidate(FALSE);return;
    }
    gameAccumulator+=std::min(elapsed,.1);
    galaga::Input input{gameKeys['A']||gameKeys[VK_LEFT],gameKeys['D']||gameKeys[VK_RIGHT],gameKeys[VK_SPACE],
        gameKeys['W']||gameKeys[VK_UP],gameKeys['S']||gameKeys[VK_DOWN],gameKeys['Q'],gameKeys[VK_SHIFT]};
    const int oldShots=game.shots,oldHits=game.hits,oldLives=game.lives,oldWave=game.wave;
    const float oldHull=game.hull,oldShield=game.shield;
    const auto oldStage=game.stage;
    int steps=0;
    while(gameAccumulator>=galaga::Game3D::Step && steps++<5) {
        game.update(input);gameAccumulator-=galaga::Game3D::Step;
        if(game.phase!=galaga::Phase::Playing){gameAccumulator=0;break;}
    }
    if(gameAccumulator>=galaga::Game3D::Step)gameAccumulator=std::fmod(gameAccumulator,double(galaga::Game3D::Step));
    if(game.shots>oldShots)gameAudio.play(galaga::SoundEvent::Shot);
    if(game.hits>oldHits)gameAudio.play(galaga::SoundEvent::Hit);
    if(game.lives<oldLives||game.hull<oldHull)gameAudio.play(galaga::SoundEvent::Damage);
    else if(game.shield<oldShield)gameAudio.play(galaga::SoundEvent::Hit);
    if(game.stage!=oldStage||game.wave!=oldWave)gameAudio.play(galaga::SoundEvent::Transition);
    if(game.phase==galaga::Phase::Victory)gameAudio.play(galaga::SoundEvent::Victory);
    if(game.phase==galaga::Phase::Defeat)gameAudio.play(galaga::SoundEvent::Defeat);
    Invalidate(FALSE);
}
