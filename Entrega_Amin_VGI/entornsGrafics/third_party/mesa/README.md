# Mesa LLVMpipe local

La demo utiliza OpenGL moderno con VAO, VBO y shaders. Este runtime local permite ejecutar ese mismo pipeline en CPU cuando el controlador de Windows solo expone OpenGL 1.1. No instala controladores ni modifica el registro o la configuracion del sistema.

- Mesa: **26.2.5**; LLVM: **23.1.3**; arquitectura: **Windows x64**.
- Distribuidor: [mmozeiko/build-mesa](https://github.com/mmozeiko/build-mesa/tree/26.2.5), compilacion estatica de las dependencias y del runtime C++.
- Archivo: [mesa-llvmpipe-x64-26.2.5.7z](https://github.com/mmozeiko/build-mesa/releases/download/26.2.5/mesa-llvmpipe-x64-26.2.5.7z).
- SHA256 del archivo: `d1b713ca2a7fba47a50c058099f13c435ddb76a16a422c334e4d787f9755a31d`.
- SHA256 de `opengl32.dll`: `8ddc061ee752fff06ae682de0ac2e010926d76a93c1aecc4c206adee771856e1`.

`scripts/setup-mesa.ps1 -Deploy` descarga, verifica y extrae unicamente `opengl32.dll`, y la copia junto a los ejecutables Debug y Release. `build-demo.cmd` realiza este paso automaticamente. El binario y la cache no se guardan en Git; la descarga es reproducible y se comprueba tambien al reutilizar archivos locales.

Solo se necesita esta DLL para WGL/OpenGL; no hacen falta EGL, Vulkan, `libgallium_wgl.dll`, `libglapi.dll` ni una DLL LLVM adicional. Las dependencias comprobadas con `dumpbin /DEPENDENTS` son exclusivamente componentes de Windows: KERNEL32, USER32, GDI32, SHELL32, ole32, ADVAPI32, ntdll y api-ms-win-core-synch-l1-2-0.

Los avisos de `licenses/` proceden del [archivo fuente oficial de Mesa 26.2.5](https://archive.mesa3d.org/mesa-26.2.5.tar.xz), SHA256 `794b3d1729075dae7ebd47c7283b7ca0cdb5dec668f7f11cc0a5d82f6138a0a5`, y de la [licencia de LLVM 23.1.3](https://raw.githubusercontent.com/llvm/llvm-project/llvmorg-23.1.3/LICENSE.TXT), SHA256 `8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee`. Se conservan las licencias de la distribucion fuente completa de Mesa como referencia; su aplicacion depende de cada componente, segun `license.rst`. La biblioteca Mesa principal utiliza MIT y LLVM utiliza Apache 2.0 con las excepciones indicadas en `LLVM.txt`.

El uso de CPU puede rendir menos que una GPU. `context.log` identifica el renderer efectivo y la verificacion grafica comprueba el pipeline real. Para probar el controlador nativo en otro ordenador, se puede apartar solo la copia local de `opengl32.dll` situada junto al ejecutable; el proyecto no modifica la DLL de Windows.
