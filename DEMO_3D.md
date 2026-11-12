# Galaga 3D en EntornVGI

La campaña se desarrolla en la rama **`codex/mallas-3d-escenario`**. Para preparar la versión de tu copia local, ejecuta **`build-demo.cmd`** desde la raíz del repositorio. El paquete queda en **`dist/Galaga3D`**; abre **`dist/Galaga3D/Galaga3D.exe`** y conserva junto a él sus carpetas de recursos y DLL.

## Cómo se juega

Elige Flecha, Delta o Doble Motor en el menú y pulsa Enter. Empiezas con una nave activa y dos reservas. Cada nave tiene 100 puntos de casco y 60 de escudo; perder todo el casco consume una nave. La secuencia es combate 1 → esquiva 1 → combate 2 → esquiva 2 → combate 3 → jefe final. Los combates reúnen 12, 15 y 18 enemigos; las esquivas duran 12 y 15 segundos. Se gana al destruir el jefe y se pierde al agotar las naves.

En los combates, la cámara empieza detrás de la nave; C permite pasar a la cabina. Los enemigos entran desde distintos puntos, ocupan posiciones a diferentes alturas y distancias, disparan y realizan picados con aviso previo. En las esquivas, la cámara pasa a la cabina y debes evitar los asteroides que se aproximan. En esos tramos no se dispara. Al volver al combate se recupera tu elección de cámara.

| Tecla | Acción |
| --- | --- |
| 1 / 2 / 3 en el menú | Elegir nave. |
| Enter en el menú | Empezar la campaña. |
| A / D o flechas izquierda / derecha | Desplazarse lateralmente. |
| W / S o flechas arriba / abajo | Subir y bajar. |
| Shift + una dirección | Impulso: aumenta la velocidad y consume carga. Mientras está activo no puedes disparar. |
| E | Cambiar prioridad: equilibrada → motores → armas → escudos. |
| C | Alternar cámara trasera y cabina durante los combates. |
| Espacio | Disparar con el arma seleccionada. |
| 1 / 2 / 3 / 4 en partida | Seleccionar simple, doble paralelo, triple o misil. |
| Q | Lanzar un misil especial; recarga de cuatro segundos. |
| P | Pausar o reanudar. |
| Esc | Pausar durante el juego; volver al menú desde pausa o resultados. |
| R en resultados | Reiniciar la campaña. |
| M | Silenciar o activar música y efectos. |
| F2 | Alternar entre caras sólidas y triángulos de la malla. |

Perder el foco de la ventana pausa la simulación. La selección de nave y de arma se conserva al reiniciar. El récord se guarda en el perfil de Windows al cerrar la aplicación y se recupera en la siguiente apertura.

El HUD ocupa los bordes: puntos y objetivo arriba; casco y escudo abajo a la izquierda; arma, calor y misil abajo a la derecha. La energía se elige arriba a la derecha y el impulso se ve en el centro inferior. Los porcentajes de escudo se refieren a sus 60 puntos máximos. «Reservas 2» significa que quedan dos naves adicionales a la actual. Durante las esquivas se ve el tiempo restante y ante el jefe, su salud. No hay mira ni recuadro de objetivo.

Un borde cian confirma daño absorbido por el escudo; el rojo indica daño al casco. Al perder la nave aparece «DESPLEGANDO NAVE DE RESERVA» y después se indican los segundos de protección de despliegue. Esa protección temporal es distinta del escudo regenerable. Q muestra los segundos que faltan para volver a lanzar el misil. La pausa explica los controles de la fase actual.

Los grupos de asteroides cambian su posición horizontal y vertical de una pasada a otra. Cada grupo conserva un hueco amplio y los siguientes huecos se pueden alcanzar a la velocidad de la nave. Mantenerse siempre en el borde ya no permite evitar toda la fase. Los enemigos que van a realizar un picado emiten dos pulsos cálidos sobre su propia malla durante el aviso previo.

## Vuelo, energía y resistencia

El movimiento alcanza gradualmente la velocidad solicitada y frena al soltar las teclas. El tiempo de aceleración normal es aproximadamente 0,20 segundos y el de frenada, 0,16. Se normaliza la diagonal y se detiene la velocidad contra los límites. La inclinación visual de la nave responde a su velocidad real.

