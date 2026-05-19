# descargar_catalogo.py

Script para descargar automáticamente los textos escolares del [Catálogo Mineduc](https://catalogotextos.mineduc.cl) usando credenciales de establecimiento (RBD + contraseña SIGE).

## Requisitos

```bash
pip3 install playwright requests beautifulsoup4 --break-system-packages
python3 -m playwright install chromium
```

## Uso básico

```bash
python3 descargar_catalogo.py --rbd TU_RBD --password TU_CLAVE_SIGE
```

Por defecto descarga **1° a 6° Básico** (todos los sectores disponibles).

## Opciones de nivel (`--nivel`)

| Opción | Cursos descargados |
|---|---|
| *(sin `--nivel`)* | Todo el catálogo |
| `pre-escolar` | Pre-Kínder y Kínder |
| `basica` | 1° a 6° Básico |
| `media` | 7° y 8° Básico + 1° a 4° Medio |

### Todo el catálogo (default)

```bash
python3 descargar_catalogo.py --rbd 12345 --password MiClave
```

### Solo Pre-Kínder y Kínder

```bash
python3 descargar_catalogo.py --rbd 12345 --password MiClave --nivel pre-escolar
```

### Solo Educación Básica (1° a 6°)

```bash
python3 descargar_catalogo.py --rbd 12345 --password MiClave --nivel basica
```

### Solo Educación Media (7° Básico a 4° Medio)

```bash
python3 descargar_catalogo.py --rbd 12345 --password MiClave --nivel media
```

## Estructura de salida

Los PDFs se guardan en `uploads/` organizados por curso y asignatura:

```
uploads/
  1_basico/
    lenguaje_y_comunicacion/
      texto_del_estudiante_3261.pdf
    ciencias_naturales/
      texto_del_estudiante_3412.pdf
    matematica/
      texto_del_estudiante_3089.pdf
  2_basico/
    historia_geografia_y_ciencias_sociales/
      texto_del_estudiante_3190.pdf
    ...
  3_basico/
    ...
```

## Comportamiento

- **Login automático**: abre Chromium visible, rellena RBD y contraseña, y maneja el reCAPTCHA del sitio.
- **Progreso por archivo**: muestra barra de avance con MB descargados.
- **Re-ejecutable**: omite archivos que ya existen en `uploads/`.
- **Reintentos**: 3 intentos automáticos por archivo con 5 segundos de espera entre cada uno.

## Notas

- El navegador Chromium se abre y cierra solo durante el login (~15 segundos). El resto de la descarga ocurre en segundo plano.
- Si el login falla (contraseña incorrecta, sesión expirada), el script se detiene e indica el error.
- Los archivos parciales (`.tmp`) se eliminan automáticamente si la descarga se interrumpe.
