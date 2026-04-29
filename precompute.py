"""
Script de pre-cómputo — se ejecuta UNA VEZ durante el build de Docker.
Guarda posiciones, centralidad, colaboraciones inter-institucionales
y resúmenes en CSVs para que Mercury solo cargue y grafique.
"""
import pandas as pd
import networkx as nx
import os

print("=" * 60)
print("PRECOMPUTE — Generando datos para visualizaciones")
print("=" * 60)

# ── Cargar datos base ──────────────────────────────────────────
print("\n1. Cargando datos...")
df_nodos   = pd.read_csv("data/clean/nodos_autores.csv")
df_aristas = pd.read_csv("data/clean/aristas_colaboraciones.csv")
df_autorias = pd.read_csv("data/clean/autorias_limpias.csv")

print(f"   Nodos: {len(df_nodos):,}")
print(f"   Aristas: {len(df_aristas):,}")
print(f"   Autorías: {len(df_autorias):,}")

# ── Construir grafo completo (sin filtro de artículos) ─────────
print("\n2. Construyendo grafo completo...")
G = nx.Graph()
for _, row in df_nodos.iterrows():
    G.add_node(row["autor_id"],
               nombre=row["nombre"],
               articulos=int(row["articulos"]),
               citas=int(row["citas_total"]),
               institucion=row["inst_principal"])
for _, row in df_aristas.iterrows():
    G.add_edge(row["source"], row["target"], weight=int(row["peso"]))

