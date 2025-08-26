import enum
from sqlalchemy import Column, Enum as SQLEnum


class BaseEnum(str, enum.Enum):
    
    def __str__(self):
        return self.value

    @classmethod
    def Column(cls):
        return Column(SQLEnum(cls, values_callable=lambda x: [e.value for e in x]))


class CallState(BaseEnum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    ANSWERED_HUMAN = "answered-human"
    REDIRECTING = "redirecting"
    DESTINATION_INITIATED = "destination-initiated"
    DESTINATION_RINGING = "destination-ringing"
    DESTINATION_ANSWERED = "destination-answered"
    CONNECTED = "connected"
    FAILED = "failed"
    NO_ANSWERED = "no-answered"
    COMPLETED = "completed"


class TwilioCallStatus(BaseEnum):
    """https://www.twilio.com/docs/voice/api/call-resource#call-status-values
    
    Args:
        BaseEnum (_type_): _description_
    """
    INITIATED = "initiated"
    QUEUED = "queued"           # The call is ready and waiting in line before dialing.
    RINGING = "ringing"         # The call is currently ringing.
    IN_PROGRESS = "in-progress" # The call was answered and is currently in progress.
    CANCELED = "canceled"       # The call was hung up while it was queued or ringing.
    COMPLETED = "completed"     # The call was answered and has ended normally.
    BUSY = "busy"               # The caller received a busy signal.
    NO_ANSWER = "no-answer"     # There was no answer or the call was rejected.
    FAILED = "failed"           # The call could not be completed as dialed, most likely because the provided number was invalid.


class TwilioAnsweredBy(BaseEnum):
    """https://www.twilio.com/docs/studio/widget-library/make-outgoing-call#example-who-answered

    Args:
        BaseEnum (_type_): _description_
    """
    HUMAN = "human"
    MACHINE_START = "machine_start"
    MACHINE_END = "machine_end"
    FAX = "fax"
    UNKNOWN = "unknown"


class EventType(BaseEnum):
    STATUS_CALLBACK = "status_callback"
    AMD_CALLBACK = "amd_callback"
    INSTRUCTION = "instruction"