FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
  git curl wget unzip \
  ffmpeg \
  libgl1-mesa-glx libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml

RUN pip install -U pip wheel && \
    pip install -e .

COPY . /app

EXPOSE 8080
CMD ["bash", "scripts/run_dev.sh"]
