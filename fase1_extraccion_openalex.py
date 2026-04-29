# =============================================================================
# PROYECTO FINAL — Redes de coautoría científica en México
# Visualización gráfica para IA · Dra. Dora Alvarado · Ibero León
#
# FASE 1: Extracción y limpieza de datos
# Fuente: OpenAlex API (https://openalex.org/)
# Sin llave de API requerida — solo email de contacto como parámetro de cortesía
# Fecha de descarga: registrada automáticamente en metadata.json
# Licencia de datos: CC0 (dominio público)
# =============================================================================


# ── CELDA 1: Instalación de dependencias ─────────────────────────────────────
# Ejecutar solo una vez. Luego reiniciar el kernel si es necesario.

# !pip install requests pandas networkx plotly pyvis tqdm


# ── CELDA 2: Importaciones y configuración ────────────────────────────────────

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime
from tqdm import tqdm  # barra de progreso opcional

# Reemplaza con tu email — OpenAlex lo usa para darte acceso al pool "polite"
# (respuestas más rápidas). Nunca se comparte públicamente.
EMAIL = "194533-3@iberoleon.edu.mx"

# Parámetros de la consulta
PAIS = "MX"                # Código ISO del país
ANIO_INICIO = 2018
ANIO_FIN = 2024
MAX_RESULTADOS = 2000      # OpenAlex permite hasta 10,000 por query, ajusta según RAM
POR_PAGINA = 200           # Máximo permitido por la API

# Directorio de datos
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/clean", exist_ok=True)

print(f"Configuración lista. Extrayendo trabajos {ANIO_INICIO}–{ANIO_FIN}, país: {PAIS}")


# ── CELDA 3: Función de extracción desde OpenAlex ─────────────────────────────
# Documentación oficial: https://docs.openalex.org/api-entities/works

def extraer_trabajos_mexico(email, anio_inicio, anio_fin, max_resultados, por_pagina):
    """
    Consulta la API de OpenAlex para obtener artículos con al menos
    un autor afiliado a una institución mexicana.

    Retorna una lista de dicts con los campos relevantes para construir
    la red de coautoría.
    """
    url_base = "https://api.openalex.org/works"
    headers = {"User-Agent": f"CoauthorshipProject/1.0 ({email})"}

    # Filtros: país de la institución + rango de años + tipo artículo
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

        time.sleep(0.12)  # Cortesía con la API: ~8 req/seg máximo

    return trabajos


# ── CELDA 4: Ejecutar extracción y guardar raw ────────────────────────────────

trabajos_raw = extraer_trabajos_mexico(
    email=EMAIL,
    anio_inicio=ANIO_INICIO,
    anio_fin=ANIO_FIN,
    max_resultados=MAX_RESULTADOS,
    por_pagina=POR_PAGINA,
)

# Guardar JSON crudo (para reproducibilidad: cualquiera que clone el repo
# puede verificar los datos de origen antes del procesamiento)
ruta_raw = "data/raw/trabajos_openalex_raw.json"
with open(ruta_raw, "w", encoding="utf-8") as f:
    json.dump(trabajos_raw, f, ensure_ascii=False, indent=2)

