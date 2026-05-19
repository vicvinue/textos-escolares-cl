# textos-escolares-cl

Script Python para descargar automáticamente los textos escolares oficiales del Ministerio de Educación de Chile desde el [Catálogo de Textos Escolares](https://catalogotextos.mineduc.cl).

Cubre desde Pre-Kínder hasta 4° Medio, todas las asignaturas disponibles. Los archivos se organizan por curso y asignatura usando los **nombres oficiales del catálogo** y el **código oficial del Mineduc** como nombre de archivo.

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

Al ejecutar el script aparece un menú interactivo para elegir qué niveles descargar:

```
=== Selección de niveles ===

  [0] Todos
  ── Grupos ──────────────────────────────
  [A] Pre-escolar (Pre-Kínder y Kínder)
  [B] Básica (1° a 8° Básico)
  [C] Media (1° a 4° Medio)
  ── Por nivel ───────────────────────────
  [1] Pre-Kínder
  [2] Kínder
  [3] 1º Básico
  ...

Ingresa opciones separadas por coma (ej: A, 3,4 o 0 para todos):
```

Se puede ingresar una letra de grupo (`A`, `B`, `C`), números de niveles individuales, o combinarlos (`B,5,6`). Ingresa `0` para descargar todo el catálogo.

---

## Estructura de salida

Los archivos se guardan en `Textos Mineduc/` con la estructura real del catálogo. Cada PDF usa el código oficial del Mineduc como nombre. Las portadas se guardan en una subcarpeta `portadas/` dentro de cada asignatura:

```
Textos Mineduc/
  1º Básico/
    Lenguaje y Comunicación/
      LYCME26E1B.pdf
      portadas/
        LYCME26E1B.jpg
    Ciencias Naturales/
      CNME26E1B.pdf
      portadas/
        CNME26E1B.jpg
    Matemática/
      MATME26E1B.pdf
      portadas/
        MATME26E1B.jpg
  2º Básico/
    Historia, Geografía y Ciencias Sociales/
      HGME26E2B.pdf
      portadas/
        HGME26E2B.jpg
  ...
  1° Medio/
    Biología/
      BIME26E1M.pdf
      portadas/
        BIME26E1M.jpg
```

---

## Cómo funciona

1. **Login automático** — abre Chromium, completa el formulario de establecimiento y maneja el reCAPTCHA del sitio (~15 segundos). El navegador se cierra una vez autenticado.
2. **Recolección** — consulta el endpoint interno del catálogo por cada combinación de curso y asignatura, extrayendo los IDs y códigos de descarga.
3. **Descarga en paralelo** — descarga 2 PDFs simultáneamente, cada uno con su propia barra de progreso en vivo, 3 reintentos automáticos y timeout de 5 minutos por archivo. También descarga la imagen de portada de cada texto.
4. **Re-ejecutable** — los archivos ya descargados se omiten, por lo que se puede interrumpir y continuar en cualquier momento sin duplicados.

Durante la descarga el terminal muestra algo así:

```
↓  1° Básico / Lenguaje y Comunicación — Texto del Estudiante
↓  1° Básico / Matemática — Texto del Estudiante
  [████████████░░░░░░░░]  60%  6.2/10.3 MB  LYCME26E1B.pdf
  [████░░░░░░░░░░░░░░░░]  20%  2.1/10.3 MB  MATME26E1B.pdf
```

---

## Aviso legal

Los textos escolares son propiedad del **Ministerio de Educación de Chile** y se distribuyen gratuitamente a establecimientos educacionales subvencionados. Este script es una herramienta de automatización para acceder a material al que el establecimiento ya tiene acceso legítimo a través del catálogo oficial.

**No redistribuyas los archivos descargados.** El uso de este script es responsabilidad del usuario y debe enmarcarse en las condiciones de uso del catálogo Mineduc.

**Privacidad:** el script ejecuta todo de forma local en tu equipo. Las credenciales (RBD y contraseña) se usan exclusivamente para autenticarse en el sitio oficial del Mineduc y nunca se almacenan en disco ni se transmiten a ningún servidor externo.

---

## Licencia

MIT
