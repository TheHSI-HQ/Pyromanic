FROM python:3.13.7-alpine3.22 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update && \
    apk add --no-cache gcc libffi-dev musl-dev postgresql-dev && \
    apk upgrade busybox

RUN mkdir /install

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade --prefix=/install -r requirements.txt

# ----------------------------

FROM python:3.13.7-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.14/site-packages"

WORKDIR /app

RUN apk add --no-cache libffi

RUN adduser -D -h /app pyromanic

COPY --from=builder /install /install
COPY --chown=pyromanic:pyromanic . .

RUN chown -R pyromanic:pyromanic /app

USER pyromanic

CMD ["python", "./app.py"]
