# Mallas industriales de Galaga 3D

[Mallas_Galaga3D.blend](../blender/Mallas_Galaga3D.blend) contiene las naves y el entorno editables. Todos los vehículos son sólidos tridimensionales con caras superiores, inferiores y laterales. Los modelos actuales usan una estética industrial: fuselajes facetados, motores integrados, armas, cabinas oscuras y materiales marfil, gris y grafito con marcas apagadas.

La referencia de Squadrons sirve para diferenciar las funciones del casco, las armas y la propulsión, y para reconocer tipos de nave por su silueta. Los diseños y recursos de esta carpeta son originales. Referencias consultadas: [entrevista de StarWars.com](https://www.starwars.com/news/star-wars-squadrons-interview) y [presentación de jugabilidad de EA/Motive](https://www.ea.com/ea-studios/motive/news/pilot-briefing-gameplay-overview).

## Catálogo

| Archivo | Diseño | Triángulos | Piezas cerradas |
| --- | --- | ---: | ---: |
| nave_flecha.obj | Interceptor de morro largo y alas barridas | 2040 | 36 |
| nave_delta.obj | Caza de ala ancha y casco reforzado | 1856 | 38 |
| nave_doble_motor.obj | Cabina central y dos góndolas de motor | 1916 | 39 |
| enemigo_abeja.obj | Interceptor compacto | 1344 | 25 |
| enemigo_escarabajo.obj | Bombardero con dos barquillas y carga ventral | 2172 | 31 |
| jefe_acorazado.obj | Fragata con puente, baterías y tres reactores | 2544 | 39 |
| escenario_orbital.obj | Planeta, astillero, carguero y rocas laterales | 9812 | 51 |
| cockpit_marco.obj | Marcos finos, consola y vidrio oscuro | 828 | 17 |
| obstaculo_asteroide.obj | Fragmento rocoso de la fase de esquiva | 320 | 1 |
| enemigo_abeja_lod.obj | Interceptor reducido para distancia | 992 | 25 |
| enemigo_escarabajo_lod.obj | Bombardero reducido para distancia | 976 | 31 |

Se conservan los nombres históricos `abeja` y `escarabajo` para mantener la compatibilidad del juego. Sus diseños actuales son naves mecánicas, sin ojos ni cabezas de insecto.

Los once OBJ suman **24.800 triángulos almacenados**. El modelo completo y su LOD son alternativas: no se dibujan superpuestos. `catalogo.json` registra el número de piezas y los límites espaciales exactos.

Las escenas de Blender son:

- `01_Modelos`: las tres naves, los dos enemigos y la fragata.
- `02_Sector_espacial`: entorno y una formación de ejemplo para revisar escala.
- `03_Cabina_y_obstaculos`: marco de cabina y asteroide individual.

## Geometría y materiales

Los cascos se construyen con secciones biseladas de ocho lados. Las alas conservan grosor y un borde de ataque definido. Las toberas tienen labio exterior, garganta, núcleo y collar de unión. Las marcas principales se asignan a las caras del casco; los registros y rejillas son piezas que se apoyan en él.

Las superficies de chapa usan normales por cara para conservar los cambios de plano. Las toberas y superficies curvas usan normales suaves. La esfera del planeta y sus continentes usan superficies curvas; los continentes son parches sólidos cerrados, con sus fondos dentro de la esfera y sus caras superiores fuera de ella. Las costas no dependen de una cuadrícula de colores. La iluminación y las normales producen la separación entre el lado iluminado y el lado oscuro.

Cada MTL contiene:

- `Kd`: color base.
- `Ks` y `Ns`: intensidad y concentración del brillo Phong.
- `Ke`: emisión de las pequeñas luces de navegación, núcleos de motor y ventanas.

El metal, la pintura, el vidrio y la roca tienen respuestas distintas a la luz. La cabina del jugador conserva superficies de vidrio oscuro sin rayas ni indicadores luminosos decorativos: los datos de vuelo se presentan en el HUD del juego.

El astillero utiliza copias propias de sus materiales con color base y brillo un 40 % menores, para separar sus estructuras de los enemigos sin cambiar los materiales de las naves, el planeta ni el carguero.

## Escala y coordenadas

X es lateral, Y es avance y Z es altura. Las naves apuntan a +Y; los enemigos y el jefe a -Y. La posición de cada objeto raíz dentro de la cuadrícula de edición no se exporta.

| Nave | Ancho máximo X | Intervalo Y | Altura máxima Z |
| --- | --- | --- | --- |
| Flecha | ±0,78 | -0,78 a 0,88 | 0,31 |
| Delta | ±0,79 | -0,78 a 0,77 | 0,293 |
| Doble Motor | ±0,65 | -0,79 a 0,68 | 0,31 |

Las bocas de las toberas del jugador están en estas coordenadas locales y miran hacia -Y:

| Nave | X de los dos motores | Y | Z |
| --- | --- | --- | --- |
| Flecha | ±0,28 | -0,78 | -0,055 |
| Delta | ±0,31 | -0,78 | -0,065 |
| Doble Motor | ±0,49 | -0,79 | -0,025 |

Los enemigos normales miden aproximadamente una unidad de ancho. El jefe ocupa X entre -1,23 y 1,23, Y entre -0,94 y 0,92 y Z entre -0,235 y 0,505. La escala de dibujo se aplica mediante la matriz `model`; los volúmenes de contacto pertenecen a la lógica del juego.

El planeta está centrado en (-35, 92, 20), con radio base 22,5. El astillero ocupa principalmente el lateral derecho, entre X=20 y X=35; la grúa alcanza X=15,5 por encima del corredor. El carguero está alrededor de (-24, 92, -12). Estas masas quedan fuera del espacio central de combate.

## Editar y exportar

Cada modelo cuelga de un objeto raíz con la propiedad `export_obj`. Conserva ese objeto y edita las piezas en coordenadas locales. Las instancias de ejemplo comparten las mallas del catálogo.

Para exportar el archivo Blender guardado, desde la raíz del repositorio:

```powershell
blender --background Recursos_Galaga3D/blender/Mallas_Galaga3D.blend --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py -- --export-only
```

El exportador escribe triángulos con índices `v/vt/vn`: posiciones, UV y normales. Las UV se obtienen de X/Y como coordenadas básicas; esta colección se colorea con materiales sólidos. Aplica los modificadores antes de exportar.

Para reconstruir todo desde los scripts:

```powershell
blender --background --factory-startup --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py
```

Este comando sustituye el archivo Blender y los OBJ/MTL generados. Guarda aparte las ediciones manuales que quieras conservar. `scripts/mallas_volumetricas.py` define la geometría; `scripts/generar_mallas_juego.py` prepara escenas, materiales, exportación y validaciones.

Para regenerar exclusivamente los dos LOD:

```powershell
blender --background Recursos_Galaga3D/blender/Mallas_Galaga3D.blend --python-exit-code 1 --python Recursos_Galaga3D/scripts/generar_mallas_juego.py -- --lod-only
```

Los LOD se calculan sobre copias temporales con Decimate. Se conservan las alas y las piezas pequeñas; se ajustan los extremos de cada pieza a los límites originales. Los originales editables no se modifican. La generación completa y `--export-only` también producen los LOD.

## Comprobaciones y OpenGL

El exportador comprueba coordenadas finitas, ausencia de triángulos degenerados, volumen firmado positivo y exactamente dos caras por arista con sentidos opuestos. Cada pieza es un sólido cerrado; distintas piezas pueden solaparse para formar un conjunto unido. Estas comprobaciones no sustituyen la inspección de uniones, siluetas, cámara y composición.

El juego carga posiciones, normales, UV, colores y propiedades del material en buffers estáticos. Los VBO/EBO guardan los vértices e índices, y los VAO describen los atributos. Las matrices `model`, `view`, `projection` y la matriz normal permiten colocar e iluminar cada instancia. El buffer de profundidad resuelve las ocultaciones entre superficies.

Los renders de Blender permiten revisar los modelos desde distintos ángulos. La lectura de amenazas, la composición y el rendimiento deben comprobarse también en el ejecutable, con su cámara e iluminación.

El modelado y la exportación se han realizado con asistencia de Codex. El código docente y los constructores anteriores del proyecto conservan sus créditos.
