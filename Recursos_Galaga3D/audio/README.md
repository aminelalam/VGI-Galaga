# Audio original: nave espacial

Dos ambientes y seis efectos creados para el proyecto mediante síntesis matemática y ruido con semillas fijas. Los ocho archivos mantienen los nombres que carga `GameAudio`: WAV PCM de 16 bits, mono, a 22.050 Hz. No contienen grabaciones, voces ni música de terceros.

Esta revisión sustituye las melodías y los arpegios por maquinaria, ventilación, resonancias y pulsos contenidos. El objetivo es acompañar una nave militar espacial y dejar espacio a los disparos y a las señales de daño.

| Archivo | Duración | Diseño | Pico | RMS |
| --- | ---: | --- | ---: | ---: |
| `menu.wav` | 24,00 s | Ambiente de hangar: motor grave, ventilación y resonancias lentas. Bucle. | −10,40 dBFS | −21,41 dBFS |
| `combat.wav` | 24,00 s | Ambiente de misión: presión del motor y pulsos graves a 75 por minuto, sin melodía principal. Bucle. | −8,87 dBFS | −20,41 dBFS |
| `shot.wav` | 0,24 s | Descarga de energía: ataque breve de ruido, cuerpo de bobina y reflexiones cortas. | −3,88 dBFS | −22,65 dBFS |
| `hit.wav` | 0,38 s | Golpe sobre metal: transitorio de impacto y resonancias que decaen a distintas velocidades. | −4,44 dBFS | −24,52 dBFS |
| `damage.wav` | 0,78 s | Impacto sobre el casco: presión grave, fragmentos y vibración de paneles. | −3,61 dBFS | −19,42 dBFS |
| `victory.wav` | 1,35 s | Confirmación de sistemas: cierre mecánico suave y una resonancia estable que se apaga. | −6,94 dBFS | −22,45 dBFS |
| `defeat.wav` | 1,45 s | Pérdida de energía: bobina que cae de frecuencia y ruido que se extingue. | −5,68 dBFS | −22,48 dBFS |
| `transition.wav` | 0,92 s | Cambio de etapa: válvula de aire y cierre mecánico corto. | −6,74 dBFS | −22,54 dBFS |

Los ocho WAV ocupan **2.342.944 bytes**, aproximadamente 2,23 MiB. `catalogo.json` registra estos niveles, duración, tamaño, desplazamiento de continua, métricas de unión de los bucles y SHA-256.

## Generación y comprobación

Desde la raíz del repositorio:

```powershell
python Recursos_Galaga3D/scripts/generar_audio.py
python Recursos_Galaga3D/scripts/generar_audio.py --check
```

La primera orden regenera los ocho WAV y su catálogo. La segunda vuelve a sintetizarlos en memoria y comprueba que cada byte coincide con los archivos guardados, sin modificarlos. Solo se utiliza la biblioteca estándar de Python.

Los sonidos combinan osciladores sinusoidales, ruido filtrado, envolventes de ataque y caída, resonancias no armónicas y pequeñas reflexiones. La normalización limita tanto el pico como la energía RMS. Los efectos empiezan y terminan en cero, con un inicio muy breve para conservar el impacto y una salida suave para evitar cortes bruscos.

Los ambientes no se funden a silencio al repetirse. Sus osciladores y modulaciones completan ciclos enteros en 24 segundos; el estado inicial de los filtros de ruido se calcula para que continúen al volver al principio. Se comprueba que el salto entre el último y el primer sample, y su cambio de pendiente, están dentro de los cambios normales del propio sonido. También se comparan los niveles de los últimos y primeros 100 ms para detectar un corte o cambio de volumen en la unión.

## Mezcla y validación

Se conserva el mezclador WinMM y su interfaz. La música usa ganancia 0,30 y los efectos 0,65, con hasta ocho efectos simultáneos. El cambio de ambiente tiene una rampa de 80 ms. El limitador suave `tanh` evita superar los límites PCM al coincidir sonidos. La aplicación puede continuar si faltan archivos o no hay dispositivo de audio.

La comprobación numérica verifica el formato WAV, las muestras finitas, la ausencia de saturación, un desplazamiento de continua menor que 0,00001 de la escala completa y la continuidad de los bucles. Además, reproduce fuera del juego las ganancias y la fórmula del mezclador en una secuencia de ocho segundos con disparos repetidos, impactos, daño y transición. Esa secuencia mide **−4,56 dBFS de pico y −23,68 dBFS RMS**, sin muestras recortadas. Una prueba de ocho efectos de daño coincidentes queda en **−0,78 dBFS de pico**, también sin recorte PCM.

Estas comprobaciones no equivalen a una escucha humana ni a una medición LUFS. No se ha realizado una escucha subjetiva con altavoces o auriculares en esta revisión; queda por valorar en una partida el equilibrio percibido entre ambiente y efectos, especialmente en los altavoces del equipo final. El script no compila ni ejecuta la aplicación.

El diseño, la síntesis y la documentación se han realizado con asistencia de Codex.
