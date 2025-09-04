import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.db import get_session
from app.graphql import get_graphql_client
from app.models import Call, TwilioCall, TwilioCallEvent
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # 🔑 mantém o banco in-memory compartilhado
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    # Override da dependência
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_graphql_client():
    """Cria um mock do GraphQL client e sobrescreve a dependency"""
    mock_client = AsyncMock()
    mock_client.execute_async.return_value = {"data": "ok"}

    async def mock_get_graphql_client():
        yield mock_client

    # Sobrescreve a dependency
    app.dependency_overrides[get_graphql_client] = mock_get_graphql_client

    yield mock_client  # disponibiliza o mock para inspeção nos testes

    # Limpa override depois do teste
    app.dependency_overrides = {}
