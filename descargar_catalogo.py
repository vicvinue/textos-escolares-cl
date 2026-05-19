"""
Descarga automatizada de textos escolares desde catalogotextos.mineduc.cl
Uso: python3 descargar_catalogo.py --rbd 12345 --password TuClave

- Login via Playwright (maneja reCAPTCHA con navegador real)
- Descarga via requests (más rápido, reutiliza la sesión autenticada)
- PDFs guardados en ./uploads/ con nombre: NIVEL_SECTOR_ID.pdf
"""

import argparse
import re
import sys
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE_URL     = "https://catalogotextos.mineduc.cl/catalogo-textos"
LOGIN_URL    = f"{BASE_URL}/login/login"
JSON_URL     = f"{BASE_URL}/privado/privadoJson"
DOWNLOAD_URL = f"{BASE_URL}/privado/descargar"
UPLOADS_DIR  = Path(__file__).parent / "Textos Mineduc"


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[°º]", "", text)
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),("ü","u")]:
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def login_playwright(rbd: str, password: str) -> dict:
    """Abre un navegador real, hace login y devuelve las cookies de sesión."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page    = context.new_page()

        page.goto(f"{LOGIN_URL}?tipo=ee", wait_until="domcontentloaded", timeout=60000)

        # Esperar a que el formulario esté listo
        page.wait_for_selector("#establecimiento_rbd", timeout=15000)
        time.sleep(5)

        # Activar tab Establecimiento
        try:
            page.click('a[href="#tab-establecimiento"], [href*="establecimiento"], li:has([data-tipo-usuario="establecimiento"]) a', timeout=5000)
            time.sleep(1)
        except PWTimeout:
            print("  WARN: no se encontró el tab Establecimiento, continuando igual")

        # Rellenar RBD y contraseña
        page.fill("#establecimiento_rbd",      rbd)
        page.fill("#establecimiento_password", password)
        time.sleep(1)

        # Click en Ingresar (dispara recaptcha + submit)
        page.click("#ingresar")

        # Esperar redirección fuera del login (hasta 20s para que resuelva el captcha)
        try:
            page.wait_for_function("!window.location.href.includes('login')", timeout=20000)
        except PWTimeout:
            print(f"  WARN: timeout esperando redirección — URL actual: {page.url}")

        if "login" in page.url:
            try:
                error_text = page.locator(".alert, .error, .invalid-feedback").first.inner_text()
                print(f"  Error en página: {error_text}")
            except Exception:
                pass
            browser.close()
            return {}

        print(f"  URL tras login: {page.url}")

        # Extraer cookies
        cookies = {c["name"]: c["value"] for c in context.cookies()}
        cookies["__post_login_url__"] = page.url
        browser.close()
        return cookies


def get_select_options(session: requests.Session) -> tuple[dict, dict, str]:
    """Obtiene niveles, sectores y rutaImagenes desde la página del catálogo."""
    r = session.get(f"{BASE_URL}/home/index")
    print(f"  Catálogo URL: {r.url}  status: {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    niveles  = {}
    sectores = {}

    for sel in soup.find_all("select"):
        sel_id = sel.get("id", "")
        opts = {
            o["value"]: o.get_text(strip=True)
            for o in sel.find_all("option")
            if o.get("value") and o["value"] not in ("-1", "0", "")
        }
        if sel_id == "idNivel":
            niveles = opts
        elif sel_id == "idSector":
            sectores = opts

    # Extraer rutaImagenes del JS inline (ej: var rutaImagenes = "2026/";)
    ruta_imagenes = "2026/"
    for script in soup.find_all("script"):
        text = script.string or ""
        m = re.search(r'var\s+rutaImagenes\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            ruta_imagenes = m.group(1)
            break

    return niveles, sectores, ruta_imagenes


def download_image(session: requests.Session, img_url: str, dest: Path) -> None:
    """Descarga la portada si no existe ya."""
    if dest.exists():
        return
    try:
        r = session.get(img_url, timeout=30)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            dest.write_bytes(r.content)
    except Exception:
        pass


def fetch_books(session: requests.Session, id_nivel: str, id_sector: str,
                csrf_token: str, csrf_header: str) -> list[dict]:
    """Llama al endpoint JSON y retorna los libros con sus materiales descargables."""
    data = {
        "idNivel":  id_nivel,
        "idSector": id_sector,
    }
    headers = {csrf_header: csrf_token, "X-Requested-With": "XMLHttpRequest"}
    try:
        r = session.post(JSON_URL, data=data, headers=headers, timeout=30)
        if r.status_code != 200:
            return []
        return r.json()
    except Exception:
        return []


def download_pdf(session: requests.Session, id_material_asociado: str,
                 dest: Path) -> bool:
    url = f"{DOWNLOAD_URL}/{id_material_asociado}"
    for attempt in range(1, 4):
        try:
            r = session.get(url, stream=True, timeout=300)
            if r.status_code != 200:
                print(f"      HTTP {r.status_code}")
                return False
            content_type = r.headers.get("Content-Type", "")
            if "pdf" not in content_type and "octet" not in content_type:
                print(f"      Content-Type inesperado: {content_type}")
                return False

            total   = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            tmp = dest.with_suffix(".tmp")

            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=131072):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct  = downloaded / total * 100
                        done = int(pct / 5)
                        bar  = "█" * done + "░" * (20 - done)
                        print(f"\r      [{bar}] {pct:4.0f}%  {downloaded/1_048_576:.1f}/{total/1_048_576:.1f} MB", end="", flush=True)
                    else:
                        print(f"\r      {downloaded/1_048_576:.1f} MB", end="", flush=True)

            print()  # salto de línea al terminar
            tmp.rename(dest)
            return dest.stat().st_size > 10_000
        except Exception as e:
            print(f"\n      intento {attempt}/3 falló: {e}")
            if attempt < 3:
                time.sleep(5)
    return False


NIVEL_FILTERS = {
    "todos": {
        "desc": "Todos los niveles",
        "match": lambda l: True,
    },
    "pre-escolar": {
        "desc": "Pre-Kínder y Kínder",
        "match": lambda l: any(x in l.lower() for x in ["kínder","kinder","pre-kínder","pre-kinder","transición","transicion"]),
    },
    "basica": {
        "desc": "1° a 6° Básico",
        "match": lambda l: any(x in l for x in ["Básico","básico"]) and any(x in l for x in ["1","2","3","4","5","6"]),
    },
    "media": {
        "desc": "7° Básico a 4° Medio",
        "match": lambda l: (any(x in l for x in ["Básico","básico"]) and any(x in l for x in ["7","8"]))
                        or  any(x in l for x in ["Medio","medio"]),
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rbd",      required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nivel", default="todos",
                        choices=list(NIVEL_FILTERS.keys()),
                        help="Rango de cursos a descargar (default: todos)")
    args = parser.parse_args()

    UPLOADS_DIR.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # ── Login via Playwright (maneja reCAPTCHA) ────────────────────────────────
    print("=== Login (abriendo navegador) ===")
    cookies = login_playwright(args.rbd, args.password)
    if not cookies:
        print("ERROR: login fallido. Verifica RBD y contraseña.")
        sys.exit(1)
    post_login_url = cookies.pop("__post_login_url__", None)
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".catalogotextos.mineduc.cl")
    print(f"Login OK — cookies: {list(cookies.keys())}")
    if post_login_url:
        print(f"  URL catálogo: {post_login_url}")

    # ── Obtener opciones de los selects ────────────────────────────────────────
    print("\n=== Leyendo catálogo ===")
    niveles, sectores, ruta_imagenes = get_select_options(session)

    if not niveles or not sectores:
        print("ERROR: no se encontraron opciones de curso/sector.")
        print("  Puede que el login haya fallado silenciosamente.")
        sys.exit(1)

    print(f"Niveles:  {niveles}")
    print(f"Sectores: {sectores}")

    # Obtener CSRF para las peticiones AJAX
    r_home = session.get(f"{BASE_URL}/home/index")
    soup   = BeautifulSoup(r_home.text, "html.parser")
    meta_token  = soup.find("meta", {"name": "_csrf"})
    meta_header = soup.find("meta", {"name": "_csrf_header"})
    csrf_token  = meta_token["content"]  if meta_token  else ""
    csrf_header = meta_header["content"] if meta_header else "X-CSRF-TOKEN"

    # ── Recolectar todos los libros ────────────────────────────────────────────
    filtro = NIVEL_FILTERS[args.nivel]
    print(f"\n=== Recolectando libros — {filtro['desc']} ===")
    to_download = []
    seen = set()

    for id_nivel, label_nivel in niveles.items():
        if not filtro["match"](label_nivel):
            continue

        for id_sector, label_sector in sectores.items():
            books = fetch_books(session, id_nivel, id_sector, csrf_token, csrf_header)
            time.sleep(0.5)

            for book in books:
                titulo       = book.get("titulo", "sin_titulo")
                nombre_img   = book.get("nombreImagen", "")
                img_stem     = Path(nombre_img).stem  # ej: "LYCME26E1B"
                img_url      = f"{BASE_URL}/portadas/{ruta_imagenes}{nombre_img}" if nombre_img else ""

                pdfs_en_libro = [m for m in book.get("materialAsociado", [])
                                 if m.get("tipoLink") == "DESCARGA"
                                 and m.get("link","").split(".")[-1].lower() == "pdf"]

                for i, mat in enumerate(pdfs_en_libro):
                    mid = str(mat["idMaterialAsociado"])
                    if mid in seen:
                        continue
                    seen.add(mid)

                    tipo   = mat.get("tipoMaterialDescripcion", "texto")
                    subdir = UPLOADS_DIR / label_nivel / label_sector

                    # Nombre basado en código oficial (ej: LYCME26E1B.pdf)
                    # Si hay >1 PDF por libro, añadir sufijo del tipo
                    if img_stem:
                        base = img_stem if len(pdfs_en_libro) == 1 else f"{img_stem}_{slugify(tipo)}"
                    else:
                        base = slugify(tipo)

                    # Evitar colisión dentro de la misma carpeta
                    used = {item["filename"] for item in to_download if item["subdir"] == subdir}
                    filename = f"{base}.pdf"
                    n = 2
                    while filename in used:
                        filename = f"{base}_{n}.pdf"
                        n += 1

                    to_download.append({
                        "id":       mid,
                        "nivel":    label_nivel,
                        "sector":   label_sector,
                        "titulo":   titulo,
                        "tipo":     tipo,
                        "filename": filename,
                        "subdir":   subdir,
                        "img_url":  img_url,
                        "img_file": nombre_img,
                    })
                    print(f"  + {label_nivel} / {label_sector} — {filename}  ({titulo[:45]})")

    print(f"\nTotal PDFs encontrados: {len(to_download)}")
    if not to_download:
        print("No se encontraron libros. Revisa credenciales o disponibilidad del catálogo.")
        sys.exit(1)

    # ── Descargar ──────────────────────────────────────────────────────────────
    print("\n=== Descargando ===")
    ok = fail = skip = 0

    for i, item in enumerate(to_download, 1):
        subdir = item["subdir"]
        subdir.mkdir(parents=True, exist_ok=True)
        dest = subdir / item["filename"]

        if dest.exists():
            print(f"[{i}/{len(to_download)}] EXISTE   {item['nivel']} / {item['sector']} / {item['filename']}")
            skip += 1
            continue

        print(f"[{i}/{len(to_download)}] {item['nivel']} / {item['sector']} — {item['titulo'][:45]}")
        if download_pdf(session, item["id"], dest):
            size_mb = dest.stat().st_size / 1_048_576
            print(f"      ✓ {item['filename']}  ({size_mb:.1f} MB)")
            # Descargar portada en subcarpeta portadas/
            if item.get("img_url") and item.get("img_file"):
                portadas_dir = subdir / "portadas"
                portadas_dir.mkdir(exist_ok=True)
                img_dest = portadas_dir / item["img_file"]
                download_image(session, item["img_url"], img_dest)
            ok += 1
        else:
            print(f"      ✗ FALLO [{item['id']}]")
            fail += 1
        time.sleep(0.3)

    print(f"\n=== Resultado: {ok} descargados, {skip} ya existían, {fail} fallaron ===")
    print(f"PDFs en: {UPLOADS_DIR}")


if __name__ == "__main__":
    main()