print(f"   Grafo completo: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

# ── Tomar los componentes más grandes para la red ──────────────
print("\n3. Seleccionando componentes para red de visualización...")
componentes = sorted(nx.connected_components(G), key=len, reverse=True)
print(f"   Total componentes: {len(componentes)}")
print(f"   Top 10 tamaños: {[len(c) for c in componentes[:10]]}")

# Tomar componentes con >= 10 nodos para tener una red interesante
nodos_seleccionados = set()
for comp in componentes:
    if len(comp) >= 10:
        nodos_seleccionados |= comp

# Si tenemos demasiados nodos, limitar a los más conectados
MAX_NODOS = 300
if len(nodos_seleccionados) > MAX_NODOS:
    G_sel = G.subgraph(nodos_seleccionados)
    top = sorted(G_sel.degree(), key=lambda x: x[1], reverse=True)[:MAX_NODOS]
    nodos_seleccionados = {n for n, _ in top}

G_sub = G.subgraph(nodos_seleccionados).copy()
print(f"   Subgrafo final: {G_sub.number_of_nodes()} nodos, {G_sub.number_of_edges()} aristas")

# ── Pre-computar posiciones ────────────────────────────────────
print("\n4. Calculando layout (spring)...")
pos = nx.spring_layout(G_sub, k=1.5, seed=42, iterations=100)
pos_df = pd.DataFrame([
    {"autor_id": n, "x": float(pos[n][0]), "y": float(pos[n][1])}
    for n in G_sub.nodes()
])
pos_df.to_csv("data/clean/posiciones.csv", index=False)
print(f"   ✓ Posiciones guardadas ({len(pos_df)} nodos)")

# ── Pre-computar centralidad ──────────────────────────────────
print("\n5. Calculando centralidad de intermediación...")
betweenness = nx.betweenness_centrality(G_sub, normalized=True)
degree = dict(G_sub.degree())

centralidad_df = pd.DataFrame([
    {
        "autor_id":    n,
        "nombre":      G_sub.nodes[n]["nombre"],
        "institucion": G_sub.nodes[n]["institucion"],
        "articulos":   G_sub.nodes[n]["articulos"],
        "citas":       G_sub.nodes[n]["citas"],
        "betweenness": round(betweenness[n], 6),
        "degree":      degree[n],
    }
    for n in G_sub.nodes()
]).sort_values("betweenness", ascending=False)
centralidad_df.to_csv("data/clean/centralidad.csv", index=False)
print(f"   ✓ Centralidad guardada ({len(centralidad_df)} investigadores)")
print(f"   Top 5 conectores:")
for _, r in centralidad_df.head(5).iterrows():
    print(f"     {r['nombre']:30s} betw={r['betweenness']:.4f}  inst={r['institucion'][:40]}")

# ── Guardar nodos y aristas del subgrafo ───────────────────────
print("\n6. Guardando subgrafo...")
nodos_sub = pd.DataFrame([
    {
        "autor_id":    n,
        "nombre":      G_sub.nodes[n]["nombre"],
        "institucion": G_sub.nodes[n]["institucion"],
        "articulos":   G_sub.nodes[n]["articulos"],
        "citas":       G_sub.nodes[n]["citas"],
    }
    for n in G_sub.nodes()
])
nodos_sub.to_csv("data/clean/nodos_sub.csv", index=False)

aristas_sub = pd.DataFrame([
    {"source": u, "target": v, "weight": G_sub.edges[u, v].get("weight", 1)}
    for u, v in G_sub.edges()
])
aristas_sub.to_csv("data/clean/aristas_sub.csv", index=False)
print(f"   ✓ Subgrafo: {len(nodos_sub)} nodos, {len(aristas_sub)} aristas")

# ── Colaboraciones inter-institucionales ───────────────────────
print("\n7. Calculando colaboraciones inter-institucionales...")
autor_inst = dict(zip(df_nodos["autor_id"], df_nodos["inst_principal"]))

inter_inst = []
for _, row in df_aristas.iterrows():
    inst_s = autor_inst.get(row["source"], "Desconocida")
    inst_t = autor_inst.get(row["target"], "Desconocida")
    if inst_s != inst_t and inst_s != "Desconocida" and inst_t != "Desconocida":
        i1, i2 = sorted([inst_s, inst_t])
        inter_inst.append({
            "inst_source": i1,
            "inst_target": i2,
            "peso": int(row["peso"]),
        })

df_inter = pd.DataFrame(inter_inst)
if len(df_inter) > 0:
    df_inter_agg = (
        df_inter
        .groupby(["inst_source", "inst_target"])
        .agg(total_colabs=("peso", "sum"), num_pares=("peso", "count"))
        .reset_index()
        .sort_values("total_colabs", ascending=False)
    )
    df_inter_agg.to_csv("data/clean/colabs_inter_inst.csv", index=False)
    print(f"   ✓ {len(df_inter_agg)} pares inter-institucionales guardados")

# ── Resumen por institución ────────────────────────────────────
print("\n8. Calculando resumen por institución...")
inst_summary = (
    df_nodos
    .groupby("inst_principal")
    .agg(
        num_investigadores=("autor_id", "count"),
        total_articulos=("articulos", "sum"),
        total_citas=("citas_total", "sum"),
        promedio_citas=("citas_total", "mean"),
    )
    .reset_index()
    .sort_values("num_investigadores", ascending=False)
)
inst_summary.to_csv("data/clean/resumen_instituciones.csv", index=False)
print(f"   ✓ Resumen de {len(inst_summary)} instituciones guardado")

# ── Evolución temporal por tipo de institución ─────────────────
print("\n9. Calculando evolución temporal...")
evol_tipo = (
    df_autorias
    .groupby(["anio", "inst_tipo"])
    .agg(publicaciones=("work_id", "nunique"), citas_promedio=("citas", "mean"))
    .reset_index()
)
evol_tipo.to_csv("data/clean/evolucion_tipo.csv", index=False)
print(f"   ✓ Evolución temporal guardada ({len(evol_tipo)} filas)")

evol_colabs = (
    df_aristas
    .groupby("primera_colab")
    .agg(nuevas_colabs=("peso", "count"), citas_promedio=("citas_max", "mean"))
    .reset_index()
    .rename(columns={"primera_colab": "anio"})
)
evol_colabs.to_csv("data/clean/evolucion_colabs.csv", index=False)
print(f"   ✓ Evolución de colaboraciones guardada")

print("\n" + "=" * 60)
print("PRE-CÓMPUTO COMPLETO")
print("=" * 60)
for f in sorted(os.listdir("data/clean")):
    size = os.path.getsize(f"data/clean/{f}")
    print(f"  {f:40s} {size:>10,} bytes")
