FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc supervisor && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir mercury==2.3.7 networkx plotly pandas requests tqdm

COPY . .

RUN mkdir -p data/clean

RUN python precompute.py

ENV ALLOWED_HOSTS="*"
ENV DJANGO_SETTINGS_MODULE="server.settings"
ENV MERCURY_SERVER_URL="https://pavoprro-coautoria-mx.hf.space"

COPY supervisord.conf /etc/supervisor/conf.d/mercury.conf

EXPOSE 7860

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
