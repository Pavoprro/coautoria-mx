import requests
import pandas as pd
import json
import time
import os
from datetime import datetime
from tqdm import tqdm

EMAIL = "194533-3@iberoleon.edu.mx"
PAIS = "MX"
ANIO_INICIO = 2018
ANIO_FIN = 2024
MAX_RESULTADOS = 2000
POR_PAGINA = 200

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/clean", exist_ok=True)

print(f"Extrayendo trabajos {ANIO_INICIO}–{ANIO_FIN}, país: {PAIS}")


def extraer_trabajos_mexico(email, anio_inicio, anio_fin, max_resultados, por_pagina):
    """Consulta OpenAlex para obtener artículos con al menos un autor afiliado a México."""
    url_base = "https://api.openalex.org/works"
    headers = {"User-Agent": f"CoauthorshipProject/1.0 ({email})"}

    filtros = (
        f"institutions.country_code:{email.split('@')[1].split('.')[0].upper() if False else 'MX'},"
        f"publication_year:{anio_inicio}-{anio_fin},"
        f"type:article"
    )

    campos = "id,title,publication_year,cited_by_count,authorships,primary_location"

    trabajos = []
    cursor = "*"
    paginas_a_pedir = max_resultados // por_pagina

    print(f"Iniciando extracción: hasta {max_resultados} artículos...")

    for i in tqdm(range(paginas_a_pedir), desc="Páginas descargadas"):
        params = {
            "filter": filtros,
            "select": campos,
            "per-page": por_pagina,
            "cursor": cursor,
            "mailto": email,
            "sort": "cited_by_count:desc",
        }

        resp = requests.get(url_base, params=params, headers=headers)

        if resp.status_code != 200:
            print(f"Error en página {i+1}: {resp.status_code} — {resp.text[:200]}")
            break

        data = resp.json()
        resultados = data.get("results", [])

        if not resultados:
            print("Sin más resultados.")
            break

        trabajos.extend(resultados)
        cursor = data.get("meta", {}).get("next_cursor")

        if not cursor:
            print("Cursor agotado — todos los resultados descargados.")
            break

        time.sleep(0.12)

    return trabajos


trabajos_raw = extraer_trabajos_mexico(
    email=EMAIL,
    anio_inicio=ANIO_INICIO,
    anio_fin=ANIO_FIN,
    max_resultados=MAX_RESULTADOS,
    por_pagina=POR_PAGINA,
)

ruta_raw = "data/raw/trabajos_openalex_raw.json"
with open(ruta_raw, "w", encoding="utf-8") as f:
    json.dump(trabajos_raw, f, ensure_ascii=False, indent=2)

metadata = {
    "fuente": "OpenAlex API",
    "url_base": "https://api.openalex.org/works",
    "licencia": "CC0 — dominio público",
    "fecha_descarga": datetime.now().isoformat(),
    "filtros": {
        "pais": PAIS,
        "anio_inicio": ANIO_INICIO,
        "anio_fin": ANIO_FIN,
        "tipo": "article",
    },
    "total_registros_crudos": len(trabajos_raw),
}
with open("data/raw/metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"\n✓ {len(trabajos_raw)} artículos descargados → '{ruta_raw}'")


def parsear_autorias(trabajos_raw):
    """Extrae autores con afiliación mexicana de cada trabajo."""
    registros = []

    for trabajo in trabajos_raw:
        work_id = trabajo.get("id", "")
        titulo = trabajo.get("title", "Sin título")
        anio = trabajo.get("publication_year")
        citas = trabajo.get("cited_by_count", 0)

        for authorship in trabajo.get("authorships", []):
            autor = authorship.get("author", {})
            autor_id = autor.get("id", "")
            autor_nombre = autor.get("display_name", "Desconocido")

            instituciones_mx = []
            for inst in authorship.get("institutions", []):
                if inst.get("country_code") == "MX":
                    instituciones_mx.append({
                        "inst_id": inst.get("id", ""),
                        "inst_nombre": inst.get("display_name", ""),
                        "inst_tipo": inst.get("type", ""),
                    })

            if not instituciones_mx:
                continue

            for inst in instituciones_mx:
                registros.append({
                    "work_id": work_id,
                    "titulo": titulo,
                    "anio": anio,
                    "citas": citas,
                    "autor_id": autor_id,
                    "autor_nombre": autor_nombre,
                    "inst_id": inst["inst_id"],
                    "inst_nombre": inst["inst_nombre"],
                    "inst_tipo": inst["inst_tipo"],
                })

    return pd.DataFrame(registros)


df_autorias = parsear_autorias(trabajos_raw)
print(f"Tabla de autorías: {len(df_autorias):,} filas × {len(df_autorias.columns)} columnas")

# Limpieza
df_autorias = df_autorias[df_autorias["autor_id"].str.startswith("https://openalex.org/A")]
df_autorias = df_autorias.drop_duplicates(subset=["work_id", "autor_id", "inst_id"])
df_autorias["inst_nombre"] = (
    df_autorias["inst_nombre"]
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)
df_autorias = df_autorias.dropna(subset=["anio"])
df_autorias["anio"] = df_autorias["anio"].astype(int)
df_autorias = df_autorias[df_autorias["anio"].between(ANIO_INICIO, ANIO_FIN)]

print(f"Tras limpieza: {len(df_autorias):,} filas")
print(f"Artículos: {df_autorias['work_id'].nunique():,} | Autores: {df_autorias['autor_id'].nunique():,} | Instituciones: {df_autorias['inst_nombre'].nunique():,}")


def construir_red(df_autorias):
    """Construye nodos (autores) y aristas (pares de coautores) a partir de las autorías."""
    df_nodos = (
        df_autorias
        .groupby("autor_id")
        .agg(
            nombre=("autor_nombre", "first"),
            articulos=("work_id", "nunique"),
            citas_total=("citas", "sum"),
            inst_principal=("inst_nombre", lambda x: x.value_counts().index[0]),
        )
        .reset_index()
    )

    aristas = []
    for work_id, grupo in df_autorias.groupby("work_id"):
        autores = grupo["autor_id"].unique().tolist()
        anio = grupo["anio"].iloc[0]
        citas = grupo["citas"].iloc[0]

        if len(autores) < 2:
            continue

        for i in range(len(autores)):
            for j in range(i + 1, len(autores)):
                src, tgt = sorted([autores[i], autores[j]])
                aristas.append({
                    "source": src,
                    "target": tgt,
                    "work_id": work_id,
                    "anio": anio,
                    "citas": citas,
                })

    df_aristas_raw = pd.DataFrame(aristas)

    df_aristas = (
        df_aristas_raw
        .groupby(["source", "target"])
        .agg(
            peso=("work_id", "count"),
            citas_max=("citas", "max"),
            primera_colab=("anio", "min"),
            ultima_colab=("anio", "max"),
        )
        .reset_index()
    )

    return df_nodos, df_aristas


df_nodos, df_aristas = construir_red(df_autorias)
print(f"Red: {len(df_nodos):,} nodos, {len(df_aristas):,} aristas")

df_nodos.to_csv("data/clean/nodos_autores.csv", index=False, encoding="utf-8")
df_aristas.to_csv("data/clean/aristas_colaboraciones.csv", index=False, encoding="utf-8")
df_autorias.to_csv("data/clean/autorias_limpias.csv", index=False, encoding="utf-8")

print("✓ Datos guardados en data/clean/")
