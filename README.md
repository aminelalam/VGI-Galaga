# Galaga 3D anterior con nuestras naves

Adaptación del Galaga3D anterior de [Releases](https://github.com/aminelalam/VGI-Galaga/releases/tag/comparativa-2026-11-12), basado en el commit cc3ced65878d21a25af445dcc3eb670e831aa792. Reutiliza las mallas exactas de Flecha, Delta y Doble Motor del juego 2D, con sus siluetas y colores originales y una escala uniforme para encajarlas en la escena 3D.

## Descargar y jugar

Descarga el [paquete Windows](https://github.com/aminelalam/VGI-Galaga/raw/refs/heads/codex/galaga3d-anterior-naves/Version_anterior_naves/Galaga3D-Anterior-Naves-Windows.zip), extrae toda la carpeta y abre INICIAR.cmd o Galaga3D.exe. No hace falta instalar Visual Studio para jugar.

En la copia de código, INICIAR.cmd abre el juego después de ejecutar build-demo.cmd. El paquete se prepara en dist/Galaga3D-Anterior-Naves.

## Las naves del 2D en el 3D

Se han sustituido los tres OBJ/MTL de las naves por los sólidos que ya se usaban para renderizar los sprites 2D. Se conserva su geometría, el centrado, los colores y la orientación: proa hacia +Y y grosor en Z. La escala es 0,75 para mantener un tamaño compatible con el corredor y las colisiones del juego anterior.

| Nave | Geometría | Rasgos conservados |
| --- | --- | --- |
| Flecha | 92 triángulos, 6 piezas | Cuerpo azul y alas blancas |
| Delta | 94 triángulos, 7 piezas | Silueta triangular roja |
| Doble Motor | 114 triángulos, 7 piezas | Cuerpo verde y dos barquillas |

La fuente editable está en Recursos_Galaga3D/blender/Naves_2D_fuente.blend. El script Recursos_Galaga3D/scripts/exportar_naves_2d.py permite regenerar los OBJ/MTL desde ese archivo. El manifiesto Recursos_Galaga3D/modelos/procedencia_naves_2d.json registra hashes, dimensiones y comprobaciones de geometría. Se verifican las piezas cerradas, las normales exteriores y la coincidencia con los vértices de la fuente.

El render mantiene VAO/VBO/EBO, materiales, iluminación, perspectiva y profundidad de la versión anterior. Las naves se cargan una vez y se reutilizan mediante sus matrices de modelo.

## Qué conserva el juego anterior

Movimiento directo en X y Z, tres combates, dos tramos de esquiva con cámara de cabina y un jefe final. Hay armas simple, doble, triple y misil, vidas, protección temporal, puntuación y audio. Las tres naves comparten reglas. Los enemigos, el escenario y las reglas de campaña proceden de la versión anterior.

| Acción | Tecla |
| --- | --- |
| Elegir nave y empezar | 1/2/3 y Enter |
| Moverse y subir o bajar | WASD o flechas |
| Disparar | Espacio |
| Cambiar arma | 1/2/3/4 durante la partida |
| Misil especial | Q |
| Pausar o continuar | P |
| Pausar o volver al menú | Esc |
| Activar o silenciar audio | M |
| Ver triángulos de las mallas | F2 |
| Reiniciar tras un resultado | R |

## Capturas y comprobaciones

La galería Capturas/README.md muestra la selección de las tres naves, combate, armas, picados, daño, protección, esquiva, jefe, pausa y resultados. Cada imagen indica si corresponde a una partida recorrida con controles normales o a un estado preparado para inspeccionar un efecto concreto.

El verificador usa el render OpenGL real. También recorre la campaña mediante entradas normales, captura cada etapa y comprueba victoria y derrota sin modificar vidas, enemigos ni resultados. El informe completo acompaña a las capturas.

## Compilar

Windows x64 y Visual Studio 2022 o 2026 con C++ de escritorio, MFC y Windows SDK. Ejecuta build-demo.cmd para compilar, comprobar y preparar el paquete. El script selecciona el toolset instalado y usa la GPU del equipo. La opción -SoftwareRenderer prepara Mesa para equipos sin OpenGL 3.3; la primera descarga necesita conexión.

La solución es Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln. Game3D mantiene la simulación del commit anterior; Mesh3D carga los OBJ/MTL y Renderer3D los dibuja. La adaptación de recursos y la verificación se han preparado con asistencia de Codex.
