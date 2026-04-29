FROM python:3.12-slim

RUN pip install mercury networkx plotly pandas requests tqdm

WORKDIR /workspace

COPY . /workspace

RUN python precompute.py

EXPOSE 7860

CMD ["mercury", "--ip=0.0.0.0", "--port=7860", "--no-browser", "--allow-root"]
