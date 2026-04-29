FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir mercury==2.3.7 networkx plotly pandas requests tqdm pyvis

COPY . .

EXPOSE 7860

CMD mercury run fase2_visualizaciones_mercury.ipynb --host 0.0.0.0 --port 7860
