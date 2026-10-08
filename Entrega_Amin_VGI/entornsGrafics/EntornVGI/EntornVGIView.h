
//******** PRACTICA VISUALITZACIÓ GRÀFICA INTERACTIVA (Escola Enginyeria - UAB)
//******** Entorn bàsic VS2026 MULTIFINESTRA amb OpenGL 4.6, interfície MFC i llibreries GLM
//******** Ferran Poveda, Marc Vivet, Carme Julià, Débora Gil, Enric Martí Gòdia (Setembre 2026)
// EntornVGIView.h: interfaz de la clase CEntornVGIView
//

#pragma once

#include "MainFrm.h"

// Entorn VGI : Constants de l'aplicació entorn VGI
#include "constants.h"

// Entorn VGI: Includes shaders GLSL
#include <gl/glew.h>
#include <gl/wglew.h>

// Include all GLM core / GLSL features
#include <glm/glm.hpp>		// perspective, translate, rotate
// Include all GLM extensions
#include <glm/ext.hpp>

#include "shader.h"

// Entorn VGI: OBJECTE OBJ. Include per la definició de l'objecte Obj_OBJ
#include "objLoader.h"

// Entorn VGI. QUATERNIONS: Include per a la definició del tipus GL_QUAT i crida a les funcions de quatern.
//#include "quatern.h"


class CEntornVGIView : public CView
{
protected: // Crear sólo a partir de serialización
	CEntornVGIView() noexcept;
	DECLARE_DYNCREATE(CEntornVGIView)

// Atributos
public:
	CEntornVGIDoc* GetDocument() const;

//-------------- Entorn VGI: Variables globals de CPractivaView
	HGLRC	 m_hrc;		// OpenGL Rendering Context 

// Entorn VGI: Variables de control per Menú Càmera: Esfèrica, Navega, Mòbil, Zoom, Satelit, Polars... 
	char camera;	// Variable que controla el tipus de càmera segons valors definits en constants.h
	bool mobil;		// Opció canvi de Punt de Vista interactiu (mobil) [0:NO,1:SI]
	bool zzoom;		// Opció Zoom interactiu (zoom) [0:NO,1:SI]
	bool zzoomO;	// Opció Zoom en Projecció Ortogràfica adaptant Volum Visualització [0:NO,1:SI]
	bool satelit;	// Opció de navegació animada al volt de l'objecte centrat definint increment per mouse (SATÈLIT)

// Entorn VGI: Variables de control de l'opció Càmera->Navega?
	GLdouble n[3];			// Punt cap on mira.
	CPunt3D opvN;			// Definició Orígen Punt de Vista (en coordenades món)
	double angleZ;			// angle de rotació de la trajectòria.
	glm::mat4 ViewMatrix;	// Matriu de Càmera a passar al shader

// Entorn VGI: Variables de control de l'opció Càmera->Geode?
	CEsfe3D OPV_G;			// Paràmetres camera en coord. esfèriques (R,alfa,beta) per a Vista Geode

	// Entorn VGI: Variables de control per Menú Vista: fullsecreen, pan, dibuixar eixos i grid. 
	bool fullscreen;	// Opció booleana per Pantalla Completal [0:NO,1:SI]
	bool pan;			// Opcio Pan. Desplaçament del centre de l'esfera de Vista [0:NO,1:SI]
	bool eixos;			// Opció per dibuixar els eixos X,Y,Z (Eixos?) [0:NO,1:SI]
	Shader shaderEixos;	// Ientificador pel shader d'eixos.
	GLuint eixos_programID;
	GLuint eixos_Id;	// Identificador del VBO per a dibuixar els eixos.
	bool sw_grid;		// Opció per activar comandes teclat per moure grids [TRUE] o no [FALSE]
	CMask3D grid;		// Opció per a dibuixar grids (.x: grid XY, .y:grid XZ, .z: grid YZ, .w:grid XYZ)
	CPunt3D hgrid;		// Alçada de cada grid (.x: grid XY, .y:grid XZ, .z: grid YZ, .w:grid XYZ)

