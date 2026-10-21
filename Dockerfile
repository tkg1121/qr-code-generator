FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 myuser \
    && mkdir logs qr_codes \
    && chown myuser:myuser logs qr_codes

COPY main.py ./

USER myuser

ENTRYPOINT ["python", "main.py"]
CMD ["--url", "http://github.com/kaw393939"]
