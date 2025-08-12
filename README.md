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

## Funcionamento da Chamada

### 📞 Chamada de Origem (quem inicia)
1. queued — Twilio recebeu a solicitação para iniciar a chamada.

2. initiated — Twilio começou a criar a ligação para o originador.

3. ringing — telefone do originador está tocando.

4. in-progress — originador atendeu, e Twilio está pronto para conectar ao destino.

5. (possível) bridged — se você usar <Dial> e conectar com outra chamada, pode aparecer como bridged nos eventos de webhook (Call Progress Events).

6. completed — chamada finalizada (pode ser normal ou abrupta).

### 📞 Chamada de Destino (quem recebe a ponte)
queued — Twilio colocou na fila a tentativa de ligar para o destino.

1. initiated — iniciou a chamada para o destino.

2. ringing — telefone do destino está tocando.

4. in-progress — destino atendeu, Twilio conectou as duas ligações.

5. completed — chamada encerrada.

IMPORTANTE: Quando o usuário declina a ligação e cai para caixa postal a ligação fica in-progress e ao final vai para completed.


// 'initiated': Ligação iniciada para o ativista.
// 'queued': Ligação iniciada para o ativista. (Primeira requisição, valor default salvo no banco)
// 'in-progress': Ligação do ativista conectada com a ligação com o alvo.
// 'completed': Ligação realizada com sucesso.
// 'canceled': Ligação interrompida ou instabilidade na rede.
// 'failed': Ligação para o alvo falhou.
// 'no-answer': Ligação para o alvo chamou e não obteve resposta.
// 'ringing': Ativista atendeu a ligação, iniciou-se a ligação para o alvo.
// 'busy': Número do alvo ocupado.