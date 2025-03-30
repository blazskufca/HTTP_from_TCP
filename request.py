import socket
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from headers import Headers

# Constants
BUFFER_SIZE = 8
CRLF = b"\r\n"

class ParserState(Enum):
    INITIALIZED = auto()
    PARSING_HEADERS = auto()
    PARSING_BODY = auto()
    DONE = auto()


@dataclass
class RequestLine:
    def __init__(self,
                 method: str = "",
                 request_target: str = "",
                 http_version: str = "") -> None:
        self.method:str = method
        self.request_target:str = request_target
        self.http_version:str = http_version


class Request:
    def __init__(self) -> None:
        self.request_line:RequestLine = RequestLine()
        self.headers:Headers = Headers()
        self.body:bytearray = bytearray()
        self.state:ParserState = ParserState.INITIALIZED
        self.body_length_read:int = 0

    def parse(self, data: bytes) -> int:
        total_bytes_parsed = 0
        while self.state != ParserState.DONE:
            n = self.__parse_single(data[total_bytes_parsed:])
            total_bytes_parsed += n
            if n == 0:
                break
        return total_bytes_parsed

    def __parse_single(self, data: bytes) -> int:
        match self.state:
            case ParserState.INITIALIZED:
                n, request_line = parse_request_line(data)
                if n == 0:
                    return 0
                self.request_line = request_line
                self.state = ParserState.PARSING_HEADERS
                return n
            case ParserState.PARSING_HEADERS:
                n, headers_done = self.headers.parse(data)
                if headers_done:
                    self.state = ParserState.PARSING_BODY
                return n
            case ParserState.PARSING_BODY:
                content_length = self.headers.get("Content-Length")
                if not content_length:
                    self.state = ParserState.DONE
                    return len(data)
                else:
                    content_len = int(content_length)

                    self.body.extend(data)
                    self.body_length_read += len(data)

                    if self.body_length_read > content_len:
                        msg = "Content-Length too large"
                        raise ValueError(msg)

                    if self.body_length_read == content_len:
                        self.state = ParserState.DONE

                    return len(data)
            case ParserState.DONE:
                msg = "error: trying to read data in a done state"
                raise RuntimeError(msg)
            case _:
                msg = "unknown state"
                raise RuntimeError(msg)


def request_from_reader(sock: socket.socket) -> Request:
    buf = bytearray(BUFFER_SIZE)
    read_to_idx = 0
    request = Request()

    while request.state != ParserState.DONE:
        if read_to_idx >= len(buf):
            new_buf = bytearray(len(buf) * 2)
            new_buf[:read_to_idx] = buf[:read_to_idx]
            buf = new_buf

        try:
            chunk = sock.recv(len(buf) - read_to_idx)
            if not chunk:
                if request.state != ParserState.DONE:
                    msg = (f"incomplete request, in state: "
                           f"{request.state}, connection closed")
                    raise ValueError(msg)
                break

            buf[read_to_idx:read_to_idx + len(chunk)] = chunk
            read_to_idx += len(chunk)

            consumed = request.parse(buf[:read_to_idx])
            buf[:read_to_idx - consumed] = buf[consumed:read_to_idx]
            read_to_idx -= consumed
        except socket.timeout:
            continue
    return request


def parse_request_line(data: bytes) -> tuple[int, Optional[RequestLine]]:
    try:
        idx = data.index(CRLF)
    except ValueError:
        return 0, None

    request_line_text = data[:idx].decode("utf-8")
    request_line = request_line_from_string(request_line_text)
    return idx + len(CRLF), request_line


def request_line_from_string(s: str) -> RequestLine:
    parts = s.split(" ")
    if len(parts) != 3:
        msg = f"poorly formatted request-line: {s}"
        raise ValueError(msg)

    method = parts[0]
    for c in method:
        if not ("A" <= c <= "Z"):
            msg = f"invalid method: {method}"
            raise ValueError(msg)
    http_verbs = ("GET",
                  "POST",
                  "PUT",
                  "DELETE",
                  "HEAD",
                  "OPTIONS",
                  "PATCH",
                  "CONNECT",
                  "TRACE",)
    if method not in http_verbs:
        msg = f"method must be one of the following {http_verbs}, got: {method}"
        raise ValueError(msg)

    request_target = parts[1]

    version_parts = parts[2].split("/")
    if len(version_parts) != 2:
        msg = f"malformed start-line: {s}"
        raise ValueError(msg)

    http_part = version_parts[0]
    if http_part != "HTTP":
        msg = f"unrecognized HTTP-version: {http_part}"
        raise ValueError(msg)

    version = version_parts[1]
    if version != "1.1":
        msg = f"unrecognized HTTP-version: {version}"
        raise ValueError(msg)

    return RequestLine(method=method,
                       request_target=request_target,
                       http_version=version)
