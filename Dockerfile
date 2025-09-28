FROM python:3.14.0rc2-alpine3.22 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apk add --no-cache gcc libffi-dev musl-dev

RUN mkdir /install

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade --prefix=/install -r requirements.txt

# ----------------------------

FROM python:3.14.0rc2-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.14/site-packages"

WORKDIR /app

# Add runtime dependencies if needed (optional)
RUN apk add --no-cache libffi postgresql-dev

# Create a non-root user
RUN adduser -D -h /app pyromanic

# Copy installed packages and app source
COPY --from=builder /install /install
COPY --chown=pyromanic:pyromanic . .

# Ensure ownership
RUN chown -R pyromanic:pyromanic /app

USER pyromanic

CMD ["python", "./app.py"]