# Registrar metadatos de descarga
metadata = {
    "fuente": "OpenAlex API",
    "url_base": "https://api.openalex.org/works",
    "licencia": "CC0 — dominio público (https://creativecommons.org/publicdomain/zero/1.0/)",
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

print(f"\n✓ {len(trabajos_raw)} artículos descargados → guardados en '{ruta_raw}'")
print(f"✓ Metadatos en 'data/raw/metadata.json'")


# ── CELDA 5: Parseo — construir tabla plana de autorías ───────────────────────
# Cada fila = un autor en un artículo. Múltiples autores = múltiples filas.

def parsear_autorias(trabajos_raw):
    """
    Extrae de cada trabajo la lista de autores con sus instituciones.
    Filtra solo los autores con al menos una afiliación mexicana conocida.
    """
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

            # Iterar sobre instituciones del autor en este trabajo
            instituciones_mx = []
            for inst in authorship.get("institutions", []):
                if inst.get("country_code") == "MX":
                    instituciones_mx.append({
                        "inst_id": inst.get("id", ""),
                        "inst_nombre": inst.get("display_name", ""),
                        "inst_tipo": inst.get("type", ""),
                    })

            # Solo nos interesan autores con afiliación MX confirmada
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
df_autorias.head(3)


# ── CELDA 6: Limpieza y normalización ─────────────────────────────────────────

# 1. Eliminar filas sin autor_id válido
df_autorias = df_autorias[df_autorias["autor_id"].str.startswith("https://openalex.org/A")]
print(f"Tras filtrar IDs inválidos: {len(df_autorias):,} filas")

# 2. Eliminar duplicados exactos (mismo autor, mismo trabajo, misma institución)
df_autorias = df_autorias.drop_duplicates(subset=["work_id", "autor_id", "inst_id"])
print(f"Tras eliminar duplicados: {len(df_autorias):,} filas")

# 3. Normalizar nombres de instituciones
#    OpenAlex a veces registra variaciones del mismo nombre
df_autorias["inst_nombre"] = (
    df_autorias["inst_nombre"]
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

# 4. Eliminar registros sin año válido
df_autorias = df_autorias.dropna(subset=["anio"])
df_autorias["anio"] = df_autorias["anio"].astype(int)
df_autorias = df_autorias[df_autorias["anio"].between(ANIO_INICIO, ANIO_FIN)]
print(f"Tras filtrar años: {len(df_autorias):,} filas")

# 5. Resumen de calidad
print(f"\n--- Resumen de calidad ---")
print(f"Artículos únicos:      {df_autorias['work_id'].nunique():,}")
print(f"Autores únicos (MX):   {df_autorias['autor_id'].nunique():,}")
print(f"Instituciones únicas:  {df_autorias['inst_nombre'].nunique():,}")
print(f"Top 5 instituciones:")
print(df_autorias["inst_nombre"].value_counts().head(5))


# ── CELDA 7: Construir nodos y aristas para la red ────────────────────────────

def construir_red(df_autorias):
    """
    A partir de la tabla de autorías construye:
    - df_nodos: un autor = un nodo, con atributos agregados
    - df_aristas: par de autores que comparten al menos un artículo = arista

    El peso de la arista = número de artículos en coautoría.
    """
    # ── Nodos ──────────────────────────────────────────────────────────────
    # Atributos por autor: institución principal (la más frecuente),
    # total de artículos, total de citas acumuladas
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

    # ── Aristas ────────────────────────────────────────────────────────────
    # Para cada artículo, hacer el producto cartesiano de sus autores MX
    aristas = []
    for work_id, grupo in df_autorias.groupby("work_id"):
        autores = grupo["autor_id"].unique().tolist()
        anio = grupo["anio"].iloc[0]
        citas = grupo["citas"].iloc[0]

        # Solo considerar artículos con 2+ autores MX (coautoría)
        if len(autores) < 2:
            continue

        for i in range(len(autores)):
            for j in range(i + 1, len(autores)):
                # Ordenar para que (A,B) y (B,A) sean la misma arista
                src, tgt = sorted([autores[i], autores[j]])
                aristas.append({
                    "source": src,
                    "target": tgt,
                    "work_id": work_id,
                    "anio": anio,
                    "citas": citas,
                })

    df_aristas_raw = pd.DataFrame(aristas)

    # Agregar: peso = número de colaboraciones
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

print(f"Red construida:")
print(f"  Nodos (autores):   {len(df_nodos):,}")
print(f"  Aristas (colabs):  {len(df_aristas):,}")
print(f"  Densidad estimada: {len(df_aristas) / (len(df_nodos)*(len(df_nodos)-1)/2):.6f}")


# ── CELDA 8: Guardar datos limpios ────────────────────────────────────────────

df_nodos.to_csv("data/clean/nodos_autores.csv", index=False, encoding="utf-8")
df_aristas.to_csv("data/clean/aristas_colaboraciones.csv", index=False, encoding="utf-8")
df_autorias.to_csv("data/clean/autorias_limpias.csv", index=False, encoding="utf-8")

print("✓ Datos limpios guardados en data/clean/")
print("  - nodos_autores.csv")
print("  - aristas_colaboraciones.csv")
print("  - autorias_limpias.csv")
print("\nLa Fase 1 está completa. Procede a fase2_visualizaciones.ipynb")
