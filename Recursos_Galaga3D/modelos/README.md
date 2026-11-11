# Mallas 3D del juego

[Mallas_Galaga3D.blend](../blender/Mallas_Galaga3D.blend) contiene los modelos editables. Son geometría con profundidad: cada fuselaje, ala, motor, cabina y pieza de armadura tiene una superficie cerrada. No se usan imágenes planas para representar las naves.

## Modelos y escenas

La escena `01_Modelos` reúne las tres naves, los dos enemigos y el jefe. `02_Sector_espacial` contiene un planeta, una estación con forma de anillo y asteroides laterales. Una formación de ejemplo permite revisar la escala. `03_Cabina_y_obstaculos` contiene el asteroide de la fase de esquiva y el marco físico de la vista en primera persona.

| Archivo | Triángulos | Piezas cerradas |
| --- | ---: | ---: |
| nave_flecha.obj | 2780 | 23 |
| nave_delta.obj | 2344 | 20 |
| nave_doble_motor.obj | 2788 | 23 |
| enemigo_abeja.obj | 3204 | 22 |
| enemigo_escarabajo.obj | 3220 | 20 |
| jefe_acorazado.obj | 4568 | 27 |
| escenario_orbital.obj | 7936 | 23 |
| cockpit_marco.obj | 332 | 9 |
| obstaculo_asteroide.obj | 80 | 1 |

Los nueve archivos suman 27.252 triángulos. Cada OBJ tiene su MTL. `catalogo.json` recoge los recuentos y los límites exactos de cada modelo. Las distintas piezas pueden solaparse para formar un conjunto; cada pieza, por separado, es un sólido cerrado y orientado hacia fuera.

Para dibujar enemigos lejanos se incluyen dos versiones de menor detalle, llamadas LOD:

| Archivo | Triángulos | Piezas cerradas | Modelo original |
| --- | ---: | ---: | --- |
| enemigo_abeja_lod.obj | 932 | 22 | enemigo_abeja.obj |
| enemigo_escarabajo_lod.obj | 924 | 20 | enemigo_escarabajo.obj |

Estos dos archivos reducen aproximadamente un 71 % los triángulos de los enemigos. Conservan las alas y las placas pequeñas, el volumen cerrado de todas las piezas, sus límites espaciales y los mismos materiales. Los cuerpos curvos, ojos y articulaciones usan menos triángulos. Los modelos detallados se mantienen para las vistas cercanas; las variantes LOD se destinan al dibujo a más de diez unidades del jugador. La selección de geometría no cambia las reglas de movimiento, disparo ni colisión.

Los once OBJ suman 29.108 triángulos almacenados. El modelo completo y su LOD son alternativas de dibujo: no se superponen. Los originales editables del archivo Blender permanecen intactos; las variantes se calculan sobre copias temporales y se exportan como archivos independientes.

Las naves se construyen con secciones elípticas de diferente tamaño, que forman el fuselaje, y perfiles de ala que conservan grosor en sus bordes. Las toberas son anillos cerrados con interior y núcleo, las cabinas son superficies curvas y las aletas tienen caras por ambos lados. Las placas de armadura siguen el perfil de las alas. Las bandas de los insectos y de los motores se asignan a las caras de la propia superficie.

Los fuselajes, cabinas y toberas usan normales suaves. Las alas, placas y rocas conservan aristas visibles. Así se distingue una superficie curva de una placa de metal sin aumentar innecesariamente los triángulos. Los materiales incluyen `Kd` para el color, `Ks` para la intensidad del brillo y `Ns` para su concentración; el vidrio, el metal y la roca responden de forma distinta a la iluminación Phong.

## Coordenadas

X es lateral, Y es avance y Z es altura. Las naves apuntan a +Y; los enemigos y el jefe apuntan a -Y. El objeto raíz del catálogo se coloca en una cuadrícula solo para editarlo: su posición no se exporta.

Las naves normales miden aproximadamente 1,3 unidades de ancho y 1,4 de largo. El jefe ocupa X entre -1,34 y 1,34; el juego puede ampliarlo con su matriz `model`. El asteroide individual está centrado en el origen y cabe aproximadamente en una esfera de radio 1,02.

El escenario se exporta directamente en coordenadas del mundo. El planeta está en (-29, 78, 21) y tiene radio 18. El anillo está en (23, 62, 6), con radio 8. Las masas principales quedan fuera del corredor central de combate. El marco de cabina mira hacia +Y; tiene la consola debajo y los montantes a los lados para dejar libre la visión frontal.

## Editar y exportar

Abre el archivo Blender y selecciona una escena. Las piezas cuelgan de un objeto raíz con la propiedad `export_obj`. Edita las piezas en coordenadas locales y conserva ese objeto raíz. Las instancias de ejemplo comparten las mallas del catálogo.

Para exportar los cambios guardados en Blender desde la raíz del repositorio:

```powershell
blender --background Recursos_Galaga3D/blender/Mallas_Galaga3D.blend --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py -- --export-only
```

Aplica los modificadores antes de exportar. El exportador triangula las caras y escribe posiciones, UV y normales en el formato `v/vt/vn`. Cada UV se obtiene de X/Y como coordenada básica; estos modelos se colorean con materiales sólidos. Para cada triángulo se conservan las normales suaves o las normales de cara que correspondan a la pieza.

Antes de escribir cada archivo, el exportador comprueba que las coordenadas sean finitas, que cada arista tenga exactamente dos caras con sentidos opuestos, que el volumen firmado sea positivo y que no haya triángulos degenerados. Un fallo detiene la exportación con el nombre de la pieza.

Para reconstruir los diseños desde los scripts:

```powershell
blender --background --factory-startup --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py
```

Este último comando sustituye el archivo Blender y los OBJ/MTL. Guarda aparte las ediciones manuales que quieras conservar. `scripts/mallas_volumetricas.py` define la geometría; `scripts/generar_mallas_juego.py` prepara las escenas, los materiales, la exportación y las comprobaciones.

Para regenerar exclusivamente los dos LOD a partir del archivo Blender existente:

```powershell
blender --background Recursos_Galaga3D/blender/Mallas_Galaga3D.blend --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py -- --lod-only
```

Esta opción escribe únicamente los dos pares OBJ/MTL reducidos y actualiza `catalogo.json`; no guarda el archivo Blender ni reexporta los nueve modelos originales. Aplica el modificador Decimate a copias independientes, conserva las piezas que definen el contorno y ajusta los extremos de cada pieza a sus límites originales. Después ejecuta las mismas comprobaciones de cierre, orientación, volumen y triángulos degenerados que usa el exportador normal. También comprueba que cada LOD tenga entre 800 y 1.100 triángulos. La generación completa y la opción `--export-only` producen igualmente los dos LOD.

## Relación con OpenGL y VGI

El juego lee las mallas OBJ y los materiales MTL, transforma los datos al formato intercalado de sus vértices y los sube a la GPU. Los VBO contienen los datos; los VAO describen sus atributos. Las matrices `model`, `view` y `projection` permiten colocar el mismo modelo en distintos puntos del espacio sin reconstruirlo. La matriz normal permite iluminar correctamente las superficies después de transformar el modelo. El buffer de profundidad resuelve qué cara queda delante.

El archivo Blender permite revisar y editar los sólidos; la apariencia y la lectura durante la partida deben comprobarse también en el ejecutable, porque la cámara y la iluminación del juego son diferentes de las de Blender.

El modelado y la exportación se han realizado con asistencia de Codex. El código docente y los constructores anteriores del proyecto conservan sus créditos.
