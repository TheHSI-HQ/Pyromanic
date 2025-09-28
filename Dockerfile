FROM python:3.14.0rc2-alpine3.22 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update && apk add --no-cache gcc libffi-dev

RUN mkdir /install

COPY --chown=pyromanic:pyromanic requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade --prefix=/install -r requirements.txt



FROM python:3.14.0rc2-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.13/site-packages"

WORKDIR /app

RUN useradd -m pyromanic

COPY --from=builder /install /install
COPY --chown=pyromanic:pyromanic . .

RUN chown -R pyromanic:pyromanic /app

USER pyromanic

CMD ["python", "./app.py"]