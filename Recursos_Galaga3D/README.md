# Interfaz de Galaga 3D

## Blender retro

Dos versiones de los modelos y las pantallas en estilo arcade. Incluyen las naves FLECHA, DELTA y DOBLE MOTOR, enemigos, jefe y HUD. Las piezas son mallas editables, con letras de bloques y materiales de pocos colores.

| Archivo | Uso |
| --- | --- |
| [Galaga3D_Retro_Estatica.blend](blender/Retro/Galaga3D_Retro_Estatica.blend) | Editar las siete pantallas sin animaciones. Se cambia de pantalla desde el selector de escenas de Blender. |
| [Galaga3D_Retro_Animada.blend](blender/Retro/Galaga3D_Retro_Animada.blend) | Ver los modelos y disparos animados. La escena `08_DEMO_COMPLETA` recorre la presentación en 18 segundos. |

Las siete pantallas son inicio, elección de nave, partida, pausa, jefe, victoria y derrota. Para abrir la animada con los botones activos, ejecutar desde la raíz del repositorio:

```powershell
& .\Recursos_Galaga3D\blender\Retro\Abrir_animada.ps1
```

También se puede abrir el `.blend` animado, seleccionar `INICIAR_INTERFAZ.py` en el Editor de texto y pulsar **Alt + P**. Después, colocar el ratón sobre la vista 3D. Los pasos y controles están en [LEEME.txt](blender/Retro/LEEME.txt).

El HUD muestra puntos, récord, oleada, tres vidas, plano y recarga. El jefe tiene su barra de vida y aviso de ataque. La nave elegida se mantiene al cambiar entre partida, jefe y resultados.

Se puede navegar con clics, **1/2/3**, **Enter** y **P**. **Espacio** reproduce o detiene la animación y **Esc** desactiva el controlador. A/D y E aparecen como ayuda del juego, pero no controlan este prototipo. Es una presentación visual: todavía no hay colisiones ni una partida completa.

![Pantallas retro](previews/Retro/Todas_las_pantallas.png)

[Demo animada](previews/Retro/Galaga_Retro_Demo.gif) · [Comprobaciones de los archivos](blender/Retro/comprobaciones.json)

La animación de Blender dura 18 segundos a 30 FPS; el GIF la muestra a 5 FPS. En `scripts/` están el controlador y los scripts para reconstruir los modelos y renderizar las vistas previas. Los fotogramas intermedios y las copias `.blend1` se generan localmente.

## Interfaz original

Recursos visuales originales para la interfaz: puntos, récord, oleada, tres vidas, vida del jefe, planos A/B, recarga y pausa. Estilo futurista con cian y colores vivos. Resolución de referencia: **1280 × 720**.

![Interfaz](previews/interfaz_galaga.png)

## Abrir y editar en Blender

Abrir [blender/Galaga3D_Interfaz.blend](blender/Galaga3D_Interfaz.blend). Archivo creado y probado con **Blender 5.2.2 LTS**. Hay tres escenas:

| Escena | Uso |
|---|---|
| `01_HUD_TRANSPARENTE` | HUD aislado para superponer al juego; fondo transparente. |
| `02_PREVIEW_INTERFAZ` | Presentación con fondo de estrellas. |
| `03_PANTALLA_PAUSA` | Pantalla de pausa con los indicadores de la partida. |

Las formas son mallas vectoriales y los textos siguen editables. Las colecciones separan puntos, jefe, vidas, planos, controles y paneles. Las fuentes Bitstream Vera están empaquetadas y también incluidas en `fonts/`, con su licencia. Las rutas de render y de fuentes son relativas.

Para cambiar los valores de ejemplo, seleccionar `CONTROL_HUD`, editar sus propiedades personalizadas y ejecutar `ACTUALIZAR_HUD.py` en el editor de textos de Blender con **Alt + P**, colocando el cursor en ese editor. El mismo script se incluye en `scripts/actualizar_hud.py`. El archivo no ejecuta scripts automáticamente al abrirse.

