# Galaga 3D · VGI

Juego nativo en C++/MFC/OpenGL, integrado en la estructura de EntornVGI. La campaña encadena **tres combates, dos tramos de esquiva desde la cabina y un jefe final**. Puedes elegir entre tres naves y moverte a izquierda, derecha, arriba y abajo. Los enemigos entran en formación a diferentes distancias y alturas, disparan y realizan picados en el espacio 3D.

Las naves, enemigos y escenario son [mallas OBJ/MTL cargadas por el juego](Recursos_Galaga3D/modelos/README.md), con vértices, triángulos y normales. Se pueden editar en [Mallas_Galaga3D.blend](Recursos_Galaga3D/blender/Mallas_Galaga3D.blend). La perspectiva, las ocultaciones y la iluminación muestran su volumen; **F2** permite inspeccionar los triángulos durante el juego.

Esta implementación está en la rama **`codex/mallas-3d-escenario`**. Ejecuta **`build-demo.cmd`** desde su copia local para compilar, lanzar las comprobaciones y preparar **`dist/Galaga3D/Galaga3D.exe`**. Conserva toda la carpeta `dist/Galaga3D` al distribuir el juego. Incluye Mesa local para ejecutar OpenGL cuando el controlador del equipo no ofrece la versión necesaria.

**Controles:** en el menú, 1/2/3 eligen nave y Enter empieza. En partida, WASD o flechas mueven en horizontal y altura; Espacio dispara; 1/2/3/4 eligen disparo simple, doble paralelo, triple o misil; Q lanza el misil especial con recarga. P pausa, M activa o silencia el audio y F2 alterna la vista de malla. R reinicia tras el resultado; Esc pausa o regresa al menú desde pausa o resultados.

La cámara sigue a la nave desde detrás durante los combates y pasa a la cabina en las esquivas. El avance se representa en un sistema de coordenadas relativo al vuelo: controlas **X** y **Z**, mientras las trayectorias y el desplazamiento del entorno expresan el avance en **Y**. El HUD discreto informa de puntos, etapa, vidas, arma y recarga, con una barra de salud para el jefe. La música y los efectos son [audio original generado matemáticamente](Recursos_Galaga3D/audio/README.md).

[Instrucciones, arquitectura y verificación](DEMO_3D.md) · [Solución Visual Studio 2022](Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln)

La revisión de diseño del 12 de noviembre corrige los combos del disparo doble/triple y las posiciones que permitían superar la esquiva sin moverse. Añade avisos de daño y protección, segundos de recarga y pulsos de preparación de ataque sobre los enemigos. Release pasa 77 comprobaciones de reglas y la verificación gráfica; los hallazgos, pruebas y límites están en [REVISION_JUEGO.txt](REVISION_JUEGO.txt).

![Combate en tercera persona, captura del ejecutable](Recursos_Galaga3D/previews/Mallas/Partida.png)

[Vista desde la cabina](Recursos_Galaga3D/previews/Mallas/Cabina.png) · [Modelos sólidos](Recursos_Galaga3D/previews/Mallas/Modelos.png) · [Triángulos de las mallas](Recursos_Galaga3D/previews/Mallas/Mallas.png) · [Informe gráfico Release](Recursos_Galaga3D/previews/Mallas/Verificacion_Release.txt)

[Aviso de picado](Recursos_Galaga3D/previews/Mallas/Aviso_picado.png) · [Daño en cabina](Recursos_Galaga3D/previews/Mallas/Dano_cabina.png) · [Paso entre asteroides](Recursos_Galaga3D/previews/Mallas/Paso_asteroides.png)

[Guía del código en PDF](docs/Guia_completa_codigo_Galaga3D.pdf). Documenta la revisión del 1 de noviembre de 2026; sus listados y alcance son anteriores a esta campaña. [Revisión técnica y relación con VGI](REVISION_JUEGO.txt). Las instrucciones de la implementación actual están en [DEMO_3D.md](DEMO_3D.md).

Los modelos se cargan una vez en VBO/EBO/VAO. Los enemigos lejanos usan una variante de menor detalle y al acercarse recuperan la malla completa. Cada instancia envía su matriz `model` y la matriz normal al shader; `view` y `projection` definen la cámara. El atributo 4 transporta los parámetros de superficie derivados de `Ks` y `Ns` del MTL. La iluminación Phong sigue los términos de luz y material de GL-6. Los detalles y su relación con GL-3 y GL-4 se explican en [DEMO_3D.md](DEMO_3D.md).

Los PDF, actas y hojas de cálculo originales se conservan como documentación de referencia. Algunos describen propuestas anteriores, incluidos los planos A/B. La campaña actual usa movimiento continuo en horizontal y altura. El MVP privado aparte queda fuera de esta entrega y de su publicación.

## 📊 Un Excel para mantener el proyecto

El libro integral conecta **52 requisitos, 60 casos de prueba y 40 tareas**.

| Hoja | Para qué sirve |
| --- | --- |
| 🏠 Inicio | Fechas, semana de consulta, avance, alertas y gráfico de carga. |
| ✅ Tareas | Responsables, apoyos, horas, dependencias, entregables y evidencias. |
| 🎯 Requisitos | Alcance, criterios verificables y aceptación de cada entrega. |
| 🧪 Pruebas | Preparación, pasos, resultado esperado, build y evidencia. |
| 🗓️ Calendario | Vista automática de tareas por semana. |
| 👥 Equipo | Disponibilidad, carga pendiente y sobrecargas. |
| 💬 Acuerdos | Decisiones, riesgos y cambios de criterio. |
| 📖 Guia | Instrucciones de uso y mantenimiento. |

