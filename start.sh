#!/bin/bash
cd /app

# Iniciar el worker de Celery en background
celery -A mercury.server worker -l info --concurrency=1 -P solo &

# Iniciar Mercury
mercury run fase2_visualizaciones_mercury.ipynb 0.0.0.0:7860