E cambia la prioridad sin abrir un menú. Ninguna opción mejora todos los sistemas a la vez:

| Prioridad | Velocidad normal | Enfriamiento láser/s | Escudo recuperado/s | Impulso recuperado/s | Tiempo entre tiros |
| --- | ---: | ---: | ---: | ---: | ---: |
| Equilibrada | 6 | 18 | 8 | 14 | ×1 |
| Motores | 7,5 | 11 | 4 | 24 | ×1,05 |
| Armas | 5,4 | 32 | 4 | 9 | ×0,90 |
| Escudos | 5,7 | 15 | 16 | 10 | ×1,30 |

Las velocidades están en unidades del mundo por segundo. Una cifra menor en la última columna permite disparar antes. El escudo empieza a recuperarse tras cuatro segundos sin impactos. El casco no se regenera: un proyectil enemigo causa 35 puntos, un choque con un enemigo normal 65, un asteroide 70 y el jefe 90. El escudo absorbe primero y el daño sobrante llega al casco. Hay 0,30 segundos de protección tras un contacto válido para evitar varios daños simultáneos.

El impulso multiplica la velocidad por 1,75 y gasta 40 puntos de carga por segundo, de un máximo de 100. Necesita al menos 20 para arrancar y una dirección pulsada. No vuelve invulnerable ni permite disparar. Al soltarlo, la carga se recupera según la prioridad de energía.

Una descarga simple añade 11 de calor; una doble, 15; una triple, 20. El láser se bloquea al llegar a 100 y vuelve a estar disponible al enfriarse a 35. Puedes dosificar ráfagas, priorizar armas o cambiar al misil mientras enfría. El misil no añade calor y tiene su propia cadencia. Al perder una nave se recuperan casco, escudo, impulso y arma fría; cambiar de fase conserva los recursos restantes.

## Espacio 3D, cámara y disparos

El mundo usa **X para izquierda/derecha, Y para avance y Z para altura**. El jugador controla X y Z de manera continua, con la velocidad diagonal normalizada. La Y del jugador permanece fija dentro del sistema relativo al vuelo. El desplazamiento de las estrellas, las entradas y picados de los enemigos y la aproximación de los obstáculos representan el avance. Hay aceleración e impulso dentro de ese plano de control; no hay pilotaje libre en seis ejes ni velocidad longitudinal elegible.

Los objetos tienen geometría tridimensional y posiciones XYZ. La cámara de combate sigue el movimiento lateral y la altura de la nave; la de cabina mira hacia +Y desde el jugador. La proyección en perspectiva hace que los objetos cercanos se vean mayores y el buffer de profundidad resuelve qué superficies ocultan a otras. Las estructuras del escenario quedan alrededor del corredor de combate.

El disparo simple avanza hacia +Y. El doble dispara dos proyectiles paralelos desde posiciones laterales distintas. El triple abre tres trayectorias en abanico. Para acertar con estas armas hay que alinear la nave con la altura y la posición lateral del enemigo.

El misil hace cuatro puntos de daño y tiene una cadencia menor. Al salir puede orientarse hacia un enemigo que esté cerca de la línea de tiro; después conserva su dirección, sin perseguirlo durante el vuelo. Q usa ese mismo tipo de proyectil con una recarga independiente. Los enemigos apuntan hacia la posición del jugador al emitir su disparo.

Tres bajas consecutivas activan puntos dobles y seis activan puntos triples. Recibir daño o fallar una descarga completa rompe la racha. El doble y el triple cuentan como una descarga: si algún proyectil acierta, los restantes pueden pasar de largo sin cancelar el combo. Se espera a que termine la descarga para decidir que ha fallado. Los impactos contra enemigos con armadura también emiten el evento de sonido de impacto aunque no los destruyan.

Las colisiones se calculan con volúmenes esféricos en XYZ y el recorrido entre la posición anterior y la actual. El jefe usa un elipsoide: su anchura, profundidad y altura tienen límites distintos, para que una bala que pase por encima de la nave no cuente como impacto. El contacto se resuelve por el primer instante válido del recorrido. Las mallas visibles no son los volúmenes de colisión: el juego utiliza estas formas simplificadas para mantener el cálculo comprensible y económico. Los destellos, efectos y sonidos comunican impactos y daño.

