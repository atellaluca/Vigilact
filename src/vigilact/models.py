# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""Transport-neutral shapes for the Vigilact v0.1 experimental profile."""

from datetime import datetime, timezone
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$")


def require_timestamp(value: object) -> object:
    """Refuse epoch numbers and non-RFC3339 strings on the public JSON boundary."""
    if isinstance(value, datetime):
        return value  # Python SDK may pass a timezone-aware datetime directly.
    if not isinstance(value, str) or not _RFC3339.fullmatch(value):
        raise ValueError("Timestamp must be an RFC 3339 string (at most microsecond precision)")
    return value


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware RFC 3339 timestamp is required")
    return value.astimezone(timezone.utc)


class ExpectedEvent(StrictModel):
    kind: Literal["expected_event"] = "expected_event"
    event_type: str = Field(min_length=1, max_length=200)
    deadline_at: datetime

    @field_validator("deadline_at", mode="before")
    @classmethod
    def validate_deadline_format(cls, value: object) -> object:
        return require_timestamp(value)

    @field_validator("deadline_at")
    @classmethod
    def utc_deadline(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ContractProposal(StrictModel):
    client_ref: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
    subject: str = Field(min_length=1, max_length=255)
    observation: ExpectedEvent


class CloudEvent(StrictModel):
    """Supported CloudEvents JSON subset; other extensions are not implemented."""

    specversion: Literal["1.0"]
    id: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=255)
    time: datetime | None = None
    datacontenttype: Literal["application/json"] = "application/json"
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("time", mode="before")
    @classmethod
    def validate_time_format(cls, value: object) -> object:
        return require_timestamp(value) if value is not None else None

    @field_validator("time")
    @classmethod
    def utc_time(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value) if value is not None else None


class Capability(StrictModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")
    mode: Literal["query", "command"]
    description: str = Field(default="", max_length=500)
    invocable: bool = False

    @model_validator(mode="after")
    def safe_mode(self) -> "Capability":
        if self.invocable and self.mode != "command":
            raise ValueError("Only command capabilities can be marked invocable")
        return self


class CapabilityManifest(StrictModel):
    capabilities: list[Capability] = Field(max_length=100)

    @model_validator(mode="after")
    def no_duplicates(self) -> "CapabilityManifest":
        names = [cap.name for cap in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("Capability names must be unique")
        return self


class CommandRequest(StrictModel):
    request_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
    target_agent: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
    capability: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")
    arguments: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


class CommandResult(StrictModel):
    status: Literal["succeeded", "failed"]
    output: dict[str, Any] = Field(default_factory=dict)


class ContractView(StrictModel):
    id: str
    owner: str
    client_ref: str
    subject: str
    observation: ExpectedEvent
    state: Literal["ACTIVE"]
    outcome: Literal["PENDING", "SATISFIED", "NOT_OBSERVED"]
    accepted_at: datetime
    resolved_at: datetime | None


class EventReceipt(StrictModel):
    status: Literal["accepted", "duplicate"]
    satisfied_contracts: list[str]


class CapabilityView(StrictModel):
    agent: str
    capabilities: list[Capability]


class CommandView(StrictModel):
    id: str
    request_id: str
    target_agent: str
    capability: str
    arguments: dict[str, Any]
    status: Literal["PENDING", "CLAIMED", "SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED", "UNKNOWN"]
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    lease_expires_at: datetime | None = None


class CommandList(StrictModel):
    commands: list[CommandView]


class OutboxEntry(StrictModel):
    seq: int
    event: CloudEvent


class OutboxPage(StrictModel):
    entries: list[OutboxEntry]
    next_cursor: int
