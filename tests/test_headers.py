import unittest

from headers import Headers


class TestHeadersParse(unittest.TestCase):
    def test_valid_single_header(self) -> None:
        headers = Headers()
        data = b"Host: localhost:42069\r\n\r\n"
        n, done = headers.parse(data)
        self.assertEqual(headers["host"], "localhost:42069")
        self.assertEqual(n, 23)
        self.assertFalse(done)

    def test_valid_single_header_with_extra_whitespace(self) -> None:
        headers = Headers()
        data = b"       Host: localhost:42069                           \r\n\r\n"
        n, done = headers.parse(data)
        self.assertEqual(headers["host"], "localhost:42069")
        self.assertEqual(n, 57)
        self.assertFalse(done)

    def test_valid_two_headers_with_existing_headers(self) -> None:
        headers = Headers()
        headers["host"] = "localhost:42069"
        data = b"User-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n"
        n, done = headers.parse(data)
        self.assertEqual(headers["host"], "localhost:42069")
        self.assertEqual(headers["user-agent"], "curl/7.81.0")
        self.assertEqual(n, 25)
        self.assertFalse(done)

    def test_valid_done(self) -> None:
        headers = Headers()
        data = b"\r\n a bunch of other stuff"
        n, done = headers.parse(data)
        self.assertEqual(len(headers), 0)
        self.assertEqual(n, 2)
        self.assertTrue(done)

    def test_invalid_spacing_header(self) -> None:
        headers = Headers()
        data = b"       Host : localhost:42069       \r\n\r\n"
        with self.assertRaises(ValueError):
            headers.parse(data)

    def test_valid_uppercase_single_header(self) -> None:
        headers = Headers()
        data = b"HOST: localhost:42069\r\n\r\n"
        n, done = headers.parse(data)
        self.assertEqual(headers["host"], "localhost:42069")
        self.assertEqual(n, 23)
        self.assertFalse(done)

    def test_invalid_char_in_header_key(self) -> None:
        headers = Headers()
        data = b"H@st: localhost:42069\r\n\r\n"
        with self.assertRaises(ValueError):
            headers.parse(data)

    def test_valid_uppercase_with_existing_header(self) -> None:
        headers = Headers()
        headers["host"] = "your-moms-house.com:42069"
        data = b"Host: localhost:42069\r\n\r\n"
        n, done = headers.parse(data)
        self.assertEqual(headers["host"], "your-moms-house.com:42069,localhost:42069")
        self.assertEqual(n, 23)
        self.assertFalse(done)
