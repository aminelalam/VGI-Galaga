// framework.h: archivo de inclusión para archivos de inclusión estándar del sistema,
//				o archivos de inclusión específicos del proyecto utilizados frecuentemente,
//				pero cambiados rara vez

#pragma once

#ifndef VC_EXTRALEAN
#define VC_EXTRALEAN            // Excluir material rara vez utilizado de encabezados de Windows
#endif

#include "targetver.h"

#define _ATL_CSTRING_EXPLICIT_CONSTRUCTORS      // Algunos constructores CString serán explícitos

// Desactiva la ocultación de MFC para algunos mensajes de advertencia comunes y, muchas veces, omitidos de forma consciente
#define _AFX_ALL_WARNINGS

#include <afxwin.h>         // Componentes principales y estándar de MFC
#include <afxext.h>         // Extensiones de MFC


#include <afxdisp.h>        // Clases de Automation de MFC

#ifndef _AFX_NO_OLE_SUPPORT
#include <afxdtctl.h>           // Compatibilidad MFC para controles comunes de Internet Explorer 4
#endif
#ifndef _AFX_NO_AFXCMN_SUPPORT
#include <afxcmn.h>             // Compatibilidad MFC para controles comunes de Windows
#endif // _AFX_NO_AFXCMN_SUPPORT

#include <afxcontrolbars.h>     // Compatibilidad de MFC con cintas y barras de control

#ifdef _UNICODE
#if defined _M_IX86
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='x86' publicKeyToken='6595b64144ccf1df' language='*'\"")
#elif defined _M_X64
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='amd64' publicKeyToken='6595b64144ccf1df' language='*'\"")
#else
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")
#endif
#endif

/* ------------------------------------------------------------------------- */
/*                                INCLUDES                                   */
/* ------------------------------------------------------------------------- */

// VGI: Includes llibreria GLEW 2.1.0 (OpenGL)
#define GLEW_STATIC
#define GLEW_NO_GLU	// Sense usar llibreria GLU
#include <gl/glew.h>
#include <gl/wglew.h>

// Include all GLM core / GLSL features
#include <glm/glm.hpp>		// perspective, translate, rotate
// Include all GLM extensions
#include <glm/ext.hpp>
//#include <glm/gtc/matrix_transform.hpp>
//#include <glm/gtc/quaternion.hpp>
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/euler_angles.hpp>
//#include <glm/gtx/norm.hpp>
using namespace glm;

// VGI: Fonts dels Objectes de la llibreria freeglut adaptats a estructures VAO, EBO i VBO
#include "glut_geometry.h"			

// VGI: Llibreria SOIL2 (actualització de SOIL) per a llegir imatges de diferents formats 
//     (BMP,JPG,TIF,GIF,etc.) en la funció loadIMA (visualitzacio.cpp)
#include <gl/SOIL2.h>

// VGI: Includes per lectura fitxers, funcions trigonomètriques i nombres aleatoris.
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <vector>
#include <string>
#include <ctime>

// VGI: Constants de l'aplicació Practica
#include "constants.h"

// Desactivar en llistat compilació diferents tipus de warnings
#  pragma warning (disable:4244)  // Disable bogus VC++ 4.2 conversion de 'GLdouble' a 'GLfloat'; posible pérdida de datos
#  pragma warning (disable:4305)  // VC++ 5.0 version of 4244 warning: 'argumento': truncamiento de 'double' a 'GLfloat'
//#  pragma warning (disable:4473)  // Disable strpcpy deprecated command in objLoader.cpp
//#  pragma warning (disable:4099)  // Warning 'no se encontro vc145.pdb
//#  pragma warning (disable:4996)  // Disable strpcpy deprecated command in objLoader.cpp
