from typing import Tuple

# Constants
CRLF = '\r\n'
TOKEN_CHARS = set(b"!$%&'*+-.^_`|~")

class Headers:
    def __init__(self) -> None:
        self.headers = {}

    def __setitem__(self, key: str, value: str) -> None:
        self.headers[key.lower()] = value

    def __delitem__(self, key: str) -> None:
        key = key.lower()
        if key in self.headers:
            del self.headers[key]

    def __getitem__(self, key: str) -> str:
        key = key.lower().strip()
        return self.headers[key]

    def parse(self, data: bytes) -> Tuple[int, bool]:
        index = data.find(CRLF.encode('utf-8'))
        if index == -1:
            return 0, False

        if index == 0:
            return index + len(CRLF), True

        line = data[:index].decode('utf-8', errors='strict').strip()

        split_key_value = line.split(':', 1)

        if len(split_key_value) != 2:
            raise ValueError(f"Invalid header format: expected key:value, got {line}")

        key, value = split_key_value

        if ' ' in key:
            raise ValueError(f"Header key contains space: {key}")
        key = key.strip()
        value = value.strip()

        if not self.__valid_tokens(key.encode('utf-8')):
            raise ValueError(f"Header key contains invalid characters: {key}")

        key_lower = key.lower()
        if key_lower in self.headers:
            self.headers[key_lower] += f",{value}"
        else:
            self.headers[key_lower] = value

        return index + len(CRLF), False

    def __valid_tokens(self, data: bytes) -> bool:
        """Check if data contains only valid token characters."""
        for c in data:
            if not (
                    (c >= ord('A') and c <= ord('Z')) or
                    (c >= ord('a') and c <= ord('z')) or
                    (c >= ord('0') and c <= ord('9')) or
                    c == ord('-') or
                    c in TOKEN_CHARS
            ):
                return False
        return True
