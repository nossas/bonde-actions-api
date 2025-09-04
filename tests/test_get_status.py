from app.models import Call
from app.enum import CallState

# busy: Não conseguimos completar a ligação porque o alvo estava ocupado
# canceled: A ligação foi interrompida - isso pode ter acontecido por instabilidade de rede ou encerramento da chamada
# completed: Obrigado por participar! Essa ligação ajuda a pressionar...
# failed: A ligação com o destino falhou - isso pode ter acontecido...
# initiated/queued: Atenda o telefone para continuar...
# in-progress: Agora é com você! Se quiser, pode usar este exemplo...
# no-answer: A chamada foi feita, mas não conseguimos contato com o alvo
# ringing: Você atendeu a nossa ligação! Agora estamos tentando falar com o alvo...

def make_call(**kwargs):
    values = {
        "from_number": "+5531998766543",
        "to_number": "+5531876234123",
        "state": CallState.INITIATED,
        **kwargs
    }
    return Call(**values)

def test_status_initiated(client, session):
    calls = [
        make_call(state=CallState.INITIATED),
        make_call(state=CallState.RINGING),
        make_call(state=CallState.ANSWERED),
    ]
    session.add_all(calls)
    session.commit()

    results = [
        client.get(f"/v1/phone/status/{call.id}").json()["status"]
        for call in calls
    ]

    assert results == ["initiated", "initiated", "initiated"]

def test_status_canceled(client, session):
    call = make_call(state=CallState.FAILED)
    session.add(call)
    session.commit()
    
    resp = client.get(f"/v1/phone/status/{call.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"

def test_status_in_progress(client, session):
    call = make_call(state=CallState.CONNECTED)
    session.add(call)
    session.commit()
    
    resp = client.get(f"/v1/phone/status/{call.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "in-progress"

def test_status_ringing(client, session):
    calls = [
        make_call(state=CallState.REDIRECTING),
        make_call(state=CallState.DESTINATION_INITIATED),
        make_call(state=CallState.DESTINATION_RINGING),
        make_call(state=CallState.DESTINATION_ANSWERED),
    ]
    session.add_all(calls)
    session.commit()

    results = [
        client.get(f"/v1/phone/status/{call.id}").json()["status"]
        for call in calls
    ]

    assert results == ["ringing", "ringing", "ringing", "ringing"]

def test_status_no_answer(client, session):
    call = make_call(state=CallState.NO_ANSWERED)
    session.add(call)
    session.commit()
    
    resp = client.get(f"/v1/phone/status/{call.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "no-answer"

def test_status_completed(client, session):
    call = make_call(state=CallState.COMPLETED)
    session.add(call)
    session.commit()
    
    resp = client.get(f"/v1/phone/status/{call.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"