from typing import List
from transitions import Machine

from .enum import CallState

class CallMachine:
    states: List[CallState] = [s for s in CallState]
    
    def __init__(self, call):
        self.model = call
        self.machine = Machine(
            model=self,
            states=self.states,
            initial=call.state,
            after_state_change="on_any_transition"
        )
        
        # Origem
        self.machine.add_transition("call", CallState.INITIATED, CallState.RINGING)
        self.machine.add_transition("attend", CallState.RINGING, CallState.ANSWERED)
        self.machine.add_transition("connect", CallState.ANSWERED, CallState.REDIRECTING)

        # Destino
        self.machine.add_transition("dial_call", CallState.REDIRECTING, CallState.DESTINATION_RINGING)
        self.machine.add_transition("dial_attend", CallState.DESTINATION_RINGING, CallState.DESTINATION_ANSWERED)
        self.machine.add_transition("dial_connect", CallState.DESTINATION_ANSWERED, CallState.CONNECTED)

        # Variações de Caixa postal e Ocupado
        self.machine.add_transition("voicemail", CallState.ANSWERED, CallState.FAILED)
        self.machine.add_transition("dial_voicemail", CallState.DESTINATION_ANSWERED, CallState.NO_ANSWERED)

        # Estado final
        self.machine.add_transition("fail", "*", CallState.FAILED)  # TODO: Mapear melhor as falhas
        self.machine.add_transition("complete", CallState.CONNECTED, CallState.COMPLETED, conditions=["is_connected"])
        self.machine.add_transition("complete", CallState.COMPLETED, CallState.COMPLETED, conditions=["is_completed"])
        self.machine.add_transition("complete", "*", CallState.FAILED)

    def is_connected(self):
        return self.model.state == CallState.CONNECTED

    def is_completed(self):
        return self.model.state == CallState.COMPLETED

    def on_any_transition(self):
        """Persistir no banco de dados"""
        self.model.state = self.state