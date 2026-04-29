---
title: Coautoria MX
emoji: 🔬
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8888
pinned: false
---

# Quién mueve los hilos de la ciencia mexicana

**Redes de coautoría científica en México 2018–2024**

Proyecto final — Visualización gráfica para IA · Dra. Dora Alvarado · Universidad Iberoamericana León

**Autor:** Pablo Villanueva — 194533-3

**Sitio en vivo:** [https://coautoria-mx.onrender.com](https://coautoria-mx.onrender.com)

---

## Descripción

Este proyecto construye una narrativa visual interactiva (data storytelling) que explora la red de coautoría científica en México. A partir de datos abiertos de OpenAlex, se analizan las conexiones entre investigadores mexicanos que publicaron artículos entre 2018 y 2024, respondiendo la pregunta: **quién conecta a quién en la ciencia mexicana, y qué instituciones sostienen esas redes.**

La aplicación web presenta 5 visualizaciones interactivas desplegadas con Mercury:

1. **Treemap de instituciones** — Las 15 instituciones con más investigadores, coloreadas por citas promedio por investigador.
2. **Evolución temporal** — Producción científica por año, segmentada por tipo de institución (universidades, gobierno, salud, etc.).
3. **Red de coautoría** — Grafo interactivo con 300 investigadores, donde cada línea es una co-firma de artículo.
4. **Impacto vs Producción** — Burbujas que relacionan artículos publicados, citas acumuladas y conexiones en la red.
5. **Mapa de calor inter-institucional** — Matriz que revela la intensidad de colaboración entre las 10 instituciones más conectadas.

---

## Fuente de datos

| Campo | Detalle |
|-------|---------|
| **Fuente** | [OpenAlex API](https://openalex.org/) |
| **URL base** | `https://api.openalex.org/works` |
| **Licencia** | CC0 — dominio público |
| **Fecha de descarga** | Registrada en `data/raw/metadata.json` |
| **Filtros** | País: MX, Años: 2018–2024, Tipo: article |
| **Volumen** | ~2,000 artículos → 3,671 autores → 10,636 pares de coautores |

---

## Estructura del repositorio

```
coautoria-mx/
├── fase1_extraccion_openalex.py   # Extracción y limpieza de datos (OpenAlex API)
├── fase2_visualizaciones_mercury.ipynb  # Notebook con las 5 visualizaciones (Mercury)
├── precompute.py                  # Pre-cómputo de grafos, centralidad y posiciones
├── data/
│   ├── raw/                       # Datos crudos (JSON de OpenAlex)
│   └── clean/                     # CSVs procesados para visualización
├── Dockerfile                     # Configuración de despliegue en Render
├── requirements.txt               # Dependencias de Python
├── jupyter_server_config.py       # Configuración del servidor Mercury
└── README.md
```

---

## Ejecución local

### Requisitos previos
- Python 3.11+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/coautoria-mx.git
cd coautoria-mx

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Regenerar datos desde OpenAlex
python fase1_extraccion_openalex.py

# 4. Pre-computar grafos y posiciones
python precompute.py

# 5. Lanzar Mercury
mercury run
```

La aplicación estará disponible en `http://localhost:8888`.

### Con Docker

```bash
docker build -t coautoria-mx .
docker run -p 8888:8888 coautoria-mx
```

---

## Tecnologías

- **Mercury** — Framework para convertir notebooks en aplicaciones web
- **Plotly** — Visualizaciones interactivas
- **NetworkX** — Análisis de grafos y centralidad
- **Pandas** — Manipulación de datos
- **OpenAlex API** — Fuente de datos académicos abiertos
- **Render** — Despliegue en la nube con Docker

---

## Licencia

Los datos provienen de OpenAlex bajo licencia CC0 (dominio público). El código de este proyecto es de uso académico.
