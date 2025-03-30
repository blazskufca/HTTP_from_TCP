from enum import IntEnum

from headers import Headers


class StatusCode(IntEnum):
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


def get_status_line(status_code: StatusCode) -> bytes:
    status_line = "HTTP/1.1 %d %s\r\n"
    status_lines = {
        StatusCode.OK: status_line % (status_code.value, "OK"),
        StatusCode.BAD_REQUEST: status_line % (status_code.value, "Bad Request"),
        StatusCode.INTERNAL_SERVER_ERROR:
            status_line % (status_code.value , "Internal Server Error"),
    }
    return status_lines.get(status_code,
                            f"HTTP/1.1 {status_code} \r\n".encode()).encode("utf-8")

def get_default_headers(content_len: int) -> Headers:
    h = Headers()
    h["content-length"] = str(content_len)
    h["connection"] = "close"
    h["content-type"] = "text/plain"
    return h
