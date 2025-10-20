FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copie ton code et ton requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Optionnel : un healthcheck
# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Lance ton app Streamlit
ENTRYPOINT ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
