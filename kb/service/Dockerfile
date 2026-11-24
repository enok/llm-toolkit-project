FROM python:3.12-slim
RUN pip install --no-cache-dir chromadb==1.0.15 pypdf==5.4.0

WORKDIR /app
COPY kb_core.py store.py ingest.py service.py /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANONYMIZED_TELEMETRY=False

EXPOSE 8011
ENTRYPOINT ["python"]
CMD ["service.py"]
