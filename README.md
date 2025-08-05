# bonde-actions-api

## Desenvolvimento

Crie um arquivo `.env` conforme o arquivo `example.env`.

Rode o projeto utilizando [Docker Compose](https://docs.docker.com/compose/).

```bash
docker compose up
```

## Estrutura do banco de dados

```sql
CREATE TABLE twilio_call (
    call_sid TEXT PRIMARY KEY,
    widget_id INT NOT NULL,
    action_id INT,
    activist_number TEXT NOT NULL,
    target_number TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE twilio_call_event (
    id SERIAL PRIMARY KEY,
    call_sid TEXT NOT NULL REFERENCES twilio_call(call_sid),
    call_status TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx__twilio_call_event__call_sid ON twilio_call_event(call_sid);
```
