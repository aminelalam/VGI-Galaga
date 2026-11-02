# Galaga 3D basico en EntornVGI

Abre **dist/Galaga3D/Galaga3D.exe** y conserva toda la carpeta junto al ejecutable.

## Juego

Una ronda, 18 enemigos y tres vidas. La nave solo se mueve en X; Y y Z permanecen fijos. Los enemigos son mallas solidas inmoviles en tres profundidades reales: Z=-2.5, Z=0 y Z=2.5. La camara en tercera persona se situa detras de la nave y la sigue lateralmente. El fondo es negro liso. Las tres filas tienen seis columnas uniformes, separadas en distancia y altura. La perspectiva, la iluminacion y el depth buffer muestran el volumen. No hay entradas, picados, particulas, parpadeos ni animacion del fondo.

Alinea tu nave horizontalmente con un enemigo. El disparo selecciona el enemigo mas cercano dentro del margen lateral y apunta a su centro en XYZ al salir. Conserva esa trayectoria durante el vuelo. Cuando ningun enemigo queda dentro del margen, sale hacia delante. Los enemigos disparan de uno en uno hacia tu posicion al emitir el tiro. Las balas aliadas son cian y las hostiles naranja rojizo. Los proyectiles hostiles se retiran tras pasar al jugador.

La camara usa un campo de vision de 38 grados y una formacion con modelos ampliados, con el radio de contacto ajustado a su escala. Durante la partida, el HUD muestra unicamente PUNTOS y la puntuacion en la esquina superior izquierda. La revision funcional y los limites de validacion se recogen en REVISION_JUEGO.txt.

Enter inicia; A/D o flechas mueven; Espacio dispara; P pausa. En el menu, 1/2/3 eligen Flecha, Delta o Doble Motor. R reinicia desde un resultado. Esc pausa o vuelve al menu desde pausa/resultados. Perder el foco pausa la simulacion.

Ganas al eliminar los 18 enemigos y pierdes al agotar tres vidas. El combo interviene en el calculo de puntos y el record se guarda internamente. El HUD utiliza la etiqueta original Recursos_Galaga3D/hud/etiqueta_puntos.png. La seleccion de nave, la pausa y los resultados tienen sus propias pantallas con instrucciones.

## Estructura y contenidos de VGI

Se conserva la solucion **Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln**, el proyecto **EntornVGI/EntornVGI.vcxproj**, las ventanas MFC, los mensajes de teclado y el contexto OpenGL de la plantilla. El menu Juego permite regresar al entorno docente. No es el MVP aparte.

- Game3D.h/.cpp: simulacion a 60 Hz, entrada lateral, formacion estatica, disparos y colisiones por barrido de esferas en XYZ.
- GameView3D.cpp: entrada y ciclo de actualizacion mediante MFC.
- Mesh3D.h/.cpp: mallas trianguladas, normales, colores y VAO/VBO estaticos.
- Renderer3D.h/.cpp: perspectiva, camara GLM y matrices model/view/projection.
- shaders/galaga3d.vert y galaga3d.frag: transformaciones e iluminacion Phong con estructuras Light y Material, segun GL-6.
- Renderer2D.h/.cpp: texturas PNG del HUD y mezcla alfa en pantalla.
- DemoVerification.cpp: comprobacion del render real, buffers, HUD y capturas.

Cada malla se carga una vez con GL_STATIC_DRAW. Cada instancia reutiliza el VAO y envia model y la matriz normal al shader. El HUD usa un buffer dinamico independiente. Las colisiones usan coordenadas del mundo, no posiciones de pantalla: coincidir visualmente a distinta profundidad no basta para impactar.

Corresponde a los bloques de transformaciones y modelado 3D, ocultaciones, iluminacion, texturas y shaders de la Guia Docent VGI aportada. GL-3 explica VBO/VAO y GL-4 explica lookAt, perspectiva y matrices. Se reviso tambien el acta 4 del repositorio; las ampliaciones de skins, cajas y modos no forman parte de esta version basica.

## Compilar y comprobar

Windows x64, Visual Studio 2022, C++ de escritorio, MFC v143 y Windows SDK.

```
build-demo.cmd -Configuration Release -Verify -Package
build-demo.cmd -Configuration Debug -Verify
```

La primera orden prepara dist/Galaga3D. Los ejecutables de desarrollo quedan en Entrega_Amin_VGI/entornsGrafics/bin/x64/Release o Debug. La solucion incluye pruebas de logica y copia los recursos del proyecto automaticamente.

Las pruebas comprueban las tres profundidades, formacion inmovil, limites, pausa, direccion XYZ, impactos, reinicio y partidas completas. Un piloto de prueba gana usando solo movimiento y disparo; un jugador quieto pierde naturalmente. La verificacion grafica comprueba shaders, VAO/VBO, depth buffer, recursos HUD, captura 16:9 y 4:3 y reutilizacion de mallas sin nuevas cargas. Resultados en bin/x64/<configuracion>/verification. No sustituyen una sesion manual del jugador.

Se incluye Mesa LLVMpipe local porque el controlador del sistema proporcionaba OpenGL 1.1. Permite ejecutar shaders sin cambiar el controlador; en este equipo el rasterizado se realiza en CPU. Es necesario conservar opengl32.dll. Origen, hashes y licencias en third_party/mesa.

## Transparencia del uso de IA

La adaptacion de Game3D, Renderer3D, Renderer2D y las pruebas, asi como esta documentacion y el ajuste del script de compilacion, se han realizado con asistencia de Codex. La guia docente aportada restringe expresamente el uso de IA en programacion. Esta implementacion asistida no debe presentarse como codigo escrito de forma independiente ni como cumplimiento de esa restriccion. El equipo debe contrastar su uso con el profesor.

El contraste con VGI - Teoria i Problemes, sus paginas de referencia y seis pruebas de los terminos de iluminacion se recogen en REVISION_JUEGO.txt.

La asistencia permite relacionar rapidamente matrices, buffers y reglas, pero el alumnado debe comprender las transformaciones, la deteccion de impactos, las limitaciones del apuntado automatico y el uso de Mesa antes de explicar o evaluar el resultado.
