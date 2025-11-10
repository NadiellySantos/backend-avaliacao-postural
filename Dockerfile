# Etapa base: Python oficial
FROM python:3.10-slim

# Evita perguntas durante o build
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema (necessárias para scipy e mediapipe)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libgtk2.0-dev \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta (mesma do seu app)
EXPOSE 8000

# Comando de execução (ajuste conforme seu app)
CMD ["python", "app.py"]
