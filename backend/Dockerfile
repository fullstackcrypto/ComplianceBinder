FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app ./app
RUN python -c "from pathlib import Path; import base64, hashlib; script=Path('/app/app/static/app.js'); index=Path('/app/app/static/index.html'); integrity='sha384-'+base64.b64encode(hashlib.sha384(script.read_bytes()).digest()).decode('ascii'); text=index.read_text(encoding='utf-8'); assert '__APP_JS_INTEGRITY__' in text; index.write_text(text.replace('__APP_JS_INTEGRITY__', integrity), encoding='utf-8')" \
    && mkdir -p /app/uploads \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
