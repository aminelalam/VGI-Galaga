# Mallas 3D del juego anterior con las naves de la prueba 2D

Flecha, Delta y Doble Motor proceden de las mismas mallas de Blender con las que se renderizaron los sprites de la prueba 2D. Sus formas y piezas se conservan; se exportan a escala uniforme 0,75 para usarlas en el juego anterior basado en `cc3ced6`. Los enemigos, el jefe, el escenario y la cabina mantienen los OBJ/MTL de esa versión.

[Naves_2D_fuente.blend](../blender/Naves_2D_fuente.blend) contiene una copia dedicada de las tres escenas originales. Cada nave tiene un objeto raíz y piezas sólidas cerradas. [procedencia_naves_2d.json](procedencia_naves_2d.json) registra la fuente, los hashes de los sprites, la transformación aplicada y los resultados de la comprobación geométrica.

## Archivos

| Archivo | Triángulos | Piezas cerradas |
| --- | ---: | ---: |
| nave_flecha.obj | 92 | 6 |
| nave_delta.obj | 94 | 7 |
| nave_doble_motor.obj | 114 | 7 |
| enemigo_abeja.obj | 3204 | 22 |
| enemigo_escarabajo.obj | 3220 | 20 |
| jefe_acorazado.obj | 4568 | 27 |
| escenario_orbital.obj | 7936 | 23 |
| cockpit_marco.obj | 332 | 9 |
| obstaculo_asteroide.obj | 80 | 1 |

Estos nueve archivos suman 19.640 triángulos. Cada OBJ tiene su MTL. [catalogo.json](catalogo.json) recoge los recuentos, los límites de los modelos y la procedencia de las tres naves sustituidas. Las piezas pueden solaparse entre sí; cada pieza, por separado, tiene volumen y una superficie cerrada orientada hacia fuera.

Para los enemigos lejanos se conservan las dos variantes de menor detalle de la versión anterior:

| Archivo | Triángulos | Piezas cerradas | Modelo original |
| --- | ---: | ---: | --- |
| enemigo_abeja_lod.obj | 932 | 22 | enemigo_abeja.obj |
| enemigo_escarabajo_lod.obj | 924 | 20 | enemigo_escarabajo.obj |

Los once OBJ suman 21.496 triángulos almacenados. El modelo detallado y su LOD son alternativas de dibujo; el juego usa el reducido a más de diez unidades del jugador. Conservan los mismos materiales y límites espaciales.

## Forma y materiales de las naves

Flecha tiene un fuselaje azul alargado y alas blancas. Delta conserva el ala triangular roja con paneles blancos. Doble Motor mantiene el cuerpo verde rectangular y las dos barquillas largas. Son los sólidos originales de pocas piezas, con caras planas y tejados inclinados que forman su volumen.

El exportador conserva los materiales de la fuente. Convierte sus valores de color lineales de Blender a sRGB para el shader del juego anterior, que no realiza esa conversión al presentar la imagen. El manifiesto guarda ambos valores. Las naves usan `Ks = 0,16` y `Ns = 8` para un acabado mate. Los materiales y las normales de los demás modelos permanecen como en la versión anterior.

## Coordenadas

X es lateral, Y es avance y Z es altura. Las naves apuntan a +Y; los enemigos y el jefe apuntan a -Y. En las tres naves se incluye la transformación del objeto raíz para conservar el mismo centrado XY que tenían sus sprites. Después se aplica la escala 0,75 por igual a los tres ejes, sin deformar las proporciones.

| Nave | Ancho | Largo | Intervalo Z |
| --- | ---: | ---: | --- |
| Flecha | 1,275 | 1,260 | −0,1275 a 0,2775 |
| Delta | 1,275 | 1,260 | −0,1500 a 0,2925 |
| Doble Motor | 1,140 | 1,1475 | −0,1725 a 0,2925 |

El jefe conserva X entre −1,34 y 1,34; su matriz `model` puede ampliarlo durante el juego. El escenario mantiene el planeta en (−29, 78, 21), con radio 18, y el anillo en (23, 62, 6), con radio 8. Sus masas principales quedan fuera del corredor central de combate.

## Editar y exportar las tres naves

Abre `Recursos_Galaga3D/blender/Naves_2D_fuente.blend` y elige la escena `nave_flecha`, `nave_delta` o `nave_doble_motor`. Conserva el objeto raíz y sus piezas. El archivo dedicado mantiene las dimensiones originales; el exportador aplica la escala al escribir los OBJ.

Desde la raíz de esta copia, ejecuta con Blender en el PATH:

```powershell
blender --background --factory-startup --python-exit-code 1 --python Recursos_Galaga3D/scripts/exportar_naves_2d.py
```

La orden utiliza únicamente el Blender dedicado incluido en esta carpeta. Regenera los tres pares OBJ/MTL, actualiza sus entradas en el catálogo y escribe el manifiesto de procedencia. No vuelve a renderizar los sprites ni necesita los directorios del proyecto 2D.

El exportador escribe caras trianguladas en formato `v/vt/vn`. Comprueba coordenadas finitas, piezas cerradas, orientación exterior, volumen firmado positivo y ausencia de triángulos degenerados. Después relee los OBJ para verificar sus normales y su topología, y compara los vértices guardados con la fuente transformada. La exportación comprobada tiene un error máximo inferior a `1e-6` unidades.

Los scripts `generar_mallas_juego.py` y `mallas_volumetricas.py` corresponden a los diseños de la versión anterior. Una regeneración completa con ellos sustituye también las tres naves; para recuperar esta adaptación, ejecuta después `exportar_naves_2d.py`. La copia dedicada de las naves no se modifica durante la exportación normal.

## Relación con OpenGL y VGI

El juego lee los OBJ y MTL, prepara sus vértices e índices y los carga una vez en buffers estáticos. Los VAO describen los atributos. Cada instancia reutiliza esa geometría y envía las matrices `model`, `view` y `projection`; la matriz normal permite calcular la iluminación y el buffer de profundidad resuelve las ocultaciones.

Las comprobaciones del exportador validan los archivos. La lectura de las naves durante la partida se revisa también en el ejecutable, porque su cámara e iluminación son distintas de las del render ortográfico 2D.

La adaptación y su exportación se han realizado con asistencia de Codex. Se conservan los créditos del código docente y de los constructores anteriores del proyecto.