## Mallas, materiales y contenidos de VGI

Se conserva la solución **`Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln`**, el proyecto **`EntornVGI/EntornVGI.vcxproj`**, las ventanas MFC, los mensajes de teclado y el contexto OpenGL de la plantilla. El menú Juego permite volver al entorno docente, que requiere OpenGL 4.6; el render del juego utiliza shaders GLSL 330. El MVP privado aparte queda fuera de esta versión y de su publicación.

Las naves, enemigos y escenario se editan en [Mallas_Galaga3D.blend](Recursos_Galaga3D/blender/Mallas_Galaga3D.blend). Los archivos OBJ/MTL exportados contienen posiciones, caras triangulares, normales, coordenadas UV y materiales. Los modelos mantienen volumen visto desde diferentes ángulos. Consulta las instrucciones de [edición y exportación](Recursos_Galaga3D/modelos/README.md).

La dirección visual usa cazas industriales con fuselaje, alas, armamento, cabina y motores conectados. Flecha es un interceptor estrecho; Delta tiene alas más anchas; Doble Motor separa sus dos góndolas. Los enemigos se distinguen por su silueta y el jefe es una fragata. El escenario ofrece escala con un planeta, astillero lateral y carguero alejados del corredor. La consola física de cabina permanece oscura: las lecturas activas están en el HUD y proceden de la simulación.

El recorrido de un modelo es: Blender → OBJ/MTL → `MeshVertex` → VBO/EBO → VAO → shader. El VBO almacena una sola copia de cada vértice completo con `GL_STATIC_DRAW`; el EBO conserva los índices de los triángulos y el VAO describe cómo leer ambos buffers. Los vértices con normales, UV o materiales diferentes siguen separados. Cada instancia reutiliza esos datos mediante `glDrawElements` y envía su matriz `model`, que sitúa, orienta y escala el objeto. `view` transforma a coordenadas de cámara y `projection` aplica la perspectiva. El shader obtiene la posición final mediante `projection * view * model * posición`.

Los enemigos normales tienen una segunda malla de menor detalle para distancias de más de diez unidades por delante del jugador. Conserva su silueta, volumen y materiales; al acercarse se usa la malla completa. Ambas versiones se cargan una vez, y cambiar de detalle solo selecciona el VAO. Esta reducción evita procesar miles de triángulos pequeños que apenas ocupan píxeles en la pantalla, especialmente cuando Mesa dibuja con la CPU.

| Atributo del VAO | Datos |
| --- | --- |
| 0 | Posición XYZ. |
| 1 | Normal XYZ de la superficie. |
| 2 | Coordenadas UV. |
| 3 | Color difuso procedente de `Kd`. |
| 4 | Dos parámetros de superficie derivados de `Ks` y `Ns`. |
| 5 | Emisión RGB de la superficie procedente de `Ke`. |

El cargador convierte `Ks` en una intensidad especular media y utiliza `Ns` para ajustar la concentración del brillo. `Ke` mantiene luminosas superficies pequeñas, como los reactores, sin iluminar todo el casco. El cargador incluye estos datos al deduplicar cada vértice. Los colores sólidos y sus brillos distinguen pintura, metal y vidrio; disponer de UV no implica que cada nave use una textura de imagen.

La iluminación Phong se calcula en coordenadas del mundo con las estructuras `Light` y `Material`: emisión, ambiente, difusión y reflexión especular. La matriz normal es la transpuesta de la inversa de la parte 3×3 de `model`, para conservar la orientación correcta de las normales al transformar un objeto. Esto relaciona la implementación con VBO/VAO de **GL-3**, cámara y matrices de **GL-4**, e iluminación de **GL-6**. El buffer de profundidad y el HUD con mezcla alfa corresponden a ocultaciones y composición de la asignatura.

