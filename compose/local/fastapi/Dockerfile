FROM python:3.12

WORKDIR /code

COPY ./compose/local/fastapi/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
