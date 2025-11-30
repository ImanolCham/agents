# perfume_db.py

import os
import re
import pandas as pd
from functools import lru_cache
from difflib import get_close_matches
from openai import OpenAI

client = OpenAI()

# ---------- CONFIG ----------

MAIN_CSV_PATH = "data/final_perfume_data.csv"   # Name, Brand, Description, Notes, Image URL
FRA_CSV_PATH = "data/fra_cleaned.csv"          # url, Perfume, Brand, Country, Gender, Rating Value, ...


# ---------- UTILIDADES GENERALES ----------

def to_slug(text: str) -> str:
    """Convierte 'Le Beau' -> 'le-beau', quitando cosas raras."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # sustituimos cualquier cosa que no sea letra o número por '-'
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text

def translate_text(text: str, target_lang: str = "es") -> str:
    """Traduce `text` al idioma indicado usando OpenAI."""
    if not isinstance(text, str) or not text.strip():
        return ""

    prompt = (
        f"Traduce el siguiente texto al {target_lang}, manteniendo un estilo natural. "
        "Devuelve solo el texto traducido, sin comillas ni explicaciones:\n\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un traductor profesional."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content.strip()


def _fuzzy_row(df: pd.DataFrame, col_norm: str, name: str):
    """Devuelve la fila cuyo nombre se parece más a `name` o None."""
    name_norm = str(name).lower().strip()
    all_names = df[col_norm].tolist()
    match = get_close_matches(name_norm, all_names, n=1, cutoff=0.6)
    if not match:
        return None
    return df[df[col_norm] == match[0]].iloc[0]


# ---------- DATASET PRINCIPAL: final_perfume_data.csv ----------

@lru_cache
def load_main_df() -> pd.DataFrame:
    if not os.path.exists(MAIN_CSV_PATH):
        raise FileNotFoundError(f"No encuentro el CSV principal en: {MAIN_CSV_PATH}")

    df = pd.read_csv(MAIN_CSV_PATH, encoding="latin1")
    # Comprobamos columnas mínimas
    required = ["Name", "Brand", "Description", "Notes", "Image URL"]
    for c in required:
        if c not in df.columns:
            raise KeyError(f"Falta la columna '{c}' en el CSV principal. Columnas: {list(df.columns)}")

    df["name_norm"] = df["Name"].astype(str).str.lower().str.strip()
    return df


def parse_notes_main(raw_notes: str):
    if not isinstance(raw_notes, str):
        return []
    return [p.strip() for p in raw_notes.split(",") if p.strip()]


def build_info_html_main(row) -> tuple[str, str]:
    """HTML + imagen usando el CSV principal (con descripción y notas)."""
    name = row["Name"]
    brand = row["Brand"]
    desc = str(row.get("Description", "")).strip()
    notes = parse_notes_main(row.get("Notes", ""))
    image_url = str(row.get("Image URL", "")).strip()

    # Recortamos descripción muy larga
    max_len = 700
    if len(desc) > max_len:
        desc_short = desc[:max_len].rsplit(" ", 1)[0] + "..."
    else:
        desc_short = desc

    # Traducciones
    desc_short_es = translate_text(desc_short, "es")
    notes_es = [translate_text(n, "es") for n in notes]

    notes_html = ""
    if notes_es:
        notes_html = "<ul>" + "".join(f"<li>{n}</li>" for n in notes_es) + "</ul>"

    html = f"""
    <div style="font-family: system-ui; max-width: 700px;">
      <h2 style="margin-bottom: 4px;">{name}</h2>
      <h3 style="margin-top: 0; font-weight: 400; color: #555;">{brand}</h3>

      <p style="line-height:1.5; text-align:justify;">{desc_short_es}</p>

      <h4>Notas</h4>
      {notes_html}
    </div>
    """

    return html, image_url


def find_in_main(name: str):
    df = load_main_df()
    return _fuzzy_row(df, "name_norm", name)


# ---------- DATASET SECUNDARIO: fra_cleaned.csv ----------

@lru_cache
def load_fra_df() -> pd.DataFrame:
    if not os.path.exists(FRA_CSV_PATH):
        raise FileNotFoundError(f"No encuentro el CSV fra_cleaned en: {FRA_CSV_PATH}")

    df = pd.read_csv(
        FRA_CSV_PATH,
        encoding="latin1",    # o "cp1252" si hiciera falta
        sep=";",              # 👈 MUY IMPORTANTE: separador por ';'
        engine="python",
        on_bad_lines="skip",
    )

    print("fra_cleaned columns:", list(df.columns))

    required = ["Perfume", "Brand"]
    for c in required:
        if c not in df.columns:
            raise KeyError(f"Falta la columna '{c}' en fra_cleaned. Columnas: {list(df.columns)}")

    df["perfume_norm"] = df["Perfume"].astype(str).str.lower().str.strip()
    return df


def _safe_list_from_col(row, colname: str):
    val = row.get(colname, "")
    if not isinstance(val, str):
        return []
    return [p.strip() for p in val.split(",") if p.strip() and p.strip().lower() != "unknown"]


def build_info_html_fra(row) -> tuple[str, str]:
    """
    Construye HTML usando fra_cleaned: genera una pequeña descripción
    a partir de mainaccords + notas top/middle/base y la traduce al español.
    """
    name = row["Perfume"]
    brand = row["Brand"]
    country = row.get("Country", "")
    gender = row.get("Gender", "")
    year = row.get("Year", "")

    # Main accords 1-5
    accords = []
    for col in ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]:
        val = row.get(col, "")
        if isinstance(val, str) and val.strip() and val.strip().lower() != "unknown":
            accords.append(val.strip())

    # Notas Top / Middle / Base
    top_notes = _safe_list_from_col(row, "Top")
    middle_notes = _safe_list_from_col(row, "Middle")
    base_notes = _safe_list_from_col(row, "Base")

    # Descripción "sintética" en inglés (luego la traducimos)
    parts = []
    if gender or country or year:
        parts.append(
            f"{name} by {brand} is a fragrance"
            + (f" for {gender}" if isinstance(gender, str) and gender else "")
            + (f" from {country}" if isinstance(country, str) and country else "")
            + (f" released in {year}" if str(year).strip() not in ("", "nan") else "")
            + "."
        )

    if accords:
        accords_txt = ", ".join(accords)
        parts.append(f"Its main accords are: {accords_txt}.")

    if top_notes:
        parts.append("Top notes include: " + ", ".join(top_notes) + ".")
    if middle_notes:
        parts.append("Heart notes include: " + ", ".join(middle_notes) + ".")
    if base_notes:
        parts.append("Base notes include: " + ", ".join(base_notes) + ".")

    desc_en = " ".join(parts) if parts else f"{name} by {brand} is a fragrance."

    # Traducimos la descripción completa
    desc_es = translate_text(desc_en, "es")

    # Listas traducidas para HTML
    top_es = [translate_text(n, "es") for n in top_notes]
    middle_es = [translate_text(n, "es") for n in middle_notes]
    base_es = [translate_text(n, "es") for n in base_notes]

    accords_es = [translate_text(a, "es") for a in accords]

    # Construimos HTML
    accords_html = ""
    if accords_es:
        accords_html = (
            "<p><b>Acordes principales:</b> "
            + ", ".join(accords_es)
            + "</p>"
        )

    notes_html = "<div>"
    if top_es:
        notes_html += "<p><b>Notas de salida:</b> " + ", ".join(top_es) + "</p>"
    if middle_es:
        notes_html += "<p><b>Notas de corazón:</b> " + ", ".join(middle_es) + "</p>"
    if base_es:
        notes_html += "<p><b>Notas de fondo:</b> " + ", ".join(base_es) + "</p>"
    notes_html += "</div>"

    html = f"""
    <div style="font-family: system-ui; max-width: 700px;">
      <h2 style="margin-bottom: 4px;">{name}</h2>
      <h3 style="margin-top: 0; font-weight: 400; color: #555;">{brand}</h3>

      <p style="line-height:1.5; text-align:justify;">{desc_es}</p>
      {accords_html}
      {notes_html}
    </div>
    """

    # En fra_cleaned la columna 'url' suele ser página, no imagen -> devolvemos None
    image_url = None
    return html, image_url


def find_in_fra(name: str):
    df = load_fra_df()

    # 1) Intento "inteligente" con slug: 'Le Beau' -> 'le-beau'
    slug = to_slug(name)
    if slug:
        mask = df["Perfume"].astype(str).str.contains(slug, case=False, na=False)
        if mask.any():
            # si hay varios, te puedes quedar por ejemplo con el de mejor rating
            candidates = df[mask]
            # aquí simplemente cojo el primero:
            return candidates.iloc[0]

    # 2) Si no hay coincidencias por slug, usamos fuzzy matching normal
    return _fuzzy_row(df, "perfume_norm", name)


# ---------- FUNCIÓN PÚBLICA: BUSCA PRIMERO EN MAIN, LUEGO EN FRA ----------

def get_perfume_info(name: str):
    """
    1) Busca en final_perfume_data.csv (principal).
    2) Si no lo encuentra, busca en fra_cleaned.csv.
    3) Si tampoco, devuelve None.
    """
    # 1) Dataset principal
    row = find_in_main(name)
    if row is not None:
        html, image_url = build_info_html_main(row)
        return {
            "name": row["Name"],
            "brand": row["Brand"],
            "html": html,
            "image_url": image_url,
        }

    # 2) Dataset secundario (fra_cleaned)
    row = find_in_fra(name)
    if row is not None:
        html, image_url = build_info_html_fra(row)
        return {
            "name": row["Perfume"],
            "brand": row["Brand"],
            "html": html,
            "image_url": image_url,  # será None normalmente
        }

    # 3) No encontrado
    return None
