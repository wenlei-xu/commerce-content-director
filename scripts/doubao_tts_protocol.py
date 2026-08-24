"""Minimal implementation of Volcengine's bidirectional TTS WebSocket protocol.

The wire format and event values follow the official protocol bundle linked from
the Doubao Voice bidirectional WebSocket documentation.
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from enum import IntEnum


class MsgType(IntEnum):
    FULL_CLIENT_REQUEST = 0b0001
    AUDIO_ONLY_CLIENT = 0b0010
    FULL_SERVER_RESPONSE = 0b1001
    AUDIO_ONLY_SERVER = 0b1011
    ERROR = 0b1111


class Flag(IntEnum):
    NO_SEQUENCE = 0
    POSITIVE_SEQUENCE = 0b0001
    NEGATIVE_SEQUENCE = 0b0011
    WITH_EVENT = 0b0100


class EventType(IntEnum):
    NONE = 0
    START_CONNECTION = 1
    FINISH_CONNECTION = 2
    CONNECTION_STARTED = 50
    CONNECTION_FAILED = 51
    CONNECTION_FINISHED = 52
    START_SESSION = 100
    CANCEL_SESSION = 101
    FINISH_SESSION = 102
    SESSION_STARTED = 150
    SESSION_CANCELED = 151
    SESSION_FINISHED = 152
    SESSION_FAILED = 153
    USAGE_RESPONSE = 154
    TASK_REQUEST = 200
    TTS_SENTENCE_START = 350
    TTS_SENTENCE_END = 351
    TTS_RESPONSE = 352
    TTS_ENDED = 359
    TTS_SUBTITLE = 364


@dataclass
class Message:
    msg_type: MsgType
    flag: Flag = Flag.NO_SEQUENCE
    event: int = EventType.NONE
    session_id: str = ""
    connect_id: str = ""
    sequence: int = 0
    error_code: int = 0
    payload: bytes = b""

    def marshal(self) -> bytes:
        buffer = io.BytesIO()
        buffer.write(bytes([0x11, (int(self.msg_type) << 4) | int(self.flag), 0x10, 0x00]))
        if self.flag == Flag.WITH_EVENT:
            buffer.write(struct.pack(">i", int(self.event)))
            if self.event not in {
                EventType.START_CONNECTION,
                EventType.FINISH_CONNECTION,
                EventType.CONNECTION_STARTED,
                EventType.CONNECTION_FAILED,
            }:
                session = self.session_id.encode("utf-8")
                buffer.write(struct.pack(">I", len(session)))
                buffer.write(session)
        if self.flag in {Flag.POSITIVE_SEQUENCE, Flag.NEGATIVE_SEQUENCE}:
            buffer.write(struct.pack(">i", self.sequence))
        buffer.write(struct.pack(">I", len(self.payload)))
        buffer.write(self.payload)
        return buffer.getvalue()

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        if len(data) < 8:
            raise ValueError(f"TTS response frame is too short: {len(data)} bytes")
        buffer = io.BytesIO(data)
        first = buffer.read(1)[0]
        header_size_words = first & 0x0F
        type_and_flag = buffer.read(1)[0]
        serialization_and_compression = buffer.read(1)[0]
        buffer.read(max(0, header_size_words * 4 - 3))
        if serialization_and_compression & 0x0F:
            raise ValueError("Compressed Doubao TTS frames are not supported")

        msg_type = MsgType(type_and_flag >> 4)
        flag = Flag(type_and_flag & 0x0F)
        message = cls(msg_type=msg_type, flag=flag)

        if flag in {Flag.POSITIVE_SEQUENCE, Flag.NEGATIVE_SEQUENCE}:
            message.sequence = _read_i32(buffer)
        elif msg_type == MsgType.ERROR:
            message.error_code = _read_u32(buffer)

        if flag == Flag.WITH_EVENT:
            message.event = _read_i32(buffer)
            if message.event not in {
                EventType.START_CONNECTION,
                EventType.FINISH_CONNECTION,
                EventType.CONNECTION_STARTED,
                EventType.CONNECTION_FAILED,
                EventType.CONNECTION_FINISHED,
            }:
                message.session_id = _read_sized_text(buffer)
            if message.event in {
                EventType.CONNECTION_STARTED,
                EventType.CONNECTION_FAILED,
                EventType.CONNECTION_FINISHED,
            }:
                message.connect_id = _read_sized_text(buffer)

        payload_size = _read_u32(buffer)
        message.payload = buffer.read(payload_size)
        if len(message.payload) != payload_size:
            raise ValueError("Incomplete Doubao TTS response payload")
        return message

    def payload_text(self) -> str:
        return self.payload.decode("utf-8", errors="replace")


def _read_i32(buffer: io.BytesIO) -> int:
    value = buffer.read(4)
    if len(value) != 4:
        raise ValueError("Incomplete signed integer in TTS frame")
    return struct.unpack(">i", value)[0]


def _read_u32(buffer: io.BytesIO) -> int:
    value = buffer.read(4)
    if len(value) != 4:
        raise ValueError("Incomplete unsigned integer in TTS frame")
    return struct.unpack(">I", value)[0]


def _read_sized_text(buffer: io.BytesIO) -> str:
    size = _read_u32(buffer)
    value = buffer.read(size)
    if len(value) != size:
        raise ValueError("Incomplete text field in TTS frame")
    return value.decode("utf-8")


def event_message(event: EventType, *, session_id: str = "", payload: bytes = b"{}") -> bytes:
    return Message(
        msg_type=MsgType.FULL_CLIENT_REQUEST,
        flag=Flag.WITH_EVENT,
        event=event,
        session_id=session_id,
        payload=payload,
    ).marshal()
