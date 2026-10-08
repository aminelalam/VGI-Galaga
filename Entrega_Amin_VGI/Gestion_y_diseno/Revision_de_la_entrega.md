# Revisión de la gestión integral de Galaga 3D

Actualización del 8 de octubre de 2026. Este informe sustituye la revisión de los tres libros iniciales.

## Entrega vigente

01_Gestion_integral_Galaga3D.xlsx sustituye los antiguos libros de requisitos y planificación. Ocho hojas reúnen tareas, requisitos, pruebas, calendario, equipo, acuerdos y guía. 03_Diseno_detallado_Amin.xlsx conserva la configuración técnica. Los dos libros sustituidos se conservan como antecedentes fuera de la entrega activa, en tmp/office/antecedentes.

## Criterios y trazabilidad

- 52 ids de requisito conservados, 60 casos de prueba, 40 tareas. Sin ids duplicados, tareas ausentes, pruebas huérfanas o ciclos en las dependencias iniciales.
- Cada requisito tiene tarea y al menos una prueba con preparación, pasos y resultado esperado. La relación requisito → tarea coincide con el registro técnico de las tareas.
- 16 criterios afinados: RQ-002, 003, 007, 008, 010, 012, 025, 032, 035, 036, 039, 043, 046, 047, 048 y 049. Tolerancias, mediciones, muestras y evidencias concretadas; cambios registrados como propuestas en Acuerdos.
- Tres requisitos proceden directamente del alcance/tecnología expresos del acta y figuran Incluido: RQ-001, 031 y 050. La aceptación de sus entregas sigue pendiente. Los demás criterios siguen Propuesto hasta acuerdo del grupo.
- La duración de 5–8 minutos se contrasta con seis partidas; 30 FPS es el presupuesto mínimo de rendimiento propuesto y 60 FPS el objetivo adicional. Confirmar ambos criterios con el anexo y la rúbrica.

## Cálculos y funcionamiento comprobados

- 5,071 fórmulas en el libro integral, comparadas tras recálculo independiente con LibreOffice Calc: cero diferencias y cero errores. 14 hojas entre los dos libros activos.
- Estado inicial: 38 tareas P0/P1 y 209 h; activar P2 añade dos tareas y 11 h. 50 requisitos activos, 47 por acordar y cero aceptados.
- Prueba aprobada sin evidencia: no válida. Tarea Hecha sin evidencia/revisión: no aceptada. Cierre completo de un requisito con tarea y pruebas revisadas: aceptado; retirar evidencia de tarea impide esa aceptación.
- Capacidad cero sin división por cero; inicio confirmado desplaza fechas; id duplicado y criterio vacío generan incidencias. Datos temporales de comprobación retirados.
- Carga de las seis personas comparada con un cálculo independiente para cada una de las 13 semanas. Máximo inicial: 7,75 h/persona/semana bajo la hipótesis de capacidad de 8 h.
- Incorporación temporal de una tarea adicional: actualiza resumen y calendario. El archivo contiene tablas, autofiltros y fórmulas nativas de columnas calculadas. Se ha comprobado el formato del archivo y su recálculo; no se ha realizado una sesión interactiva en Microsoft Excel de escritorio.
- Tablas ampliables; validaciones preparadas hasta fila 2000. Calendario automático para las primeras 200 tareas y ventana de 16 semanas. Las referencias de tabla evitan rangos de resumen fijos.

## Documentación

- Word y PDF actualizados: 33 páginas y nueve figuras, con sección de gestión, gráfica de carga e índice sincronizados. Dossier de consulta: 29 páginas, con duración y rendimiento revisados. Portada y guías apuntan al Excel vigente.
- Revisadas visualmente las ocho hojas del libro y la maquetación del Word, incluida la sección de gestión. Todas las rutas locales de INICIO.html existen. Acta original conservada byte por byte.
- Archivo XLSX sin macros y sin vínculos de fórmulas con otros libros. No se ha publicado una copia externa.

## Validación pendiente del equipo

1. Confirmar fechas, capacidad y reparto de trabajo. Las 13 semanas son una propuesta nivelada; no una fecha de entrega aprobada ni una optimización garantizada.
2. Acordar alcance y criterios con el enunciado, anexo y rúbrica completos. Acordar el día de los traspasos que comparten semana.
3. Ejecutar los 60 casos en la aplicación C++/MFC/OpenGL/GLM del curso. En esta carpeta no está el repositorio del juego; las comprobaciones anteriores certifican las herramientas de gestión y documentación, no su implementación.
4. Registrar cada cambio en Acuerdos, actualizar criterios/configuración y repetir pruebas afectadas. Conservar evidencia por build y una única copia compartida del libro integral.
