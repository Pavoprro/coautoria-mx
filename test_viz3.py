import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Load Data
df_nodos      = pd.read_csv('data/clean/nodos_autores.csv')
df_aristas    = pd.read_csv('data/clean/aristas_colaboraciones.csv')
df_autorias   = pd.read_csv('data/clean/autorias_limpias.csv')
df_pos        = pd.read_csv('data/clean/posiciones.csv')
df_central    = pd.read_csv('data/clean/centralidad.csv')
df_nodos_sub  = pd.read_csv('data/clean/nodos_sub.csv')
df_aristas_sub= pd.read_csv('data/clean/aristas_sub.csv')
df_inst       = pd.read_csv('data/clean/resumen_instituciones.csv')
df_inter      = pd.read_csv('data/clean/colabs_inter_inst.csv')
df_evol_tipo  = pd.read_csv('data/clean/evolucion_tipo.csv')
df_evol_colab = pd.read_csv('data/clean/evolucion_colabs.csv')

BG = '#0d1117'
CARD = '#161b22'
TEXT = '#e6edf3'
GRID = '#21262d'
ACCENT1 = '#8b5cf6'
ACCENT2 = '#3b82f6'
ACCENT3 = '#06b6d4'
ACCENT4 = '#10b981'
ACCENT5 = '#f59e0b'
ACCENT6 = '#ef4444'
ACCENT7 = '#ec4899'
PALETTE = [ACCENT1, ACCENT2, ACCENT3, ACCENT4, ACCENT5, ACCENT6, ACCENT7, '#6366f1', '#14b8a6', '#f97316']

class MockSlider:
    def __init__(self, value):
        self.value = value

min_arts = MockSlider(1)
min_degree = MockSlider(0)

# Preparar datos base
df_plot = df_nodos_sub.merge(df_pos, on='autor_id')
df_plot = df_plot.merge(
    df_central[['autor_id', 'degree', 'betweenness']], on='autor_id', how='left'
)
df_plot['degree'] = df_plot['degree'].fillna(1)

# Aplicar filtros de los sliders
df_plot = df_plot[(df_plot['articulos'] >= min_arts.value) & (df_plot['degree'] >= min_degree.value)]

top_inst = df_plot['institucion'].value_counts().head(8).index.tolist()
inst_color_map = {inst: PALETTE[i] for i, inst in enumerate(top_inst)}
df_plot['color'] = df_plot['institucion'].map(inst_color_map).fillna('#444444')
df_plot['inst_short'] = df_plot['institucion'].apply(lambda x: x[:40] + '...' if len(str(x)) > 40 else x)

# Filtrar aristas: solo las que conecten nodos visibles
visible_ids = set(df_plot['autor_id'])
df_aristas_filt = df_aristas_sub[
    df_aristas_sub['source'].isin(visible_ids) & df_aristas_sub['target'].isin(visible_ids)
]

df_e = df_aristas_filt.merge(
    df_pos.rename(columns={'autor_id':'source','x':'x0','y':'y0'}), on='source')
df_e = df_e.merge(
    df_pos.rename(columns={'autor_id':'target','x':'x1','y':'y1'}), on='target')

edge_x, edge_y = [], []
for _, r in df_e.iterrows():
    edge_x += [r.x0, r.x1, None]
    edge_y += [r.y0, r.y1, None]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=edge_x, y=edge_y, mode='lines',
    line=dict(width=0.3, color='rgba(139,92,246,0.28)'),
    hoverinfo='none', showlegend=False,
))
fig3.add_trace(go.Scatter(
    x=df_plot['x'], y=df_plot['y'], mode='markers',
    marker=dict(
        size=[max(3, min(14, d**0.7 * 2)) for d in df_plot['degree']],
        color=df_plot['color'],
        opacity=0.9,
        line=dict(width=0.3, color='rgba(255,255,255,0.3)'),
    ),
    text=['<b>' + str(n) + '</b><br>' + str(i) + '<br>' + str(a) + ' arts / ' + str(c) + ' citas / ' + str(int(d)) + ' colabs'
          for n, i, a, c, d in zip(df_plot['nombre'], df_plot['inst_short'], df_plot['articulos'], df_plot['citas'], df_plot['degree'])],
    hovertemplate='%{text}<extra></extra>',
    showlegend=False,
))
fig3.update_layout(
    height=600,
    title=f'Red de coautoría — {len(df_plot)} investigadores (filtro: ≥{min_arts.value} arts, ≥{min_degree.value} colabs)',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
    plot_bgcolor=BG,
)
fig3.write_html('test_plot.html')
print("Graph generated successfully.")
