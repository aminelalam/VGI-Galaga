# Galaga 3D · VGI

Demo nativa en C++/MFC/OpenGL: **una ronda, tres naves seleccionables y movimiento exclusivamente lateral**. Los modelos son sólidos; los enemigos siguen trayectorias con profundidad y las colisiones se calculan en XYZ.

Abre **`dist/Galaga3D/Galaga3D.exe`** para jugar o ejecuta **`build-demo.cmd`** para compilar, probar y preparar el paquete. La carpeta distribuida incluye un motor OpenGL local que evita el aviso de actualizar el controlador en este equipo.

**Controles:** 1/2/3 eligen nave; Enter empieza; A/D o flechas mueven; Espacio dispara; P pausa; R reinicia tras el resultado. Esc permite regresar a la selección desde pausa o resultados.

[Instrucciones, arquitectura y verificación](DEMO_3D.md) · [Solución Visual Studio 2022](Entrega_Amin_VGI/entornsGrafics/Galaga3D.sln)

La nueva acta se aplica con mallas cargadas una sola vez en VBO/VAO y una matriz `model` enviada al shader por instancia. El HUD sigue el aspecto arcade negro/amarillo de las fotos y las naves reinterpretan sus tres diseños con colores y siluetas de Galaga.

La documentación de gestión que sigue recoge el diseño completo anterior: tres oleadas, jefe y planos A/B. **La demo actual usa una sola ronda y no permite cambiar de plano**, según la última decisión del usuario. Los PDF, actas y hojas de cálculo originales se conservan como documentación de referencia.

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

La interfaz editable de Blender, los sprites PNG/SVG, los atlas y sus comprobaciones están en [Recursos_Galaga3D](Recursos_Galaga3D/README.md). Conservan la propuesta anterior, incluidos los planos A/B. La demo C++ tiene un HUD arcade propio y modelos sólidos basados en las fotos; su implementación está en `Entrega_Amin_VGI/entornsGrafics/EntornVGI`.

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

## 🧭 Estado de la implementación

- [x] Integrar una ronda completa en la plantilla de VGI.
- [x] Crear tres naves y enemigos con volumen, VAO/VBO y shaders.
- [x] Mantener controles laterales y trayectorias enemigas en 3D.
- [x] Ejecutar pruebas de lógica y de render, con capturas.
- [ ] Ampliar a las tres oleadas y jefe del diseño completo, si se solicita.

## 🎨 Fuentes y créditos

El referente es **Galaga**, de Bandai Namco. Los valores concretos de balance y las ampliaciones son propuestas de diseño del proyecto. Las imágenes y el tráiler externos conservan sus atribuciones en [CREDITOS.md](Entrega_Amin_VGI/CREDITOS.md). Las fuentes técnicas se recogen en el Word/PDF.

📋 [Acta original del grupo](Entrega_Amin_VGI/recursos/acta_original.pdf)

---

**🚀 Un diseño que podamos explicar, implementar y comprobar juntos.**
