# perfume_db.py
import pandas as pd
from functools import lru_cache
from difflib import get_close_matches


@lru_cache
def load_perfumes() -> pd.DataFrame:
    # Ajusta el nombre del fichero si es otro
    df = pd.read_csv("data/perfumes_detailed.csv")

    # Normalizamos el nombre para facilitar la búsqueda
    df["name_norm"] = df["Name"].str.lower().str.strip()
    return df


def find_perfume_row(name: str):
    """Devuelve la fila del perfume más parecido al proporcionado."""
    df = load_perfumes()
    name_norm = name.lower().strip()

    all_names = df["name_norm"].tolist()
    match = get_close_matches(name_norm, all_names, n=1, cutoff=0.6)

    if not match:
        return None

    row = df[df["name_norm"] == match[0]].iloc[0]
    return row


def parse_notes(raw_notes: str):
    """
    Convierte el string de notas en una lista limpia.
    Ejemplo: ' Vanilla bean, musks' -> ['Vanilla bean', 'musks']
    """
    if not isinstance(raw_notes, str):
        return []

    parts = [p.strip() for p in raw_notes.split(",") if p.strip()]
    return parts


def build_info_html(row) -> str:
    """Construye un bloque HTML bonito con la info del perfume."""
    name = row["Name"]
    brand = row["Brand"]
    desc = row.get("Description", "").strip()
    notes = parse_notes(row.get("Notes", ""))
    image_url = row.get("Image URL", "")

    # Cortar descripción si es larguísima (opcional)
    max_len = 700
    if len(desc) > max_len:
        desc_short = desc[:max_len].rsplit(" ", 1)[0] + "..."
    else:
        desc_short = desc

    notes_html = ""
    if notes:
        notes_html = "<ul>" + "".join(f"<li>{n}</li>" for n in notes) + "</ul>"

    html = f"""
    <div style="font-family: system-ui; max-width: 700px;">
      <h2 style="margin-bottom: 4px;">{name}</h2>
      <h3 style="margin-top: 0; font-weight: 400; color: #555;">{brand}</h3>

      <p style="line-height:1.5; text-align:justify;">{desc_short}</p>

      <h4>Notes</h4>
      {notes_html}
    </div>
    """

    return html, image_url


def get_perfume_info(name: str):
    """
    Devuelve un diccionario con:
    - name
    - brand
    - html (descripcion + notas)
    - image_url
    """
    row = find_perfume_row(name)
    if row is None:
        return None

    html, image_url = build_info_html(row)

    info = {
        "name": row["Name"],
        "brand": row["Brand"],
        "html": html,
        "image_url": image_url,
    }
    return info