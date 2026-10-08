# HUD original · Galaga 3D

16 sprites originales: PNG **RGBA8** transparentes con alpha recto y SVG editables. `atlas_hud.png` agrupa los mismos sprites a 1024 × 512. No usa recursos gráficos de Namco. `preview_hud.png` muestra composición a 1280 × 720; `componentes_hud.png` muestra cada capa por separado. Los PNG de las vistas previas tienen fondo opaco y no son sprites.

## Barras por capas

Dibujar en este orden, **con la misma posición y dimensiones**: `vida_*_fondo`, `vida_*_relleno`, `vida_*_marco`. Jugador: 336 × 48; jefe: 640 × 48. El marco tiene centro transparente, por lo que no tapa el relleno. El fondo garantiza contraste. Labels y contadores se dibujan como texto de la aplicación y pueden traducirse.

El jugador conserva **3 vidas**: las tres celdas representan 3/3, 2/3, 1/3 o 0/3. No se introduce vida continua ni una regla adicional. El jefe conserva **24 HP**, con una marca por HP. `vida_nave.png` se puede repetir tres veces como alternativa a la barra; `vida_nave_inactiva.png` decora las reservas perdidas.

Para actualizar una barra: `r = clamp(valor / maximo, 0, 1)`. Conserva el quad completo y recorta **solo el relleno** mediante scissor/máscara en su rectángulo interno. Los límites internos son x=28..308 para jugador y x=28..612 para jefe; y=17..31. Limita la derecha a `28 + ancho_interno * r`. A 0 no dibujes el relleno. No escales horizontalmente la textura: deformaría las celdas. La ficha de cada sprite del atlas incorpora `fill_rect_px` y `max_value`.

## Iconos y reglas

`plano_A`: círculo + cian + letra A; usar texto **PLANO A · CERCA**. `plano_B`: rombo + ámbar + letra B; texto **PLANO B · LEJOS**. No depender solo del color. Iconos de plano, nave, pausa, escudo, doble disparo, aviso y flecha: 64 × 64. Mira: 96 × 96. Son adecuados a 48–64 px en un HUD de 1280 × 720; se recomienda mantener 24 px de margen al borde.

`escudo` es un indicador visual de **invulnerabilidad** ya prevista; no añade un power-up de escudo a P0. `doble_disparo` pertenece a P2 opcional. La mira es una ayuda visual opcional y no cambia la puntería. `aviso` acompaña la señal del plano de ataque del jefe. La flecha apunta a la derecha; girarla por transformaciones para otros sentidos. El prototipo no cambia reglas por cargar estos archivos.

## Atlas y OpenGL

`atlas_hud.json` contiene `rect_px: [x,y,ancho,alto]` con origen **arriba a la izquierda**, y dos UV explícitas `[u_min,v_min,u_max,v_max]`:

- `uv_top_left`: filas PNG sin invertir; v=0 corresponde a la fila superior del PNG. Asociar v mínima al vértice superior del quad para verlo derecho.
- `uv_bottom_left`: invertir filas al cargar; v=0 corresponde a la parte inferior. Asociar v máxima al vértice superior del quad.

Cada sprite tiene 4 px de separación y 2 px de extrusión fuera de su rectángulo. Los rects excluyen la extrusión. Para este HUD, usar `GL_LINEAR`, `GL_CLAMP_TO_EDGE` y no generar mipmaps del atlas sin ampliar márgenes. Texturas con alpha **no premultiplicado**: `glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)`. Desactivar escritura de profundidad para el HUD y dibujarlo después de la escena 3D. El RGB de píxeles transparentes no contiene un fondo blanco.

## Regenerar y editar

`scripts/generar_hud.py` requiere Python y Pillow; no requiere Blender. Todas las formas usan una fuente compartida para SVG y rasterizado a 4× con reducción antialias. Los SVG no dependen de fuentes instaladas: las letras A/B están dibujadas con líneas. Las vistas previas usan exclusivamente las fuentes libres locales `fonts/Vera.ttf` y `fonts/VeraBd.ttf`; su licencia se incluye en `fonts/bitstream-vera-license.txt`. No hay rutas a fuentes del sistema. Los SVG son masters editables; si se editan manualmente, no ejecutar el generador sin guardar una copia, porque regenera el pack desde el script.

Paleta: navy `#101a2c`, hielo `#d8edf3`, cian `#36e6ed`, ámbar `#ffba52`, rojo `#fa5269`, morado `#9478ff`. Diseño geométrico original para este proyecto. No hay dependencias de red.
