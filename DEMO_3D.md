# Galaga 3D — demo de una ronda

Abre **`dist/Galaga3D/Galaga3D.exe`**. Conserva la carpeta completa junto al ejecutable: contiene el motor OpenGL y los shaders.

La demo utiliza modelos sólidos, cámara en perspectiva, iluminación y profundidad real. Tu nave se mueve **solo de izquierda a derecha**, con Y y Z fijos. Los enemigos entran, atacan y regresan por trayectorias XYZ continuas. No hay cambio entre planos.

## Controles

| Acción | Tecla |
| --- | --- |
| Elegir Flecha, Delta o Doble Motor | 1, 2, 3 |
| Empezar | Enter |
| Mover horizontalmente | A/D o flechas |
| Disparar | Espacio, se puede mantener |
| Pausar / continuar | P |
| Pausar o volver a elegir nave desde pausa/resultados | Esc |
| Repetir después de victoria o derrota | R |

Una ronda con 18 enemigos, tres vidas, disparos con cadencia, entrada en formación, picados y retorno. Las tres naves comparten reglas. Ganas al eliminar la formación; pierdes al agotar las vidas. Cambiar de ventana pausa la partida.

Las bajas consecutivas dan ×2 desde la tercera y ×3 desde la sexta. Un disparo fallado o recibir daño rompe la racha. El récord se guarda al cerrar normalmente la aplicación.

## Compilar

Requiere Windows x64 y Visual Studio 2022 con **Desarrollo para el escritorio con C++**, **MFC v143** y Windows SDK.

Ejecuta `build-demo.cmd` desde la raíz. Descarga el motor Mesa verificado por SHA256 si falta, compila Release, ejecuta las pruebas, verifica el render y prepara `dist/Galaga3D`. La descarga inicial requiere conexión; la carpeta distribuida funciona sin conexión. El script no modifica la política de PowerShell del sistema.

También puedes abrir `Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln` y elegir **Release | x64**. Ejecuta previamente `scripts/setup-mesa.ps1 -Deploy` mediante PowerShell con la política limitada al proceso, tal como hace `build-demo.cmd`.

```bat
build-demo.cmd -Configuration Debug -Verify
build-demo.cmd -Configuration Release -Verify -Package
```

El ejecutable compilado queda en `Entrega_Amin_VGI/entornsGrafics/bin/x64/<configuración>/Galaga3D.exe`.

## Controlador gráfico

En este equipo, el proveedor del sistema devolvía **GDI Generic / OpenGL 1.1**. Se incluye **Mesa LLVMpipe 26.2.5** como `opengl32.dll` local. Ejecuta OpenGL moderno y shaders en CPU sin instalar ni actualizar controladores. Se ha verificado un contexto **OpenGL 4.6 Core Profile**; la demo necesita 3.3.

No copies únicamente el EXE ni retires esa DLL. Origen, hashes y licencias: `Entrega_Amin_VGI/entornsGrafics/third_party/mesa/`. Los mensajes técnicos de arranque quedan en `startup.log` y `context.log` junto al ejecutable.

## Código y decisiones

| Archivo, bajo EntornVGI | Responsabilidad |
| --- | --- |
| `Game3D.h/.cpp` | Simulación a 60 Hz, entrada lateral, estados, colisiones por barrido de esferas XYZ, puntuación |
| `GameView3D.cpp` | Teclas MFC, pausa al perder foco, reloj y reinicios |
| `Mesh3D.h/.cpp` | Modelos originales triangulados, normales por cara, colores y VAO/VBO |
| `Renderer3D.h/.cpp` | Cámara, luz, instancias y matrices |
| `shaders/galaga3d.vert` | Transformación `projection * view * model * position` |
| `shaders/galaga3d.frag` | Ambiente, Lambert y especular |
| `Renderer2D.h/.cpp` | Únicamente HUD: atlas pixel original y paneles, sin naves ni enemigos |
| `DemoVerification.cpp` | Verificación del pipeline real en FBO con profundidad y capturas |

`ModelLibrary::initialize()` realiza nueve cargas estáticas de geometría: tres naves, tres insectos, dos proyectiles y una partícula. El tercer insecto es un modelo reservado para ampliar el juego; no añade un jefe a esta ronda. Son 1.524 triángulos en total.

Cada malla tiene un VAO y un VBO intercalado con atributos **0 posición, 1 normal, 2 UV, 3 color**. Se sube una sola vez con `GL_STATIC_DRAW`. Durante el dibujo, `Renderer3D::instance()` envía `model` mediante `glUniformMatrix4fv(..., GL_FALSE, glm::value_ptr(model))`, envía la matriz normal inversa transpuesta y reutiliza el VAO. El HUD actualiza su propio VBO dinámico por pasada. Los buffers se liberan con el contexto todavía activo.

Se conserva la base MFC/OpenGL de la asignatura. El menú **Juego** permite volver al entorno docente, que requiere OpenGL 4.6; la demo usa sus propios shaders 330.

## Documentación aplicada

Se revisaron las dos actas, el diseño técnico, los ocho PDF docentes (640 páginas), las siete fotos nuevas y los recursos/modelos del repositorio.

- **Acta nueva, reunión 3**: carga de modelos una vez, VAO/VBO y matriz model por instancia. Archivo `docuemntacion/acta-ABP-continuacio (1).pdf`.
- **GL-3, pp. 47, 68, 70 y 138–139**: ciclo de carga/dibujo/liberación y atributos.
- **GL-4, pp. 13–14 y 57–59**: orden T·R·S, matrices GLM y uniforms.
- **VGI-6, pp. 9–30 y 48–65**: iluminación y normales.
- **Fotos**: Flecha, Delta y Doble Motor, menú negro, títulos amarillos y estilo arcade. La referencia Galaga aporta las alas de insecto, ojos, colores y formación.
- `prototips.blend` contiene prototipos voxel de Space Invaders, no las naves de las fotos. Las mallas de esta demo se han construido expresamente en C++.

La decisión más reciente del usuario elimina los planos A/B del diseño anterior. La demo mantiene una sola ronda; las tres oleadas, jefe, audio y propuestas de primera persona del proyecto completo quedan fuera de esta entrega.

## Validación reproducible

`build-demo.cmd` ejecuta las pruebas de lógica y `Galaga3D.exe /verify-render`:

- **50 pruebas de lógica**: controles laterales, trayectorias continuas en Z, colisiones XYZ, protección, cadencia, selección, combos, pausa y reinicios.
- Un piloto que solo utiliza controles normales completa la ronda con 18 bajas; un jugador inmóvil pierde las tres vidas naturalmente.
- Inspección de buffers reales: tamaño, uso estático, VAO y atributos, programa enlazado y uniforms activos.
- Diez capturas de menú, selección, combate, formato 4:3, picado, pausa, resultados preparados y modelos girados.
- Comprobación de píxeles de profundidad, HUD visible y geometría sin volver a cargarse durante 60 fotogramas.

Los resultados gráficos quedan en `bin/x64/<configuración>/verification/`. Las pantallas de victoria/derrota etiquetadas `fixture` son estados preparados para comprobar su presentación; las victorias y derrotas completas se comprueban aparte mediante la simulación.

El render se ha verificado automáticamente con el contexto real; no se ha realizado una sesión manual de juego.
