# Audio original

Dos bucles de música y seis efectos creados para Galaga 3D mediante síntesis matemática. Los archivos son WAV PCM de 16 bits, mono, a 22.050 Hz. `catalogo.json` registra duración, pico, RMS y SHA256.

`menu.wav` es una secuencia ambiente de 20 segundos. `combat.wav` introduce un pulso más rápido y dura aproximadamente 14,55 segundos. Los efectos cubren disparo, impacto, daño al jugador, victoria, derrota y transición de fase.

Para reconstruirlos desde la raíz del repositorio, ejecuta `python Recursos_Galaga3D/scripts/generar_audio.py`. La generación es determinista. El script comprueba el formato, los extremos de cada onda y el margen frente a saturación.

`GameAudio` mezcla la música y hasta ocho efectos mediante un único dispositivo WinMM. El volumen de música es moderado y los impactos simultáneos pasan por un limitador suave. La aplicación puede continuar si faltan archivos de sonido o si el dispositivo de audio no está disponible.

Este material se ha creado con asistencia de Codex y usa composiciones y efectos generados para el proyecto.
