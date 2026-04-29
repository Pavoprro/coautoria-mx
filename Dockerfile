FROM python:3.11-slim
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
 
RUN pip install --no-cache-dir mercury networkx plotly pandas requests tqdm
 
COPY . .
 
RUN mkdir -p data/clean && python precompute.py
 
# Copiar config de Jupyter al lugar donde Mercury la lee
RUN mkdir -p /root/.jupyter
COPY jupyter_server_config.py /root/.jupyter/jupyter_server_config.py
 
EXPOSE 8888
 
CMD ["mercury"]
 