	// Entorn VGI: Variables de l'opció Vista->Pan
	double fact_pan;	// Factor de desplaçament de la càmara (opció pan).
	CPunt3D tr_cpv;		// Vector de Traslació del Centre del Punt de Vista actiu dins opció pan.
	CPunt3D tr_cpvF;	// Vector de Traslació del Centre del Punt de Vista (fixat amb INSERT dins opció pan) 
						//       i actiu fora l'opció pan.

// Entorn VGI: Variables de control per les opcions de menú Projecció, Objecte
	char projeccio;	// Menú Projecció: Tipus de projeccio
	glm::mat4 ProjectionMatrix;// Matriu de Projecció a passar al shader
	char objecte;	// Menú Objecte: Tipus d'Objecte

// Entorn VGI: Variables de control Skybox Cube
	bool SkyBoxCube;			// Booleana que controla si es visualitza Skybox [TRUE] o no [FALSE].
	Shader shader_SkyBoxC;		// Shader Skybox Cub
	GLuint skC_programID;		// Identificador program Skybox Cube
	CVAO skC_VAOID;				// Identificador VAO List (vaoId, vboId, nVertexs) per a Skybox Cube
	GLuint cubemapTexture;		// Identificador textura cubemap.
	Shader shaderSkyBox;		// Shader SkyBox

