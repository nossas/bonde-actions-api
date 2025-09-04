# bonde-actions-api
API de táticas de Ações usadas no BONDE

# Visão Geral
Este projeto fornece uma API, desenvolvida com FastAPI, para orquestrar ações telefônicas através do serviço Twilio.
É parte da infraestrutura do BONDE para disparar chamadas automatizadas, enviar SMS e interagir via telefonia.

## Tecnologias Utilizadas
- Python 3.x
- FastAPI – Framework da API
- Alembic: Migrações de banco de dados
- uv: Gerenciador de ambientes e dependências Python
- Docker e docker-compose

## Estrutura do Projeto
```
.
├── src/
│   └── app/
│       ├── main.py             # Inicialização da API FastAPI
│       ├── api/
│           └── routers/        # Endpoints (ex: chamadas, status)
│       ├── models.py           # Schemas Pydantic e models ORM
│       └── db.py               # Configuração e migrações Alembic
├── migrations/                 # Arquivos de migração
├── pyproject.toml / uv.lock    # Dependências gerenciadas pelo uv
├── .python-version
├── LICENSE
└── README.md
```

## Instalação e Execução
### Resuisitos
- Docker compose
- Python 3.x + uv instalado globalmente

### Passo a passo
```bash
# Clone o projeto
git clone https://github.com/nossas/bonde-actions-api.git
cd bonde-actions-api

# Instalação do uv globalmente (macOS and Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Instalação do uv globalmente (macOS com Homebrew)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Instalação do uv globalmente (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Instalação do uv usando PyPI
pip install uv

# Instale dependências com uv
uv sync

# Suba o ambiente com Docker
docker-compose up --build
```

## Pressão por Telefone

Conectar 2 números de telefone, Ativista e Alvo para realizar uma tática de Pressão.

Passo 1: Ligar para o Ativista e conectá-lo a uma conferência quando a ligação for atendida
Passo 2: Ao conectar o Ativista a conferência, adicionar o Alvo a conferência
Passo 3: Acompanhar o status da chamada e da conferência

### Acompanhamento da ligação

Ligar para um ativista requer fazer um redirecionamento, esse redirecionamento da ligação possui um ciclo que pode ser acompanhado pela API do Twilio, mas que representam através de combinações um status para acompanhar seu ciclo. Ou seja redirecionar ligações é uma das coisas que o Twilio pode fazer. Vamos discutir como decidimos implementar esse ciclo para funcionar na tática de Pressão por Telefone.

Primeiro passo, é iniciar uma ligação para o Ativista, nesse momento podemos configurar alguma mensagem e logo após redirecionamos o resultado da ligação para um URL de instruções no formato Twiml do que fazer:

```python
client = client.calls.create(
    to=activist_number,
    from_=settings.twilio_phone_number,
    url=f"{base_url}/call-redirect/{target_number}",
    method="POST"
)
```

Vamos precisar registrar essa ligação em local único, isso vai ser necessário para acompanhar em um ponto central as 2 ligação que vai acontecer, a primeira é para o Ativista e quando ele atende, se faz uma segunda ligação para o Alvo. Abaixo segue uma sugestão de modelagem:

```python
class PhoneCall(BaseModel):
    # Número do Ativista
    from_phone_number: str
    from_call_sid: str
    # Número do Alvo
    to_phone_number: str
    to_call_sid: str
    status: str
    created_at: timestamp

class TwilioCall(BaseModel):
    phone_call: PhoneCall
    sid: str
    status: str
    reason: str
    # Armazenamos os telefones para os números usados pelo Twilio
    from_phone_number: str
    to_phone_number: str
```