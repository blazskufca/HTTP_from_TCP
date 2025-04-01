from typing import Optional

# Constants
CRLF = b"\r\n"
TOKEN_CHARS = {ord(c) for c in "!#$%&'*+-.^_`|~"}

class Headers(dict):
    def __init__(self, *args: dict[str, str], **kwargs: dict[str, str]) -> None:
        super().__init__()
        if args and isinstance(args[0], dict):
            for key, value in args[0].items():
                self[key] = value
        if kwargs:
            for key, value in kwargs.items():
                self[key] = value

    def __setitem__(self, key: str, value: str) -> None:
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key.lower())

    def __getitem__(self, key: str) -> str:
        return super().__getitem__(key.lower())

    def __contains__(self, key: str) -> bool:
        return super().__contains__(key.lower())

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return super().get(key.lower(), default)

    def parse(self, data: bytes) -> tuple[int, bool]:
        idx = data.find(CRLF)
        if idx == -1:
            return 0, False
        if idx == 0:
            return idx + len(CRLF), True
        try:
            line = data[:idx].decode("utf-8", errors="strict").strip()
            split_key_value = line.split(":", 1)
            if len(split_key_value) != 2:
                msg = "invalid field-line, not key-value"
                raise ValueError(msg)
            key, value = split_key_value
            if " " in key:
                msg = "the key must not contain any space"
                raise ValueError(msg)
            if not self.__valid_tokens(key.encode("utf-8")):
                msg = f"invalid header token found: {key}"
                raise ValueError(msg)
            key = key.strip().lower()
            value = value.strip()
            if key in self:
                self[key] = f"{self[key]},{value}"
            else:
                self[key] = value
            return idx + len(CRLF), False
        except UnicodeDecodeError as err:
            msg = "Invalid UTF-8 sequence in header"
            raise ValueError(msg) from err

    def __valid_tokens(self, data: bytes) -> bool:
        for c in data:
            if not (
                    (ord("A") <= c <= ord("Z")) or
                    (ord("a") <= c <= ord("z")) or
                    (ord("0") <= c <= ord("9")) or
                    c in TOKEN_CHARS
            ):
                return False
        return True