	// Entorn VGI: Variables de control del menú Transforma
	bool transf;	// Booleana per activar Transformacions (true) o no (false).
	bool trasl;		// Booleana d'activació de la Traslació (true) o no (false).
	bool rota;		// Booleana d'activació de la Rotació (true) o no (false).
	bool escal;		// Booleana d'activació de l'Escalatge (true) o no (false).
	double fact_Tras, fact_Rota;	// Increments de Traslació i Rotació.
	INSTANCIA TG;	// Estructura que conté TG del menú Transforma actiu dins qualsevol opció de Transforma 
					//      (Traslació Rotació i Escalatge).
	INSTANCIA TGF;	// Estructura que conté TG del menú Transforma fixat amb INSERT dins les opcions de Transforma
					//     i actiu fora l'opció Transforma.
	bool transX;	// Opció Mobil Eix X?: TG interactives per l'eix X via mouse [F:NO,T:SI].
	bool transY;	// Opció Mobil Eix Y?: TG interactives per l'eix Y via mouse [F:NO,T:SI].
	bool transZ;	// Opció Mobil Eix Z?: TG interactives per l'eix Z via mouse [F:NO,T:SI].
	glm::mat4 GTMatrix; // Matriu de Transformacions Geomètriques a passar al shader

// Entorn VGI: Variables de control per les opcions de menú Ocultacions
	bool front_faces;// Menú ocultacions: Determina si les cares visibles són les frontals [true-defecte] o les back [false] pel Test de Visibilitat.
	bool test_vis;  // Menú ocultacions: Activa [true] o desactiva [false] Test Visibilitat.
	bool oculta;    // Menú ocultacions: Activa [true] o desactiva [false] Ocultacions (Z-buffer).

// Entorn VGI: Variables de control del menú Iluminació	
	bool ifixe;         // Iluminació fixe independent del PV (ifixe=1) 
// o depenent (mobil) respecte el PV (casc miner) (ifixe=0)
	bool ilum2sides;	// Iluminació de les cares FRONT i BACK [TRUE] o només les FRONT [FALSE]
	char ilumina;		// Tipus d'il.luminació [PUNTS 'P',FILFERROS 'w', PLANA 'f',GOURAUD 'g', PHONG 'p']
	bool sw_material[5];// Variable que controla els coeficients de reflectivitat del material [TRUE] o no [FALSE]:
// [0]: emission, [1]: ambient, [2]: difusa, [3] especular.
	bool sw_material_old[5]; // Variable que guarda els valors de sw_material mentre no hi ha reflectivitat de material (refl_material=false).
	bool textura;       // Control de textures desactivades [0:NO] o activades [1:SI]
	char t_textura;		// Tipus de textures (predefinides o per fitxer)
	bool textura_map;	// Mapping de textura modulat amb la llum [TRUE] o calcat [FALSE]
	GLuint texturesID[NUM_MAX_TEXTURES];// Vector d'identificadors de textura de l'entorn. Si no hi ha textura activa, agafa el valor -1.
										// 0: Textura general, assignada a la lectura de fitxer.
										// 1-6: Textures assignables
										// 7: Textura pel Fractal
										// 8-9: Lliures
	bool tFlag_invert_Y; // Booleana que activa la inversió coordenada textura t (o Y) a 1.0-cty segons llibreria SOIL (TRUE) o no (FALSE).

// Entorn VGI: Variables de control del menú Llums
	bool llum_ambient;		// Booleana que controla la llum ambient (SI/NO).
	LLUM llumGL[NUM_MAX_LLUMS];		// Vector de llums d'OpenGL
	bool sw_llambient;		// Booleana que controla modus de configurar el color de la llum ambient [TRUE] o no [FALSE]
	CColor col_llambient;	// Color llum ambient.

// Entorn VGI: Variables de control del menú Shaders
	char shader;				// Tipus de shader [FLAT, GOURAUD, PHONG, FILE, PROG_BINARY_SHADER]
	GLuint shader_programID;	// Shader Program que conté el Vertex i Fragment program.
	Shader shaderLighting;		// Shader que implementa els codis GLSL d'il.luminació

// Entorn VGI: Variables butons de mouse 
	CPoint m_PosEAvall, m_PosDAvall; // Coordenades del cursor quan el boto esquerre(E) o dret(D) del 
//    mouse ha estat clicat.
	bool m_ButoEAvall, m_ButoDAvall; //TRUE si el boto esquerre(E) o dret(D) del mouse esta clicat.
	CEsfe3D m_EsfeEAvall;			 // Coordenades Esfèriques del PV (OPV) quan el boto esquerre(E) o dret(D) del 
//										mouse ha estat clicat.
	CEsfe3D m_EsfeIncEAvall;		 // Increment de desplaçament en coordenades Esfèriques del PV (OPV).

// Entorn VGI: Variables que controlen paràmetres visualització: Mides finestra Windows i PV
	int w, h;				// Mides de la finestra Windows (w-amplada,h-alçada)
	int w_old, h_old;		// Mides de la finestra Windows (w-amplada,h-alçada) per restaurar Finestra des de fullscreen
	CEsfe3D OPV;			// Paràmetres camera en coord. esfèriques (R,alfa,beta)
	char Vis_Polar;			// Variable que controla orientació dels eixos en Visualització Interactiva (POLARZ,POLARY,POLARX)

// Entorn VGI: Color de fons i de l'objecte
	bool fonsR, fonsG, fonsB;	// Booleanes per controlar variació de color per teclat.
	CColor c_fons;			// Intensitat de color de fons.
	bool sw_color;			// Booleana que controla el modus de configurar color de l'objecte per teclat [TRUE] o no [FALSE]
	CColor col_obj;			// Color de l'objecte simple.

// Entorn VGI: Objecte OBJ:
	COBJModel* ObOBJ;		// Variable d'objecte format OBJ (*.OBJ)
	CVAO vao_OBJ;			// Identificador VAO per a objecte OBJ

// Entorn VGI: OBJECTE --> Corbes Bezier i BSpline
	int npts_T;							// Número de punts de control de la corba en el Vector corbaSpline (<=MAX_PATH_SPLINE)
	CPunt3D PC_t[MAX_PATCH_CORBA];		// Vector que enmagatzema Punts de Control Corba Spline
	GLdouble pas_Corba;					// Increment del paràmetre t per al dibuix de les corbes.
	GLdouble pas_CS;						// Increment del paràmetre t per al dibuix de corbes i superficies.
	bool sw_Punts_Control;				// Booleana que activa o desactiva la visualització dels punts de control de la corba o de la superficie

// Entorn VGI. TRIEDRE DE FRENET / DARBOUX: VT: vector Tangent, VNP: Vector Normal Principal, VBN: vector BiNormal
	bool dibuixa_TriedreFrenet;			// Booleana que controla dibuix de Triedre de Frenet per a cada punt de la Corba [TRUE-dibuixa, FALSE-no dibuixa]
	bool dibuixa_TriedreDarboux;		// Booleana que controla dibuix de Triedre de Darboux per a cada punt de la Corba Loxodroma[TRUE-dibuixa, FALSE-no dibuixa]
	CPunt3D VT, VNP, VBN;				// TRIEDRE de FRENET: VT: Vector Tangent, VNP: Vector Normal Principal, VBN: Vector BiNormal.

// Entorn VGI: Variables del Timer
	double t;		// Paràmetre t pel Timer.
	bool anima;		// Booleana que controla si l'animació és activa (TRUE) o no (FALSE)
					//    dins la funció de control del rellotge OnTimer.


// Entorn VGI : QUATERNIONS: Animació de cossos rígids per QUATERNIONS
	bool animaQ;			// Booleana que controla si l'animació rígida és activa 
	bool rotaQ;				// Booleana que verifica si les rotacions es fan per Quaternions.
/*
	CPunt3D keyf_Rota[MAX_KEYFRAMES_Q]; // Estructura que guarda fins a 3 keyframes d'orientació de l'objecte rígid
	//	en angles d'Euler. Es graben amb la tecla INSERT.
	GL_Quat keyf_Quat[MAX_KEYFRAMES_Q]; // Estructura que guarda fins a 3 keyframes d'orientació de l'objecte rígid
	//	en Quaternions. Es graben amb la tecla INSERT.
	CPunt3D keyf_Tras[MAX_KEYFRAMES_Q]; // Estructura que guarda fins a 3 keyframes de TRASLACIÓ de 
	//	l'objecte rígid. Es graben amb la tecla INSERT.
	CPunt3D keyf_Scal[MAX_KEYFRAMES_Q]; // Estructura que guarda fins a 3 keyframes d'ESCALATGE de 
	//	l'objecte rígid. Es graben amb la tecla INSERT.
	CPunt3D eix_Rota;		// Eix de rotació interpolat resultat dels quaternions.
	GLdouble angle_Rota;		// Angle de rotació interpolat dels quaternions.
	GLdouble QMatrix[16];	// Matriu de rotació corresponent a un quaternió.	
	CPunt3D int_Tras;		// Valors de Traslació interpolats en moviment rigid.
	CPunt3D int_Scal;		// Valors d'Escalat interpolats en moviment rígid.
	int np_InQ;				// Controla el número de keyframes entrats.
	bool animaQ;			// Booleana que controla si l'animació rígida és activa 
	//   (TRUE) o no (FALSE).
	CPunt3D keyf_RotaI, keyf_RotaF, keyf_RotaT;	// Angles Euler inicial  (keyf_RotaI), final (keyf_RotaF) i 
	// intermig (keyf_RotaT) del moviment d'objectes rígids.
	GL_Quat qT;				// Quaternió que acumula ordenadament les rotacions aplicades sobre l'objecte en moviment d'objectes rígids.
	GL_Quat qI, qF;			// Quaternions inicial (qI), final (qF) del moviment d'objectes rígids.
	GL_Quat qT_L, qT_S;		// Quaternions intermitjos per interpolació linial (qT_L) i esfèrica (qT_S) del moviment d'objectes rígids.
	GL_Quat qI_E, qF_E, qT_E;// Quaternions inicial (qI_E), final (qF_E) i intermig (qT_E) convertits i interpolats dels angles d'Euler.
	bool lerp, slerp;		// Booleanes que activen la interpolació linial (lerp) i 
							//     esfèrica (slerp).
*/

// Entorn VGI: Variables de l'objecte FRACTAL
	char t_fractal;		// Tipus de fractal.
	char soroll;		// Menú Fractals: Tipus de soroll
	int pas, pas_ini;	// Resolució del fractal inicial (pas_ini) i de visualització (pas).
	bool sw_il;			// Booleana que controla si cal compilar el fractal (sw_il=1) o no (sw_il=0)
	bool palcolFractal;	// Booleana que activa coloració del fractal segons paleta de colors [TRUE] o no [FALSE].
	/*
	bool zzoomF;		// variable que activa [TRUE] o desactiva [FALSE] el Zoom Fractal.
	char paletaFractal;	// Variable que conté la paleta de colors a aplicar el fractal.
	CVAO vaoFractal;	// Variable VAO per al Fractal
	int nvertexsFractal; // Nombre de vèrtexs del Fractal per a VAO.
	CVAO vaoMar;		// Variable VAO per al mar del Fractal
*/

// Entorn VGI: ROBOT ARTICULAT
	bool animaR;		// Booleana que controla si l'animació del robot és activa (TRUE) o no (FALSE).
	bool sw_robot;		// Switch que activa (TRUE) o desactiva (FALSE) moviments de robot per teclat.
	bool sh_rmov;		// Shift que intercanvia els moviments del robot per teclat. 
	/*
	double angles_R[6]; // Vector d'angles que indiquen la posició del braç del robot / Synkope
	// [0]: Rotació Z del braç.
	// [1]: Rotació X del braç.
	// [2]: Rotació Z del canell.
	// [3]: Rotació X del canell.
	// [4]: Rotació Y del canell.
	// [5]: Tancament de la ma.	  
	bool sh_rmov;	// Shift que intercanvia els moviments del robot per teclat. 
	//   (TRUE: moviments braç i mà, FALSE: moviments canell)
	double pos_RI[6], pos_RF[6]; // Angles que defineixen dos keyframes: posició inicial (pos_RI)
	// i final del robot per fer l'animació. Es graben amb la
	// tecla INSERT.
	double keyf_R[MAX_KEYFRAMES][6];	// Estructura que guarda fins a 5 keyframes de la cama articulada (0: Esquerra, 1: Dreta).
	//    Es graben amb la tecla INSERT.
	int np_In;				// Controla el número de punts de l'animació entrats
	GLdouble num_frame;		// Número de frame de l'animació.
	GLdouble incr_frame;	// Increment positiu/negatiu per assegurar continuitat a l'animació.
*/



// Entorn VGI: FPS
	clock_t beginFrame, endFrame, deltaTime;
	unsigned int frames;
	double  frameRate, averageFrameTimeMilliseconds, fps;

// Entorn VGI: Altres variables
	GLdouble mida;	// Factor d'escala per calcular Volum de Visualització de l'objecte que encaixi.
	CString nom;	// Nom de fitxer.
	CString buffer; // Buffer que magatzema string caracters corresponent a variables double a printar en Status Bar (funció Barra_Estat).
//-------------- Entorn VGI: Fi De Variables globals de CEntornVGIView

// Operaciones
public:

// Reemplazos
public:
	virtual void OnDraw(CDC* pDC);  // Reemplazado para dibujar esta vista
	virtual BOOL PreCreateWindow(CREATESTRUCT& cs);
protected:
	virtual BOOL OnPreparePrinting(CPrintInfo* pInfo);
	virtual void OnBeginPrinting(CDC* pDC, CPrintInfo* pInfo);
	virtual void OnEndPrinting(CDC* pDC, CPrintInfo* pInfo);

// Entorn VGI : Funcions de càrrega i activació de shaders
	void InitAPI();
	void GetGLVersion(int* major, int* minor);
	void APIENTRY glDebugOutput(GLenum source, GLenum type, GLuint id, GLenum severity, GLsizei length,
		const GLchar* message, const void* userParam);
	void OnInitialUpdate();


// Implementación
public:
	virtual ~CEntornVGIView();
#ifdef _DEBUG
	virtual void AssertValid() const;
	virtual void Dump(CDumpContext& dc) const;
#endif

// Entorn VGI : Funcions locals d'entornVGIView
	void CEntornVGIView::configura_Escena();
	void CEntornVGIView::dibuixa_Escena();
	void CEntornVGIView::Barra_Estat();
	void CEntornVGIView::double2CString(double varf);
	int CEntornVGIView::Log2(int num);							// Log2: Càlcul del log base 2 de num
	char* CEntornVGIView::CString2Char(CString entrada);		// Conversió string CString --> char *
	void CEntornVGIView::Refl_MaterialOff();					// Desactivar Reflexió de Material
	void CEntornVGIView::Refl_MaterialOn();						// Activar Reflexió de Material
	int CEntornVGIView::llegir_ptsC(char* nomf);				// Lectura Punts de Control Corba (B-spline o Bezier)
	bool CEntornVGIView::llegir_FontLlum(char* nomf);			// Lectura Paràmetres Font de Llum
	std::string CEntornVGIView::CString2String(const CString& cString); // Conversió CString --> std::string

// Entorn VGI: Funcions de tractament de teclat en diferents modus
	void CEntornVGIView::Teclat_ColorObjecte(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_ColorFons(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_Navega(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_Pan(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_TransEscala(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_TransRota(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_TransTraslada(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_Grid(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_PasCorbes(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_RobotMA(UINT nChar, UINT nRepCnt);
	void CEntornVGIView::Teclat_RobotMB(UINT nChar, UINT nRepCnt);

// Entorn VGI: Crida a Status Bar per imprimir informació de variables de control
	CMFCStatusBar& GetStatusBar() const
	{	return ((CMainFrame*)AfxGetMainWnd())->GetStatusBar();
	}

protected:
// Entorn VGI: Variables Full Screen
	CWnd* saveParent = NULL;
	CMenu* ContextMenu = NULL;

private:
// Rendering Context and Device Context Pointers
	HGLRC m_hRC = NULL;
	CDC* m_pDC = NULL;

// Funciones de asignación de mensajes generadas
protected:
	afx_msg void OnFilePrintPreview();
	afx_msg void OnRButtonUp(UINT nFlags, CPoint point);
	afx_msg void OnContextMenu(CWnd* pWnd, CPoint point);
	DECLARE_MESSAGE_MAP()
public:
	afx_msg int OnCreate(LPCREATESTRUCT lpCreateStruct);
	afx_msg void OnDestroy();
	afx_msg void OnKeyDown(UINT nChar, UINT nRepCnt, UINT nFlags);
	afx_msg void OnKeyUp(UINT nChar, UINT nRepCnt, UINT nFlags);
	afx_msg void OnLButtonDown(UINT nFlags, CPoint point);
	afx_msg void OnLButtonUp(UINT nFlags, CPoint point);
	afx_msg void OnMouseMove(UINT nFlags, CPoint point);
	afx_msg BOOL OnMouseWheel(UINT nFlags, short zDelta, CPoint pt);
	afx_msg void OnPaint();
	afx_msg void OnRButtonDown(UINT nFlags, CPoint point);
	afx_msg void OnSize(UINT nType, int cx, int cy);
	afx_msg void OnTimer(UINT_PTR nIDEvent);
	afx_msg void OnCameraEsferica();
	afx_msg void OnUpdateCameraEsferica(CCmdUI* pCmdUI);
	afx_msg void OnCameraMobil();
	afx_msg void OnUpdateCameraMobil(CCmdUI* pCmdUI);
	afx_msg void OnCameraZoom();
	afx_msg void OnUpdateCameraZoom(CCmdUI* pCmdUI);
	afx_msg void OnCameraZoomOrto();
	afx_msg void OnUpdateCameraZoomOrto(CCmdUI* pCmdUI);
	afx_msg void OnCameraSatelit();
	afx_msg void OnUpdateCameraSatelit(CCmdUI* pCmdUI);
	afx_msg void OnCameraPolarsX();
	afx_msg void OnUpdateCameraPolarsX(CCmdUI* pCmdUI);
	afx_msg void OnCameraPolarsY();
	afx_msg void OnUpdateCameraPolarsY(CCmdUI* pCmdUI);
	afx_msg void OnCameraPolarsZ();
	afx_msg void OnUpdateCameraPolarsZ(CCmdUI* pCmdUI);
	afx_msg void OnCameraNavega();
	afx_msg void OnUpdateCameraNavega(CCmdUI* pCmdUI);
	afx_msg void OnCameraOrigenNavega();
	afx_msg void OnCameraGeode();
	afx_msg void OnUpdateCameraGeode(CCmdUI* pCmdUI);
	afx_msg void OnCameraOrigenGeode();
	afx_msg void OnArxiuObrirFractal();
	afx_msg void OnArxiuObrirFontLlum();
	afx_msg void OnArxiuObrirSkybox();
	afx_msg void OnArxiuObrirOBJ();
	afx_msg void OnVistaFullScreen();
	afx_msg void OnUpdateVistaFullScreen(CCmdUI* pCmdUI);
	afx_msg void OnVistaPan();
	afx_msg void OnUpdateVistaPan(CCmdUI* pCmdUI);
	afx_msg void OnVistaOrigenPan();
	afx_msg void OnVistaEixos();
	afx_msg void OnUpdateVistaEixos(CCmdUI* pCmdUI);
	afx_msg void OnVistaSkybox();
	afx_msg void OnUpdateVistaSkybox(CCmdUI* pCmdUI);
	afx_msg void OnProjeccioPerspectiva();
	afx_msg void OnUpdateProjeccioPerspectiva(CCmdUI* pCmdUI);
	afx_msg void OnObjecteCap();
	afx_msg void OnUpdateObjecteCap(CCmdUI* pCmdUI);
	afx_msg void OnObjecteCub();
	afx_msg void OnUpdateObjecteCub(CCmdUI* pCmdUI);
	afx_msg void OnObjecteCubRGB();
	afx_msg void OnUpdateObjecteCubRGB(CCmdUI* pCmdUI);
	afx_msg void OnObjecteEsfera();
	afx_msg void OnUpdateObjecteEsfera(CCmdUI* pCmdUI);
	afx_msg void OnObjecteTetera();
	afx_msg void OnUpdateObjecteTetera(CCmdUI* pCmdUI);
	afx_msg void OnObjecteArc();
	afx_msg void OnUpdateObjecteArc(CCmdUI* pCmdUI);
	afx_msg void OnCorbesBezier();
	afx_msg void OnUpdateCorbesBezier(CCmdUI* pCmdUI);
	afx_msg void OnCorbesLemniscata();
	afx_msg void OnUpdateCorbesLemniscata(CCmdUI* pCmdUI);
	afx_msg void OnCorbesBSpline();
	afx_msg void OnUpdateCorbesBSpline(CCmdUI* pCmdUI);
	afx_msg void OnCorbesHermitte();
	afx_msg void OnUpdateCorbesHermitte(CCmdUI* pCmdUI);
	afx_msg void OnCorbesCatmullRom();
	afx_msg void OnUpdateCorbesCatmullRom(CCmdUI* pCmdUI);
	afx_msg void OnCorbesPuntsControl();
	afx_msg void OnUpdateCorbesPuntsControl(CCmdUI* pCmdUI);
	afx_msg void OnCorbesTriedreFrenet();
	afx_msg void OnUpdateCorbesTriedreFrenet(CCmdUI* pCmdUI);
	afx_msg void OnObjecteMatriuPrimitives();
	afx_msg void OnUpdateObjecteMatriuPrimitives(CCmdUI* pCmdUI);
	afx_msg void OnObjecteMatriuPrimitivesVAO();
	afx_msg void OnUpdateObjecteMatriuPrimitivesVAO(CCmdUI* pCmdUI);
	afx_msg void OnObjecteTie();
	afx_msg void OnUpdateObjecteTie(CCmdUI* pCmdUI);
	afx_msg void OnTransformaTraslacio();
	afx_msg void OnUpdateTransformaTraslacio(CCmdUI* pCmdUI);
	afx_msg void OnTransformaOrigenTraslacio();
	afx_msg void OnTransformaRotacio();
	afx_msg void OnUpdateTransformaRotacio(CCmdUI* pCmdUI);
	afx_msg void OnTransformaOrigenRotacio();
	afx_msg void OnTransformaEscalat();
	afx_msg void OnUpdateTransformaEscalat(CCmdUI* pCmdUI);
	afx_msg void OnTransformaOrigenEscalat();
	afx_msg void OnTransformaMobilX();
	afx_msg void OnUpdateTransformaMobilX(CCmdUI* pCmdUI);
	afx_msg void OnTransformaMobilY();
	afx_msg void OnUpdateTransformaMobilY(CCmdUI* pCmdUI);
	afx_msg void OnTransformaMobilZ();
	afx_msg void OnUpdateTransformaMobilZ(CCmdUI* pCmdUI);
	afx_msg void OnOcultacionsFrontFaces();
	afx_msg void OnUpdateOcultacionsFrontFaces(CCmdUI* pCmdUI);
	afx_msg void OnOcultacionsTestVisibilitat();
	afx_msg void OnUpdateOcultacionsTestVisibilitat(CCmdUI* pCmdUI);
	afx_msg void OnOcultacionsZBuffer();
	afx_msg void OnUpdateOcultacionsZBuffer(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioLlumFixe();
	afx_msg void OnUpdateIluminacioLlumFixe(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioCaresFrontBack();
	afx_msg void OnUpdateIluminacioCaresFrontBack(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioPunts();
	afx_msg void OnUpdateIluminacioPunts(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioFilferros();
	afx_msg void OnUpdateIluminacioFilferros(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioPlana();
	afx_msg void OnUpdateIluminacioPlana(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioSuau();
	afx_msg void OnUpdateIluminacioSuau(CCmdUI* pCmdUI);
	afx_msg void OnMaterialMaterialColor();
	afx_msg void OnUpdateMaterialMaterialColor(CCmdUI* pCmdUI);
	afx_msg void OnMaterialEmissio();
	afx_msg void OnUpdateMaterialEmissio(CCmdUI* pCmdUI);
	afx_msg void OnMaterialAmbient();
	afx_msg void OnUpdateMaterialAmbient(CCmdUI* pCmdUI);
	afx_msg void OnMaterialDifusa();
	afx_msg void OnUpdateMaterialDifusa(CCmdUI* pCmdUI);
	afx_msg void OnMaterialEspecular();
	afx_msg void OnUpdateMaterialEspecular(CCmdUI* pCmdUI);
	afx_msg void OnIluminacioTextures();
	afx_msg void OnUpdateIluminacioTextures(CCmdUI* pCmdUI);
	afx_msg void OnTexturaImatgeSOIL();
	afx_msg void OnUpdateTexturaImatgeSOIL(CCmdUI* pCmdUI);
	afx_msg void OnTexturaFlagInvertY();
	afx_msg void OnUpdateTexturaFlagInvertY(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlumAmbient();
	afx_msg void OnUpdateLlumsLlumAmbient(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum0();
	afx_msg void OnUpdateLlumsLlum0(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum1();
	afx_msg void OnUpdateLlumsLlum1(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum2();
	afx_msg void OnUpdateLlumsLlum2(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum3();
	afx_msg void OnUpdateLlumsLlum3(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum4();
	afx_msg void OnUpdateLlumsLlum4(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum5();
	afx_msg void OnUpdateLlumsLlum5(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum6();
	afx_msg void OnUpdateLlumsLlum6(CCmdUI* pCmdUI);
	afx_msg void OnLlumsLlum7();
	afx_msg void OnUpdateLlumsLlum7(CCmdUI* pCmdUI);
	afx_msg void OnShadersFlat();
	afx_msg void OnUpdateShadersFlat(CCmdUI* pCmdUI);
	afx_msg void OnShadersGouraud();
	afx_msg void OnUpdateShadersGouraud(CCmdUI* pCmdUI);
	afx_msg void OnUpdateShadersPhong(CCmdUI* pCmdUI);
	afx_msg void OnShadersPhong();
	afx_msg void OnShadersLoadFiles();
	afx_msg void OnUpdateShadersLoadFiles(CCmdUI* pCmdUI);
	afx_msg void OnShadersPBinaryRead();
	afx_msg void OnUpdateShadersPBinaryRead(CCmdUI* pCmdUI);
	afx_msg void OnShadersPBinaryWrite();
};

#ifndef _DEBUG  // Versión de depuración en EntornVGIView.cpp
inline CEntornVGIDoc* CEntornVGIView::GetDocument() const
   { return reinterpret_cast<CEntornVGIDoc*>(m_pDocument); }
#endif

