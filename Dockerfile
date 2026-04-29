FROM python:3.11-slim
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
 
RUN pip install --no-cache-dir mercury networkx plotly pandas requests tqdm
 
COPY . .
 
RUN mkdir -p data/clean && python precompute.py
 
EXPOSE 8888
 
CMD ["mercury", "--ip=0.0.0.0", "--no-browser", "--allow-root"]

