"""Add phone tables

Revision ID: 5dcd0a4c3dfb
Revises: 
Create Date: 2025-08-21 17:37:19.452887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5dcd0a4c3dfb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    callstate_enum = sa.Enum(
        "initiated",
        "ringing",
        "answered",
        "answered-human",
        "redirecting",
        "destination-initiated",
        "destination-ringing",
        "destination-answered",
        "connected",
        "failed",
        "no-answered",
        "completed",
        name="callstate",
    )
    twiliocallstatus_enum = sa.Enum(
        "initiated",
        "queued",
        "ringing",
        "in-progress",
        "canceled",
        "completed",
        "busy",
        "no-answer",
        "failed",
        name="twiliocallstatus",
    )
    twilioansweredby_enum = sa.Enum(
        "human",
        "machine_start",
        "machine_start_beep",
        "machine_end",
        "machine_end_beep",
        "fax",
        "unknown",
        name="twilioansweredby",
    )
    eventtype_enum = sa.Enum(
        "status_callback",
        "amd_callback",
        "instruction",
        name="eventtype",
    )

    # phone_calls
    op.create_table(
        "phone_calls",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("state", callstate_enum, nullable=False, server_default="initiated"),
        sa.Column("from_number", sa.String(), nullable=False),
        sa.Column("to_number", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # phone_twilio_calls
    op.create_table(
        "phone_twilio_calls",
        sa.Column("sid", sa.String(), primary_key=True),
        sa.Column("status", twiliocallstatus_enum, nullable=False),
        sa.Column("direction", sa.String(), nullable=True),
        sa.Column("answered_by", twilioansweredby_enum, nullable=True),
        sa.Column("parent_call_id", sa.String(), sa.ForeignKey("phone_calls.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_phone_twilio_calls_parent_call_id",
        "phone_twilio_calls",
        ["parent_call_id"],
    )

    # phone_twilio_call_events
    op.create_table(
        "phone_twilio_call_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_type", eventtype_enum, nullable=False),
        sa.Column("twilio_response", sa.JSON, nullable=True),
        sa.Column("twilio_call_sid", sa.String(), sa.ForeignKey("phone_twilio_calls.sid")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_phone_twilio_call_events_twilio_call_sid",
        "phone_twilio_call_events",
        ["twilio_call_sid"],
    )


def downgrade() -> None:
    op.drop_index("ix_phone_twilio_call_events_twilio_call_sid", table_name="phone_twilio_call_events")
    op.drop_table("phone_twilio_call_events")

    op.drop_index("ix_phone_twilio_calls_parent_call_id", table_name="phone_twilio_calls")
    op.drop_table("phone_twilio_calls")

    op.drop_table("phone_calls")

    # Enums
    eventtype_enum = sa.Enum(name="eventtype")
    twilioansweredby_enum = sa.Enum(name="twilioansweredby")
    twiliocallstatus_enum = sa.Enum(name="twiliocallstatus")
    callstate_enum = sa.Enum(name="callstate")

    eventtype_enum.drop(op.get_bind(), checkfirst=True)
    twilioansweredby_enum.drop(op.get_bind(), checkfirst=True)
    twiliocallstatus_enum.drop(op.get_bind(), checkfirst=True)
    callstate_enum.drop(op.get_bind(), checkfirst=True)