La revisión añade un relleno hemisférico frío y una contribución suave de borde para leer los cascos sobre negro. Es una decisión artística adicional, no una sustitución del modelo Phong docente ni un render físicamente basado. La prueba de los términos GL-6 desactiva ese relleno y comprueba cada término por separado; otra prueba verifica `Ke` con un material sin luz exterior.

Los proyectiles láser son tubos cerrados con un núcleo y un halo aditivo estrecho. El misil tiene cuerpo y aletas. Los escapes se instancian en las toberas de la nave, comparten su matriz y aumentan al impulsar. Conservan prueba de profundidad; el halo transparente no escribe profundidad. Son mallas reutilizadas, no recursos generados durante cada fotograma.

El HUD utiliza un atlas RGBA de Bitstream Vera, textura con mipmaps y mezcla alfa, relacionado con **GL-7**. La licencia está en `Recursos_Galaga3D/fonts`. `generar_fuente_hud.py` genera tanto `hud/instrument_font.png` como las métricas de `RendererFont.h`; se ejecuta con Python y Pillow para regenerarlo. El jugador solo necesita los recursos ya generados.

## Dónde está cada parte del código

Todos los archivos siguientes están en `Entrega_Amin_VGI/entornsGrafics/EntornVGI`, salvo las pruebas de lógica, situadas en `Entrega_Amin_VGI/entornsGrafics/tests`.

| Archivo | Responsabilidad |
| --- | --- |
| `Game3D.h/.cpp` | Reglas a 60 pasos por segundo: campaña, inercia X/Z, energía, calor, escudos, impulso, armas, obstáculos, puntuación y colisiones XYZ. No depende de MFC ni OpenGL. |
| `GameView3D.cpp` | Teclado, reloj, acumulador de pasos de simulación, pausa al perder el foco y eventos de audio. |
| `Mesh3D.h/.cpp` | Lectura de OBJ/MTL, formato intercalado de vértices, VBO/VAO y biblioteca de mallas reutilizadas. |
| `Renderer3D.h/.cpp` | Cámaras de combate y cabina, perspectiva, matrices, dibujo de instancias y modo de malla. |
| `shaders/galaga3d.vert` y `galaga3d.frag` | Transformación de vértices y normales; iluminación Phong y parámetros de material. |
| `Renderer2D.h/.cpp` y `RendererFont.h` | Menú, HUD, pausa, resultados y métricas de texto, superpuestos mediante mezcla alfa. |
| `GameAudio.h/.cpp` | Mezcla de música y efectos WAV con WinMM; el audio es opcional si el dispositivo no está disponible. |
| `Game3DTests.cpp` | Comprobaciones automáticas de reglas y campaña mediante la API de simulación. |
| `DemoVerification.cpp` | Comprobación gráfica con contexto OpenGL real, recursos, buffers y capturas. |

Los recursos son externos al ejecutable y se copian durante la compilación. El [audio original](Recursos_Galaga3D/audio/README.md) incluye música de menú y partida y efectos de disparo, impacto, daño, transición, victoria y derrota. Se genera de forma determinista con `Recursos_Galaga3D/scripts/generar_audio.py` y se mezcla mediante WinMM sin incorporar un motor de audio grande.

La nueva paleta sonora utiliza fondos sostenidos y pulsos, con disparos de energía e impactos metálicos. Un contacto absorbido por el escudo emite impacto; el daño al casco emite el aviso más grave. `python Recursos_Galaga3D/scripts/generar_audio.py --check` comprueba formato, generación reproducible, niveles y continuidad de los bucles. Esta medida no sustituye escuchar una partida.

## Compilar y comprobar

Requisitos: Windows x64, Visual Studio 2022 con desarrollo de escritorio en C++, MFC v143 y Windows SDK.

Desde la raíz del repositorio:

```powershell
.\build-demo.cmd
.\build-demo.cmd -Configuration Release -Verify -Package
.\build-demo.cmd -Configuration Debug -Verify
```

Sin argumentos, el script realiza la misma operación que la segunda orden: compila Release, ejecuta las pruebas de lógica y la verificación gráfica, y prepara `dist/Galaga3D`. La tercera orden prepara una compilación Debug con comprobación gráfica, sin empaquetarla.

