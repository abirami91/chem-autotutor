# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

# System deps:
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless curl ca-certificates tini \
    libxrender1 libxext6 libsm6 libx11-6 libfreetype6 fontconfig \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Freeze Python deps so numpy<2 is guaranteed:
RUN printf '%s\n' \
  'numpy==1.26.4' \
  'rdkit-pypi==2022.9.5' \
  'jinja2>=3.1,<4' \
  'pillow>=9,<10' \
  > /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# App files
COPY build.py /app/build.py
COPY templates/ /app/templates/

# OPSIN (name -> SMILES): use the CLI jar from v2.8.0
# https://github.com/dan2097/opsin/releases
ARG OPSIN_VERSION=2.8.0
RUN curl -fL --retry 5 -o /app/opsin.jar \
  "https://github.com/dan2097/opsin/releases/download/${OPSIN_VERSION}/opsin-cli-${OPSIN_VERSION}-jar-with-dependencies.jar" \
  && test -s /app/opsin.jar

# Non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","/app/build.py","--help"]
