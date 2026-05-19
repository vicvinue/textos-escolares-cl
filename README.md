# textos-escolares-cl

Script Python para descargar automáticamente los textos escolares oficiales del Ministerio de Educación de Chile desde el [Catálogo de Textos Escolares](https://catalogotextos.mineduc.cl).

Cubre desde Pre-Kínder hasta 4° Medio, todas las asignaturas disponibles, organizando los archivos por curso y asignatura.

---

## Requisitos

- Python 3.9+
- Credenciales de establecimiento del Catálogo Mineduc (RBD + contraseña SIGE)

```bash
pip3 install playwright requests beautifulsoup4
python3 -m playwright install chromium
```

---

## Uso

```bash
python3 descargar_catalogo.py --rbd TU_RBD --password TU_CLAVE_SIGE
```

Por defecto descarga **todo el catálogo**. Puedes filtrar por nivel:

| Parámetro | Cursos |
|---|---|
| *(sin `--nivel`)* | Todo el catálogo |
| `--nivel pre-escolar` | Pre-Kínder y Kínder |
| `--nivel basica` | 1° a 6° Básico |
| `--nivel media` | 7° Básico a 4° Medio |

Ejemplos:

```bash
# Solo educación básica
python3 descargar_catalogo.py --rbd XXXXX --password MiClave --nivel basica

# Solo educación media
python3 descargar_catalogo.py --rbd XXXXX --password MiClave --nivel media

# Solo pre-escolar
python3 descargar_catalogo.py --rbd XXXXX --password MiClave --nivel pre-escolar
```

---

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
  1_medio/
    biologia/
      texto_del_estudiante_4021.pdf
```

---

## Cómo funciona

1. **Login automático** — abre Chromium, completa el formulario de establecimiento y maneja el reCAPTCHA del sitio (~15 segundos).
2. **Recolección** — consulta el endpoint interno del catálogo por cada combinación de curso y asignatura, extrayendo los IDs de descarga.
3. **Descarga** — descarga cada PDF con barra de progreso, 3 reintentos automáticos y timeout de 5 minutos por archivo.
4. **Re-ejecutable** — los archivos ya descargados se omiten, por lo que se puede interrumpir y continuar sin problema.

---

## Aviso legal

Los textos escolares son propiedad del **Ministerio de Educación de Chile** y se distribuyen gratuitamente a establecimientos educacionales subvencionados. Este script es una herramienta de automatización para acceder a material al que el establecimiento ya tiene acceso legítimo a través del catálogo oficial.

**No redistribuyas los archivos descargados.** El uso de este script es responsabilidad del usuario y debe enmarcarse en las condiciones de uso del catálogo Mineduc.

---

## Licencia

MIT — libre para usar, modificar y distribuir el script.