| Propiedad | Valores |
|---|---|
| `puntos`, `record` | 0–999999; seis cifras con ceros iniciales. |
| `oleada` | 1–3. |
| `vidas` | 0–3. |
| `vida_jefe` | 0–24. |
| `mostrar_jefe` | Mostrar u ocultar barra y etiquetas del jefe. |
| `plano_B` | Desactivado: A/círculo/cian/CERCA. Activado: B/rombo/ámbar/LEJOS. |
| `recarga_plano` | Tiempo restante de 0 a 1,2 s; 0 muestra LISTO. |
| `invulnerable` | Indicador de invulnerabilidad. |
| `doble_disparo` | Indicador de la ampliación opcional P2. |

Los valores de la presentación son ejemplos. El jugador conserva tres vidas discretas y el jefe 24 HP; los recursos no cambian las reglas del diseño.

## Recursos para OpenGL

En `hud/` hay **16 sprites PNG RGBA transparentes y sus SVG**, un atlas de iconos de **1024 × 512**, un atlas de las diez cifras de **512 × 64** y 14 etiquetas PNG. Los JSON contienen tamaños, rectángulos y UV. Consultar [HUD y barras](hud/README.md) y [cifras y etiquetas](hud/README_texto.md).

Dibujar fondo, relleno y marco de las barras en ese orden. Recortar el relleno según vidas/3 o HP/24, conservando su ancho original. Dibujar el HUD después de la escena 3D con alpha recto (`GL_SRC_ALPHA`, `GL_ONE_MINUS_SRC_ALPHA`). La documentación de los atlas explica las dos convenciones de origen UV.

`previews/hud_transparente.png` es una composición completa de ejemplo con alpha. Los contadores de esa imagen están fijados: para mostrar valores de la partida hay que usar los componentes y cifras, o dibujar textos desde la aplicación. `previews/interfaz_galaga.png` e `interfaz_pausa.png` son presentaciones con fondo. `previews/verificacion_estado.png` muestra la prueba de 2 vidas, jefe 12/24 y plano B.

**La integración en C++/MFC/OpenGL está pendiente.** El `.blend` y sus scripts permiten editar y comprobar el diseño; no implementan la lógica ni los controles del juego.

## Regenerar y verificar

Ejecutar desde la raíz del repositorio. Python requiere Pillow; Blender debe estar disponible como `blender` o sustituirse por su ruta local.

```sh
python Recursos_Galaga3D/scripts/generar_hud.py
python Recursos_Galaga3D/scripts/generar_texto_hud.py
blender --background --factory-startup --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_interfaz_blender.py
python Recursos_Galaga3D/scripts/verificar_hud.py
blender --background Recursos_Galaga3D/blender/Galaga3D_Interfaz.blend --python-exit-code 1 --python Recursos_Galaga3D/scripts/verificar_blender.py
```

Los generadores reconstruyen sus recursos; conservar una copia de cualquier edición manual antes de ejecutarlos. Los verificadores no guardan cambios en el `.blend`; generan informes JSON y una imagen de prueba. `validacion_hud_final.json` y `validacion_blender_final.json` recogen la revisión final: archivos, transparencia, atlas, cifras, recortes, valores límite, planos, pausa y portabilidad de las fuentes y rutas.

Para las versiones retro se utilizan `scripts/generar_retro_blender.py`, `scripts/verificar_retro_blender.py` y `scripts/verificar_botones_retro.py`. Estos verificadores generan sus informes en `previews/Retro/`. Revisan la estructura, animaciones y geometría de botones en segundo plano. Los clics y atajos se comprueban aparte en una ventana de Blender.

## Subir a GitHub

Incluir los archivos de Blender, recursos del HUD, fuentes, vistas previas finales y scripts. Las copias `.blend1` y los fotogramas intermedios no son necesarios. Conservar `fonts/bitstream-vera-license.txt`; la licencia de Bitstream Vera está limitada a las fuentes.

Los gráficos se han generado para este proyecto y no contienen sprites de Namco. Las referencias al juego y al diseño están en la documentación del repositorio.
