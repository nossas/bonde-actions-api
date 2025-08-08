FROM python:3.12-slim

# Não gerar bytecode (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1
# Garantir que a saída do Python seja enviado diretamente para o terminal
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install --no-install-recommends -y curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./compose/local/fastapi/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]