# Gestión de Galaga 3D para el equipo

## Empezar

Abre **01_Gestion_integral_Galaga3D.xlsx** y lee Inicio y Guia. Es el archivo vigente de requisitos, tareas, pruebas y acuerdos. Mantener una única copia compartida del equipo.

## Hojas y rutina

| Hoja | Uso |
| --- | --- |
| Inicio | Fechas, semana de consulta, activación de P2, avance, alertas y gráfico de carga. |
| Tareas | Responsable, apoyo, horas, semana, dependencia principal, entregable y evidencia. Cada persona actualiza su Estado. |
| Requisitos | Alcance, criterio específico, tarea vinculada y aceptación final. Estado calculado desde tarea y pruebas. |
| Pruebas | Preparación, pasos, resultado esperado, resultado real, evidencia, build y fecha. |
| Calendario | Vista automática de las primeras 200 tareas; ventana móvil de 16 semanas. |
| Equipo | Coordinación, capacidad editable, carga pendiente y sobrecarga de la semana seleccionada. |
| Acuerdos | Decisiones, riesgos y 16 revisiones de criterios pendientes de acuerdo. |
| Guia | Instrucciones de cierre, ampliación de tablas, trabajo compartido y cambios. |

En cada reunión: actualizar fecha y semana; filtrar Tareas por Responsable; actualizar estado; revisar bloqueos y carga; registrar pruebas y acuerdos.

## Qué se puede editar

Ámbar identifica entradas. Azul claro identifica cálculos que se deben conservar. Las tablas admiten filtros y ordenación: conservar los ids. Para cerrar una tarea, completar Hecha, Evidencia, Revisa y Fecha. Para aceptar un requisito, acordar alcance Incluido, revisar tarea aceptada y todas las pruebas válidas, y registrar Aceptacion, Revisa y Fecha.

Para añadir registros, usar la siguiente fila de la tabla o Tab en su última celda. Comprobar que la tabla se amplía y conserva las columnas azules calculadas. Hay una fila inicial preparada al final de Tareas. Las validaciones de entrada cubren hasta la fila 2000; más allá habría que ampliarlas. Los resúmenes usan las tablas completas. El visor Calendario muestra las primeras 200 tareas.

## Alcance y capacidad

52 requisitos, 60 casos y 40 tareas. P0/P1: 38 tareas y 209 horas previstas. P2: dos tareas y 11 horas adicionales, fuera por defecto.

La propuesta nivelada ocupa **13 semanas** con **8 h por persona y semana**, una hipótesis por confirmar. El reparto usa Responsable + Apoyo % de cada tarea; cambiarlo actualiza la carga. No se deduce disponibilidad individual a partir de los porcentajes de coordinación del acta. Las dependencias que comparten semana necesitan día de traspaso acordado. El libro detecta incidencias; la replanificación la hace el equipo. Fechas de inicio y entrega permanecen sin confirmar.

## Criterios revisados

Se han conservado los 52 ids y afinado 16 criterios. Cada requisito tiene tarea y casos de prueba. RQ-002 mide seis partidas y documenta el balance hacia 5–8 minutos. RQ-047 propone p95 ≤33,3 ms en el equipo de entrega y 16,7 ms como objetivo adicional; debe contrastarse con la rúbrica. Las velocidades, vidas y temporizadores son configuración de referencia propuesta, revisable con versión y evidencia.

El acta confirma el referente, roles, alcance inicial y tecnología. Las propuestas restantes se acuerdan en el equipo. Faltan el anexo y la rúbrica completos para validar el alcance final. No hay aplicación C++ en esta carpeta para certificar sus pruebas.

## Diseño y recursos

**Diseno_tecnico_Galaga3D_Amin.docx** explica la transformación 2D a 3D, estados, reglas, contratos y fuentes. **03_Diseno_detallado_Amin.xlsx** conserva los 40 parámetros y la especificación técnica. El registro de acuerdos vigente está en el libro integral; trasladar los cambios de parámetros al juego y repetir pruebas.

Diagramas en figuras/. Vídeo, captura y acta en ../recursos/. Atribuciones en ../CREDITOS.md. Sin macros ni enlaces de fórmulas entre archivos. No se ha publicado ninguna copia en servicios externos.
