#include "pch.h"
#include "EntornVGIDoc.h"
#include "EntornVGIView.h"

void CEntornVGIView::ClearGameInput() {
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
        if(key=='A'||key=='D'||key==VK_LEFT||key==VK_RIGHT||key==VK_SPACE||key=='P'||key=='R'||
            key=='1'||key=='2'||key=='3'||key==VK_RETURN||key==VK_ESCAPE) {
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
    if(fresh && key>='1' && key<='3') game.selectShip(int(key-'1'));
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
    if(!demoMode||game.phase!=galaga::Phase::Playing) {gameAccumulator=0;return;}
    // An inactive app or an inactive MDI document must never keep simulating.
    if(GetForegroundWindow()!=AfxGetMainWnd() || GetFocus()!=this) {
        game.pause();ClearGameInput();Invalidate(FALSE);return;
    }
    gameAccumulator+=std::min(elapsed,.1);
    galaga::Input input{gameKeys['A']||gameKeys[VK_LEFT],gameKeys['D']||gameKeys[VK_RIGHT],gameKeys[VK_SPACE]};
    int steps=0;
    while(gameAccumulator>=galaga::Game3D::Step && steps++<5) {
        game.update(input);gameAccumulator-=galaga::Game3D::Step;
        if(game.phase!=galaga::Phase::Playing){gameAccumulator=0;break;}
    }
    if(gameAccumulator>=galaga::Game3D::Step)gameAccumulator=std::fmod(gameAccumulator,double(galaga::Game3D::Step));
    Invalidate(FALSE);
}
