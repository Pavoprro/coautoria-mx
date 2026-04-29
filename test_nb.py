import mercury as mr
app = mr.App(
    title='Quién mueve los hilos de la ciencia mexicana',
    description='Redes de coautoría científica en México 2018-2024',
    show_code=False
)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

dark_template = go.layout.Template()
dark_template.layout = go.Layout(
    paper_bgcolor=BG,
    plot_bgcolor=CARD,
    font=dict(color=TEXT, family='Inter, system-ui, sans-serif'),
    title=dict(font=dict(size=18, color=TEXT)),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
    colorway=PALETTE,
    margin=dict(l=40, r=40, t=60, b=40),
)
from IPython.display import HTML
HTML('''
<style>
body, .jp-Notebook, .mercury-app, .mercury-notebook,
#root, .main-content, .container, .container-fluid,
.card, .card-body, .notebook-container,
.jp-Cell, .jp-MarkdownCell, .jp-OutputArea,
div[class*="mercury"], div[class*="notebook"] {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
.navbar, nav, header {
    background-color: #161b22 !important;
    border-bottom: 1px solid #21262d !important;
}
h1, h2, h3, h4, h5, h6, p, li, span, a, label, td, th {
    color: #e6edf3 !important;
}
h1 { color: #c4b5fd !important; }
h2 { color: #a78bfa !important; }
hr { border-color: #21262d !important; }
a { color: #8b5cf6 !important; }
strong, b { color: #c4b5fd !important; }
em, i { color: #9ca3af !important; }
.sidebar, .side-panel, div[class*="sidebar"] {
    background-color: #161b22 !important;
}
</style>
''')
n_inv = len(df_nodos)
n_colabs = len(df_aristas)
n_inst = df_nodos['inst_principal'].nunique()
n_works = df_autorias['work_id'].nunique()

fig_stats = go.Figure()
vals = [n_inv, n_works, n_colabs, n_inst]
labels = ['Investigadores', 'Artículos', 'Pares de coautores', 'Instituciones']
colors = [ACCENT1, ACCENT2, ACCENT3, ACCENT4]

for i, (v, l, c) in enumerate(zip(vals, labels, colors)):
    fig_stats.add_trace(go.Indicator(
        mode='number',
        value=v,
        title=dict(text=l, font=dict(size=14, color=TEXT)),
        number=dict(font=dict(size=36, color=c)),
        domain=dict(x=[i/4, (i+1)/4], y=[0, 1]),
    ))
fig_stats.update_layout(
    template=dark_template, height=120,
    margin=dict(l=10, r=10, t=10, b=10),
)
fig_stats.show()
top15 = df_inst.head(15).copy()
top15['nombre_corto'] = top15['inst_principal'].apply(
    lambda x: x[:35] + '...' if len(str(x)) > 35 else x
)
top15['label'] = top15.apply(
    lambda r: f"{r['nombre_corto']}<br>{r['num_investigadores']} inv. / ~{r['promedio_citas']:.0f} citas prom. por inv.", axis=1
)

fig1 = px.treemap(
    top15,
    path=['label'],
    values='num_investigadores',
    color='promedio_citas',
    color_continuous_scale=[[0, '#1e1b4b'], [0.5, ACCENT1], [1, '#c4b5fd']],
    hover_data={'total_articulos': True, 'total_citas': True, 'promedio_citas': ':.0f'},
)
fig1.update_layout(
    template=dark_template, height=500,
    title='Top 15 instituciones por número de investigadores',
    coloraxis_colorbar=dict(title='Citas prom.<br>por inv.', tickfont=dict(color=TEXT)),
    margin=dict(l=10, r=10, t=60, b=10),
)
fig1.update_traces(
    textfont=dict(color='white', size=11),
    marker=dict(cornerradius=5),
)
fig1.show()
tipo_labels = {
    'education': 'Universidades',
    'facility': 'Centros de inv.',
    'government': 'Gobierno',
    'nonprofit': 'Sin fines de lucro',
    'healthcare': 'Salud',
    'company': 'Empresas',
    'funder': 'Fondos',
    'other': 'Otros',
    'archive': 'Archivos',
}
df_ev = df_evol_tipo.copy()
df_ev['tipo_es'] = df_ev['inst_tipo'].map(tipo_labels).fillna(df_ev['inst_tipo'])

fig2 = px.area(
    df_ev, x='anio', y='publicaciones', color='tipo_es',
    labels={'anio': 'Año', 'publicaciones': 'Publicaciones', 'tipo_es': 'Tipo'},
    title='Producción científica por tipo de institución',
    color_discrete_sequence=PALETTE,
)
fig2.update_layout(
    template=dark_template, height=420,
    xaxis=dict(tickmode='linear', dtick=1),
    legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center', font=dict(size=11)),
)
fig2.update_traces(line=dict(width=0.5))
fig2.show()
min_arts = mr.Slider(value=1, min=1, max=18, step=1, label='Filtrar por artículos mínimos')
min_degree = mr.Slider(value=0, min=0, max=50, step=5, label='Filtrar por colaboraciones mínimas (degree)')
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
    template=dark_template, height=600,
    title=f'Red de coautoría — {len(df_plot)} investigadores (filtro: ≥{min_arts.value} arts, ≥{min_degree.value} colabs)',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
    plot_bgcolor=BG,
)
fig3.show()
top10_bridge = df_central.nlargest(10, 'betweenness').copy()
top10_bridge['nombre_corto'] = top10_bridge['nombre'].apply(
    lambda x: x[:30] + '...' if len(str(x)) > 30 else x
)
top10_bridge['inst_short'] = top10_bridge['institucion'].apply(
    lambda x: x[:35] + '...' if len(str(x)) > 35 else x
)
top10_bridge = top10_bridge.sort_values('betweenness', ascending=True)