**Rutina de cada reunión:** actualizar fecha y semana → revisar las tareas de cada persona → resolver bloqueos y carga → registrar pruebas y acuerdos.

- 🟨 **Ámbar:** entradas editables.
- 🟦 **Azul claro:** cálculos que se deben conservar.
- 📎 Una tarea `Hecha` necesita **evidencia, revisor y fecha** para contar como aceptada.
- 🧪 Un requisito necesita tarea aceptada, pruebas válidas y aceptación registrada.
- 🔢 Conservar los ids al ordenar o filtrar. Añadir registros dentro de las tablas.
- 🤝 Mantener **una única copia compartida** del Excel.

La planificación propone **209 horas P0/P1 en 13 semanas**, con **8 h por persona y semana** por confirmar. Activar P2 añade 11 horas. Las fechas reales, disponibilidad y alcance se acuerdan con el equipo y el enunciado del curso.

📖 [Guía completa de uso](Entrega_Amin_VGI/Gestion_y_diseno/LEEME.md) · 🔍 [Informe de revisión](Entrega_Amin_VGI/Gestion_y_diseno/Revision_de_la_entrega.md)

## 👥 Equipo y coordinación

| Persona | Área que coordina |
| --- | --- |
| Pablo | 🔎 Estado del arte |
| Amin | 🧠 Diseño de aplicación |
| Ferran | 🖥️ Interfaz |
| Iker | 🛠️ Implementación |
| Uri / Oriol | 🧪 Pruebas |
| David | 📝 Memoria y presentación |

La aportación principal de Amin consiste en concretar **reglas, estados, entidades, rutas, oleadas, colisiones y profundidad**, y preparar sus criterios de verificación. El acta recoge también su apoyo a las otras áreas.

## 🖥️ Abrir los materiales en tu ordenador

1. En GitHub, pulsa **Code → Download ZIP**, o clona el repositorio:

   ```bash
   git clone https://github.com/aminelalam/VGI-Galaga.git
   ```

2. Extrae la carpeta completa si descargaste el ZIP.
3. Abre `Entrega_Amin_VGI/INICIO.html` en tu navegador.
4. Abre los PDF para leer y los archivos Word/Excel para editar.

La portada, diagramas, maqueta y tráiler descargado funcionan localmente. Los enlaces a fuentes externas requieren internet. El HTML se debe abrir desde la copia descargada; en GitHub se muestra su código.

## 📁 Organización

Los modelos editables de Blender, OBJ/MTL, audio, sprites PNG/SVG y atlas están en [Recursos_Galaga3D](Recursos_Galaga3D/README.md). Los materiales gráficos de propuestas anteriores se conservan junto a los recursos del juego. La implementación C++ de la campaña está en `Entrega_Amin_VGI/entornsGrafics/EntornVGI`.

```text
Entrega_Amin_VGI/
├── Resumen_Amin_VGI.pdf              # Tu parte en una página
├── INICIO.html                      # Portada, maqueta y recursos
├── Dossier_Amin_Galaga3D.pdf          # Dossier de consulta
├── Dossier_editable.md               # Versión de texto editable
├── Guion_reunion.md
├── Tareas_para_el_grupo.md
├── CREDITOS.md
├── Gestion_y_diseno/
│   ├── 01_Gestion_integral_Galaga3D.xlsx
│   ├── 03_Diseno_detallado_Amin.xlsx
│   ├── Diseno_tecnico_Galaga3D_Amin.docx
│   ├── Diseno_tecnico_Galaga3D_Amin.pdf
│   ├── LEEME.md
│   ├── Revision_de_la_entrega.md
│   └── figuras/
└── recursos/                        # Acta, imágenes, diagramas y vídeo
```

## 🧭 Alcance y comprobación

La implementación incluye la secuencia de campaña, cuatro armas, misil especial, vuelo en X/Z, combates en tercera persona, esquivas desde cabina y audio. Las mallas y los shaders se integran en la plantilla de VGI. Las skins, las cajas de recompensas y una economía de partida siguen como propuestas de las actas.

`build-demo.cmd` ejecuta las pruebas de lógica y la verificación gráfica antes de preparar el paquete. En la revisión del 11 de noviembre de 2026, Release y Debug pasan 53 comprobaciones de lógica, incluida una campaña completa con entradas normales, y la verificación del pipeline OpenGL. Las capturas se han inspeccionado; la dificultad y la mezcla de sonido quedan pendientes de una sesión manual.

## 🎨 Fuentes y créditos

El referente es **Galaga**, de Bandai Namco. Los valores concretos de balance y las ampliaciones son propuestas de diseño del proyecto. Las imágenes y el tráiler externos conservan sus atribuciones en [CREDITOS.md](Entrega_Amin_VGI/CREDITOS.md). Las fuentes técnicas se recogen en el Word/PDF.

📋 [Acta original del grupo](Entrega_Amin_VGI/recursos/acta_original.pdf)

---

**🚀 Un diseño que podamos explicar, implementar y comprobar juntos.**
