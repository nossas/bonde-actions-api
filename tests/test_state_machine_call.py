import pytest
from transitions import MachineError

from app.models import Call
from app.enum import CallState
from app.machine import CallMachine

def create_call_record(**attrs):
    return Call(
        **{
            "id": "fake-id",
            "from_number": "+5531998998767",
            "to_number": "+5521998736412",
            "state": CallState.INITIATED,
            **attrs
        }
    )


def test_call_machine_success():
    call = create_call_record(state=CallState.INITIATED)
    
    events = ["call", "attend", "connect", "dial_call", "dial_attend", "dial_connect"]
    
    machine = CallMachine(call)
    for e in events:
        getattr(machine, e)()
    
    assert call.state == CallState.CONNECTED


def test_call_machine_not_attend():
    call = create_call_record(state=CallState.INITIATED)
    
    events = ["call", "attend", "voicemail"]
    
    machine = CallMachine(call)
    for e in events:
        getattr(machine, e)()
    
    assert call.state == CallState.FAILED
    

def test_call_machine_not_attend():
    call = create_call_record(state=CallState.INITIATED)
    
    events = ["call", "attend", "voicemail"]
    
    machine = CallMachine(call)
    for e in events:
        getattr(machine, e)()
    
    assert call.state == CallState.FAILED


def test_call_machine_failed_cycle():
    call = create_call_record(state=CallState.RINGING)
    events = ["call", "attend"]
    
    with pytest.raises(MachineError, match="Can't trigger event call from state RINGING!"):
        machine = CallMachine(call)
        for e in events:
            getattr(machine, e)()