bridge_inst = top10_bridge['inst_short'].unique().tolist()
bridge_color_map = {inst: PALETTE[i % len(PALETTE)] for i, inst in enumerate(bridge_inst)}
top10_bridge['color'] = top10_bridge['inst_short'].map(bridge_color_map)

fig3b = go.Figure()
for inst in bridge_inst:
    mask = top10_bridge['inst_short'] == inst
    subset = top10_bridge[mask]
    fig3b.add_trace(go.Bar(
        y=subset['nombre_corto'],
        x=subset['betweenness'],
        orientation='h',
        name=inst,
        marker=dict(color=bridge_color_map[inst], line=dict(width=0)),
        text=[f'{v:.4f}' for v in subset['betweenness']],
        textposition='outside',
        textfont=dict(color=TEXT, size=10),
        hovertemplate='<b>%{y}</b><br>' + inst + '<br>Betweenness: %{x:.4f}<extra></extra>',
    ))

fig3b.update_layout(
    template=dark_template, height=480,
    title='Top 10 Investigadores Puente — Centralidad de intermediación',
    xaxis=dict(title='Betweenness Centrality', showgrid=True, gridcolor=GRID),
    yaxis=dict(title=''),
    barmode='stack',
    legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center', font=dict(size=10)),
    margin=dict(l=180, r=60, t=60, b=80),
)
fig3b.show()
top80 = df_central.head(80).copy()

fig4 = px.scatter(
    top80,
    x='articulos', y='citas',
    size='degree', color='institucion',
    hover_name='nombre',
    hover_data={'betweenness': ':.4f', 'degree': True},
    labels={'articulos': 'Artículos publicados', 'citas': 'Citas acumuladas',
            'degree': 'Conexiones', 'institucion': 'Institución'},
    title='Impacto vs Producción — Top 80 investigadores más conectados',
    color_discrete_sequence=PALETTE,
    size_max=30,
)

for _, row in top80.head(5).iterrows():
    apellido = str(row['nombre']).split()[-1] if pd.notna(row['nombre']) else ''
    fig4.add_annotation(
        x=row['articulos'], y=row['citas'],
        text=apellido, showarrow=True, arrowhead=2,
        font=dict(size=10, color=TEXT),
        arrowcolor='#555',
    )

fig4.update_layout(
    template=dark_template, height=520,
    legend=dict(font=dict(size=9), y=0.5),
)
fig4.show()
top_inst_colabs = (
    df_inter.melt(id_vars=['total_colabs'], value_vars=['inst_source','inst_target'], value_name='inst')
    .groupby('inst')['total_colabs'].sum()
    .sort_values(ascending=False)
    .head(10).index.tolist()
)

short_names = {n: (n[:25] + '...' if len(n) > 25 else n) for n in top_inst_colabs}
full_ordered = top_inst_colabs  # nombres completos
labels_ordered = [short_names[n] for n in top_inst_colabs]

matrix = pd.DataFrame(0, index=labels_ordered, columns=labels_ordered)
for _, r in df_inter.iterrows():
    if r['inst_source'] in top_inst_colabs and r['inst_target'] in top_inst_colabs:
        s = short_names[r['inst_source']]
        t = short_names[r['inst_target']]
        matrix.loc[s, t] = r['total_colabs']
        matrix.loc[t, s] = r['total_colabs']

# Crear customdata con nombres completos para el hover
hover_text = []
for i in range(len(full_ordered)):
    row_hover = []
    for j in range(len(full_ordered)):
        row_hover.append(full_ordered[i] + '  x  ' + full_ordered[j])
    hover_text.append(row_hover)

fig5 = go.Figure(go.Heatmap(
    z=matrix.values,
    x=labels_ordered,
    y=labels_ordered,
    colorscale=[[0, '#0d1117'], [0.15, '#1e1b4b'], [0.4, '#5b21b6'], [0.7, '#8b5cf6'], [1, '#c4b5fd']],
    customdata=hover_text,
    hovertemplate='<b>%{customdata}</b><br>Colaboraciones: %{z}<extra></extra>',
    showscale=True,
    colorbar=dict(title='Colaboraciones', tickfont=dict(color=TEXT)),
))

for i in range(len(labels_ordered)):
    for j in range(len(labels_ordered)):
        val = matrix.values[i][j]
        if val > 0:
            fig5.add_annotation(
                x=labels_ordered[j], y=labels_ordered[i],
                text=str(int(val)), showarrow=False,
                font=dict(size=9, color='white' if val > matrix.values.max()*0.3 else '#888'),
            )

fig5.update_layout(
    template=dark_template, height=550,
    title='Intensidad de colaboración inter-institucional',
    xaxis=dict(tickangle=45, tickfont=dict(size=9)),
    yaxis=dict(tickfont=dict(size=9), autorange='reversed'),
    margin=dict(l=160, b=140, t=60, r=40),
)
fig5.show()