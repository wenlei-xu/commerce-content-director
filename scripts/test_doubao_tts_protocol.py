from __future__ import annotations

import struct
import unittest

from doubao_tts_protocol import EventType, Flag, Message, MsgType, event_message


class DoubaoProtocolTests(unittest.TestCase):
    def test_start_connection_frame_round_trips(self) -> None:
        frame = event_message(EventType.START_CONNECTION)
        message = Message.from_bytes(frame)
        self.assertEqual(message.msg_type, MsgType.FULL_CLIENT_REQUEST)
        self.assertEqual(message.flag, Flag.WITH_EVENT)
        self.assertEqual(message.event, EventType.START_CONNECTION)
        self.assertEqual(message.payload, b"{}")

    def test_audio_response_frame_parses_payload(self) -> None:
        payload = b"mp3-bytes"
        frame = bytes([0x11, 0xB4, 0x00, 0x00])
        frame += struct.pack(">i", int(EventType.TTS_RESPONSE))
        session = b"session-1"
        frame += struct.pack(">I", len(session)) + session
        frame += struct.pack(">I", len(payload)) + payload
        message = Message.from_bytes(frame)
        self.assertEqual(message.msg_type, MsgType.AUDIO_ONLY_SERVER)
        self.assertEqual(message.event, EventType.TTS_RESPONSE)
        self.assertEqual(message.session_id, "session-1")
        self.assertEqual(message.payload, payload)


if __name__ == "__main__":
    unittest.main()
