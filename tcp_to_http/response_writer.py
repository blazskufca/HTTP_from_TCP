import asyncio
from collections.abc import Coroutine
from enum import IntEnum, auto
from typing import Any, Optional

from .headers import Headers
from .responses import StatusCode, get_status_line


class WriterState(IntEnum):
    STATUS_LINE = auto()
    HEADERS = auto()
    BODY = auto()

class Writer:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self.writer_state = WriterState.STATUS_LINE
        self.writer = writer
        self._needs_drain = False

    def write_status_line(self, status_code: StatusCode) -> None:
        if self.writer_state != WriterState.STATUS_LINE:
            msg = f"cannot write status line in state {self.writer_state}"
            raise ValueError(msg)
        self.writer.write(get_status_line(status_code))
        self.writer_state = WriterState.HEADERS

    def write_headers(self, headers: Headers) -> None:
        if self.writer_state != WriterState.HEADERS:
            msg = f"cannot write headers in state {self.writer_state}"
            raise ValueError(msg)
        for key, value in headers.items():
            self.writer.write(f"{key}: {value}\r\n".encode())
        self.writer.write(b"\r\n")
        self.writer_state = WriterState.BODY

    def write_body(self, data: str) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        encoded_data = data.encode("utf-8")
        self.writer.write(encoded_data)
        return len(data)

    def write_chunked_body(self, data: str | bytes) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        total_written = 0

        if isinstance(data, str):
            encoded_data = data.encode("utf-8")
        else:
            encoded_data = data

        chunk_size = f"{len(encoded_data):x}\r\n".encode()
        self.writer.write(chunk_size)
        total_written += len(chunk_size)

        self.writer.write(encoded_data)
        total_written += len(encoded_data)

        self.writer.write(b"\r\n")
        total_written += 2

        self._needs_drain = True

        return total_written

    def get_drain_future(self) -> Optional[Coroutine[Any, Any, None]]:
        if self._needs_drain:
            self._needs_drain = False
            return self.writer.drain()
        return None

    def write_trailers(self, trailers: Headers) -> None:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write headers in state {self.writer_state}"
            raise ValueError(msg)
        self.writer.write(b"0\r\n")
        for key, value in trailers.items():
            self.writer.write(f"{key}: {value}\r\n".encode())
        self.writer.write(b"\r\n")


    def write_chunked_body_done(self) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        data = b"0\r\n\r\n"
        self.writer.write(data)
        return len(data)
