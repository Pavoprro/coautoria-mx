"""
Script de pre-cómputo — se ejecuta UNA VEZ durante el build de Docker.
Guarda posiciones y centralidad en CSVs para que Mercury solo cargue y grafique.
"""
import pandas as pd
import networkx as nx
import json, os

print("Cargando datos...")
df_nodos   = pd.read_csv("data/clean/nodos_autores.csv")
df_aristas = pd.read_csv("data/clean/aristas_colaboraciones.csv")

# Filtro base: autores con >= 3 artículos
df_n = df_nodos[df_nodos["articulos"] >= 3].copy()
df_a = df_aristas[
    df_aristas["source"].isin(df_n["autor_id"]) &
    df_aristas["target"].isin(df_n["autor_id"])
].copy()

print(f"Construyendo grafo: {len(df_n)} nodos, {len(df_a)} aristas...")
G = nx.Graph()
for _, row in df_n.iterrows():
    G.add_node(row["autor_id"],
               nombre=row["nombre"],
               articulos=int(row["articulos"]),
               citas=int(row["citas_total"]),
               institucion=row["inst_principal"])
for _, row in df_a.iterrows():
    G.add_edge(row["source"], row["target"], weight=int(row["peso"]))

# Solo componente gigante
componentes = sorted(nx.connected_components(G), key=len, reverse=True)
G_giant = G.subgraph(componentes[0]).copy()
print(f"Componente gigante: {G_giant.number_of_nodes()} nodos")

# Limitar a 400 nodos para performance (los más conectados)
top_nodos = sorted(G_giant.degree(), key=lambda x: x[1], reverse=True)[:400]
top_ids = [n for n, _ in top_nodos]
G_sub = G_giant.subgraph(top_ids).copy()
print(f"Subgrafo para visualización: {G_sub.number_of_nodes()} nodos")

# Pre-computar posiciones
print("Calculando layout...")
pos = nx.spring_layout(G_sub, k=0.8, seed=42)
pos_df = pd.DataFrame([
    {"autor_id": n, "x": float(pos[n][0]), "y": float(pos[n][1])}
    for n in G_sub.nodes()
])
pos_df.to_csv("data/clean/posiciones.csv", index=False)
print("✓ Posiciones guardadas")

# Pre-computar centralidad
print("Calculando centralidad (esto puede tardar 1-2 min)...")
betweenness = nx.betweenness_centrality(G_sub, normalized=True)
degree      = dict(G_sub.degree())

centralidad_df = pd.DataFrame([
    {
        "autor_id":    n,
        "nombre":      G_sub.nodes[n]["nombre"],
        "institucion": G_sub.nodes[n]["institucion"],
        "articulos":   G_sub.nodes[n]["articulos"],
        "citas":       G_sub.nodes[n]["citas"],
        "betweenness": betweenness[n],
        "degree":      degree[n],
    }
    for n in G_sub.nodes()
]).sort_values("betweenness", ascending=False)
centralidad_df.to_csv("data/clean/centralidad.csv", index=False)
print("✓ Centralidad guardada")

# Guardar lista de nodos y aristas del subgrafo
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
    {"source": u, "target": v}
    for u, v in G_sub.edges()
])
aristas_sub.to_csv("data/clean/aristas_sub.csv", index=False)
print("✓ Subgrafo guardado")
print("\nPre-cómputo completo.")
