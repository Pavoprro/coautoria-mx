FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir mercury networkx plotly pandas requests tqdm

COPY . .

RUN mkdir -p data/clean

# Correr precompute con salida visible para detectar errores
RUN python precompute.py || echo "PRECOMPUTE FAILED - check data files"

# Mercury 3.x usa JUPYTER_PORT para cambiar el puerto
ENV JUPYTER_PORT=7860

EXPOSE 7860

CMD ["mercury", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
