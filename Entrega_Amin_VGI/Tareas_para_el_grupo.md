# Tarjetas propuestas para Trello · Galaga 3D

Preparadas como aportación de Amin al seguimiento y a la coordinación. No se han publicado en Trello. Responsables según el acta; todos los criterios siguientes son propuestas pendientes de aprobación. Las estimaciones del acta no se convierten en fechas de entrega.

## DIS-01 · Validar el diseño

Responsable: Amin. Participan: todo el grupo.

- Revisar reglas, estados, prioridades y casos límite del dossier.
- Obtener enunciado completo, anexo y rúbrica.
- Registrar qué decisiones se aprueban y qué parámetros se modifican.

Aceptación: reglas sin contradicciones y registro de acuerdos fechado. Dependencia: ninguna.

## REF-01 · Contrastar referentes

Responsable: Pablo. Apoyo de Amin.

- Revisar las fichas oficiales de Galaga y Galaga ’88.
- Observar el tráiler y discutir legibilidad y adaptación al 3D.
- Diferenciar mecánicas históricas, alcance del acta y decisiones propias.

Aceptación: comparación breve con enlaces y criterio de selección. Dependencia: ninguna.

## TEC-01 · Revisar la plantilla y acordar interfaces

Responsable: Iker. Apoyo de Amin.

- Identificar versión OpenGL, shaders, cargador de modelos y estructura MFC.
- Localizar entrada, actualización y renderizado.
- Acordar InputState, World, WaveDefinition y eventos de daño/puntos.

Aceptación: diagrama adaptado a clases reales y tarea de integración por módulo. Dependencia: DIS-01.

## IMP-01 · Nave y disparo

Responsable: Iker. Apoyo de Amin y Ferran.

- Movimiento lateral con límites, teclas opuestas y pérdida de foco.
- Cadencia y máximo de proyectiles configurables.
- Un enemigo inmóvil con modelo sencillo.

Aceptación: se mueve y dispara sin depender de la tasa de render; controles visibles. Dependencia: TEC-01.

## IMP-02 · Impactos, vidas y puntuación

Responsable: Iker. Apoyo de Amin; pruebas con Uri.

- Contactos con barrido relativo y resolución determinista.
- Consumo único de balas, muerte única y puntos únicos.
- Daño, reaparición e invulnerabilidad.

Aceptación: casos T04-T06 reproducibles y registrados. Dependencia: IMP-01.

## IMP-03 · Ciclo del enemigo

Responsable: Iker. Apoyo de Amin y Pablo.

- Entrada, formación, aviso, picado, retorno y destrucción.
- Slot reservado y objetivo lateral fijado antes del picado.
- Director de ataques con máximo de picados simultáneos.

Aceptación: un enemigo repite el ciclo sin atascarse; morir cancela sus acciones. Dependencia: IMP-02.

## IMP-04 · Partida completa P0

Responsable: Iker. Participa el grupo.

- Tres oleadas con configuración y jefe de dos fases.
- Menú, intro, transición, pausa, victoria, derrota y reinicio.
- Regla de muerte simultánea y limpieza de proyectiles.

Aceptación: ciclo completo desde menú a resultado y nueva partida, con T07-T10. Dependencia: IMP-03.

## UI-01 · Cámara, HUD y modelos

Responsable: Ferran. Apoyo de Amin y Uri.

- Cámara fija que mantiene visible el campo.
- Vidas, puntos, oleada, vida del jefe, estado y ayuda de controles.
- Siluetas distintas y materiales compatibles con la plantilla.

Aceptación: legibilidad en 1280×720 y 1024×768; la información no depende solo de color. Puede avanzar en paralelo a IMP-01 tras TEC-01.

## PROF-01 · Dos planos P1

Coordinación del diseño: Amin. Implementación: Iker. Interfaz: Ferran.

- Filtro de plano y persistencia del plano de cada bala.
- Transición, recarga y compatibilidad con invulnerabilidad.
- Marcas A/círculo y B/rombo, indicador y aviso del jefe.

Aceptación: T11-T18, 4/5 escenas identificadas en la prueba de comprensión y base P0 estable. Dependencias: IMP-04 y UI-01.

## QA-01 · Pruebas y balance

Responsable: Uri. Apoyo de Amin e Iker.

- Ejecutar los casos preparados sobre la aplicación C++ real.
- Registrar equipo, resolución, frame time y errores de estado.
- Medir partidas y ajustar el objetivo de 5-8 minutos.

Aceptación: resultados reproducibles, fallos resueltos o limitaciones documentadas. Pruebas continuas desde IMP-01; cierre después de P1.

## DOC-01 · Memoria y demostración

Responsable: David. Apoyo de Amin y todo el grupo.

- Integrar diseño aprobado y fuentes con atribución.
- Guardar capturas y vídeo de la aplicación real.
- Documentar reparto, resultados, métricas y decisiones.

Aceptación: memoria coherente con lo implementado y demostración reproducible. La maqueta local debe quedar identificada como material didáctico.

## OPT-01 · Rescate P2

Responsabilidad y dedicación concreta por acordar.

- Usar el apartado 28 como punto de partida para aliada y portador.
- Revisar coste de doble hitbox, doble disparo y HUD.

Aceptación: criterios del apartado 28; nunca bloquea el cierre de P0 o P1. Dependencia: P0/P1 validados y tiempo disponible.
