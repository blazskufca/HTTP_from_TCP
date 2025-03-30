from enum import IntEnum, auto
from socket import socket

from .headers import Headers
from .responses import StatusCode, get_status_line


class WriterState(IntEnum):
    STATUS_LINE = auto()
    HEADERS = auto()
    BODY = auto()

class Writer:
    def __init__(self, writer: socket) -> None:
        self.writer_state = WriterState.STATUS_LINE
        self.writer = writer

    def write_status_line(self, status_code: StatusCode) -> None:
        if self.writer_state != WriterState.STATUS_LINE:
            msg = f"cannot write status line in state {self.writer_state}"
            raise ValueError(msg)
        self.writer.sendall(get_status_line(status_code))
        self.writer_state = WriterState.HEADERS

    def write_headers(self, headers: Headers) -> None:
        if self.writer_state != WriterState.HEADERS:
            msg = f"cannot write headers in state {self.writer_state}"
            raise ValueError(msg)
        for key, value in headers.items():
            self.writer.sendall(f"{key}: {value}\r\n".encode())
        self.writer.sendall(b"\r\n")
        self.writer_state = WriterState.BODY

    def write_body(self, data: str) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        self.writer.sendall(data.encode("utf-8"))
        return len(data)

    def write_chunked_body(self, data: str) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        total_written = 0

        chunk_size = f"{len(data):x}\r\n".encode()
        self.writer.sendall(chunk_size)
        total_written += len(chunk_size)

        self.writer.sendall(data.encode("utf-8"))
        total_written += len(data)

        self.writer.sendall(b"\r\n")
        total_written += 2

        return total_written

    def write_trailers(self, trailers: Headers) -> None:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write headers in state {self.writer_state}"
            raise ValueError(msg)
        self.writer.sendall(b"0\r\n")
        for key, value in trailers.items():
            self.writer.sendall(f"{key}: {value}\r\n".encode())
        self.writer.sendall(b"\r\n")

    def write_chunked_body_done(self) -> int:
        if self.writer_state != WriterState.BODY:
            msg = f"cannot write body in state {self.writer_state}"
            raise ValueError(msg)
        data = b"0\r\n\r\n"
        self.writer.sendall(data)
        return len(data)