Los ejecutables de desarrollo quedan en `Entrega_Amin_VGI/entornsGrafics/bin/x64/Release` o `Debug`. Las pruebas de lógica se ejecutan desde `bin/tests/<configuración>/Game3DTests.exe`. Los informes y capturas de verificación gráfica quedan en `bin/x64/<configuración>/verification`; los mensajes de arranque están junto al ejecutable en `startup.log` y `context.log`.

Verificación del 12 de noviembre de 2026: **Release pasa 108 comprobaciones de lógica y la verificación gráfica**. El piloto completa las tres oleadas, ambas esquivas y el jefe en aproximadamente 119 segundos, con tres naves y mediante entradas normales. Ambas esquivas se prueban también por separado sin invulnerabilidad ni daño al casco o escudo. Un barrido de 12.245 posiciones por fase comprueba que ninguna de las posiciones muestreadas sea segura durante toda la fase. Las nuevas pruebas cubren frenada, diagonal, límites, prioridades de energía, escudo, calor, impulso, cambio de cámara y conservación de recursos. Se mantienen las regresiones de colisiones, combos, daño y pausa.

La comprobación gráfica utiliza la aplicación MFC y OpenGL reales: buffers, seis atributos de vértice, matrices, materiales, profundidad, teclado y estados de interfaz. Captura centro, extremos, 16:9 y 4:3, cabina, jefe, cuatro prioridades, sobrecalentamiento, impulso y daño al escudo. Comprueba que las mallas se suben una vez y se reutilizan. Los resultados Debug del historial pertenecen a versiones anteriores.

La inspección visual se ha realizado sobre capturas del ejecutable, sin superposiciones ni recortes de edición. No se ha realizado una partida manual en esta revisión: la herramienta de automatización de ventanas no pudo inicializarse. Las pruebas y el piloto demuestran los recorridos descritos, no la comprensión de un jugador nuevo ni el balance subjetivo del juego o de su sonido. El detalle de hallazgos y límites está al principio de [REVISION_JUEGO.txt](REVISION_JUEGO.txt).

El [informe conservado](Recursos_Galaga3D/previews/Mallas/Verificacion_Release.txt) identifica el renderizador y los tiempos de esta versión. Mide medias de 60 imágenes de la formación de referencia a 1280×720 y 960×540 con Mesa LLVMpipe, sincronizando la finalización de cada dibujo. No se controla la carga del equipo entre revisiones y no es una garantía de FPS para todos los equipos o fases.

El paquete incluye Mesa LLVMpipe local para equipos cuyo controlador solo expone OpenGL 1.1. En esa configuración el rasterizado se realiza en CPU. Conserva `opengl32.dll` y los recursos del paquete. Su origen, hashes y licencias están en `Entrega_Amin_VGI/entornsGrafics/third_party/mesa`.

## Alcance de la documentación y uso de IA

La referencia de Squadrons se ha estudiado en la [descripción de juego de EA](https://www.ea.com/ea-studios/motive/news/pilot-briefing-gameplay-overview) y la [entrevista oficial a Motive](https://www.starwars.com/news/star-wars-squadrons-interview). Se adaptan la decisión entre subsistemas y la lectura del puesto de pilotaje al corredor de Galaga. No se incorporan sus modelos, música ni imágenes. Los tiempos, daños y prioridades de esta demo son decisiones propias que requieren valoración de jugadores.

Los PDF, actas y documentos de gestión se conservan como referencia. La [guía del código en PDF](docs/Guia_completa_codigo_Galaga3D.pdf) corresponde a la revisión del 1 de noviembre de 2026 y no documenta todos los cambios de esta campaña. Las propuestas de skins, cajas de recompensas y economía de partida no están implementadas aquí. El contraste previo con las páginas de teoría se conserva en `REVISION_JUEGO.txt`.

La adaptación del juego, sus mallas, audio, pruebas y documentación se ha realizado con asistencia de Codex. La guía docente aportada restringe expresamente el uso de IA en programación. Esta implementación asistida no debe presentarse como código escrito de forma independiente ni como cumplimiento de esa restricción. El equipo debe contrastar su uso con el profesor y comprender las transformaciones, buffers, iluminación, reglas y colisiones antes de explicar el resultado.
