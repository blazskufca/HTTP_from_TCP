import asyncio
import unittest
from collections.abc import Coroutine
from typing import Any

from tcp_to_http.request import request_from_reader


class MockStreamReader(asyncio.StreamReader):
    def __init__(self, data: str, num_bytes_per_read: int) -> None:
        super().__init__()
        self.data = data.encode("utf-8")
        self.num_bytes_per_read = num_bytes_per_read
        self.pos = 0

    async def read(self, bufsize: int) -> Coroutine[Any, Any, bytes]:
        if self.pos >= len(self.data):
            return b""  # Connection closed

        available = len(self.data) - self.pos
        to_read = min(bufsize, available, self.num_bytes_per_read)

        chunk = self.data[self.pos:self.pos + to_read]
        self.pos += to_read
        return chunk


class TestRequestParsingRequestLine(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_good_GET_request_line(self) -> None:
        # Test: Good GET Request line
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHost: localhost:42069\r\n"
                 "User-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.request_line.method, "GET")
        self.assertEqual(r.request_line.request_target, "/")
        self.assertEqual(r.request_line.http_version, "1.1")

    def test_good_GET_request_line_with_path(self) -> None:
        # Test: Good GET Request line with path
        mock_reader = MockStreamReader(
            data="GET /coffee HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nUser-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=1
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.request_line.method, "GET")
        self.assertEqual(r.request_line.request_target, "/coffee")
        self.assertEqual(r.request_line.http_version, "1.1")

    def test_invalid_number_of_request_line_parts(self) -> None:
        # Test: Invalid number of parts in request line
        mock_reader = MockStreamReader(
            data="/coffee HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nUser-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=3
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))

    def test_good_POST_request_line(self) -> None:
        # Test: Good POST Request line with path
        mock_reader = MockStreamReader(
            data="POST /coffee HTTP/1.1\r\n"
                 "Host: localhost:42069\r\n"
                 "User-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=5
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.request_line.method, "POST")
        self.assertEqual(r.request_line.request_target, "/coffee")
        self.assertEqual(r.request_line.http_version, "1.1")

    def test_out_of_order_request_line(self) -> None:
        # Test: Invalid method (out of order) Request line
        mock_reader = MockStreamReader(
            data="/coffee POST HTTP/1.1\r\n"
                 "Host: localhost:42069\r\n"
                 "User-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=3
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))

    def test_invalid_version_in_request_line(self) -> None:
        # Test: Invalid version in Request line
        mock_reader = MockStreamReader(
            data="OPTIONS /prime/rib TCP/1.1\r\n"
                 "Host: localhost:42069\r\n"
                 "User-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=50
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))


class TestRequestParsingHeaders(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_standard_headers(self) -> None:
        # Test: Standard Headers
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nUser-Agent: curl/7.81.0\r\nAccept: */*\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.headers["host"], "localhost:42069")
        self.assertEqual(r.headers["user-agent"], "curl/7.81.0")
        self.assertEqual(r.headers["accept"], "*/*")

    def test_empty_headers(self) -> None:
        # Test: Empty Headers
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(len(r.headers), 0)

    def test_malformed_headers(self) -> None:
        # Test: Malformed Header
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHost localhost:42069\r\n\r\n",
            num_bytes_per_read=3
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))

    def test_duplicate_headers(self) -> None:
        # Test: Duplicate Headers
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nHost: duplicate:8080\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.headers["host"], "localhost:42069,duplicate:8080")

    def test_case_insensitive_headers(self) -> None:
        # Test: Case Insensitive Headers
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHOST: localhost:42069"
                 "\r\nUSER-AGENT: curl/7.81.0\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.headers["host"], "localhost:42069")
        self.assertEqual(r.headers["user-agent"], "curl/7.81.0")

    def test_invalid_header_end_marker(self) -> None:
        # Test: Missing End of Headers
        mock_reader = MockStreamReader(
            data="GET / HTTP/1.1\r\nHost: localhost:42069\r\nUser-Agent: curl/7.81.0",
            num_bytes_per_read=3
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))


class TestRequestParsingBody(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_standard_body(self) -> None:
        # Test: Standard Body
        mock_reader = MockStreamReader(
            data="POST /submit HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nContent-Length: 13\r\n\r\nhello world!\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.body.decode("utf-8"), "hello world!\n")

    def test_emtpy_body_with_no_content_length(self) -> None:
        # Test: Empty Body, 0 reported content length
        mock_reader = MockStreamReader(
            data="POST /submit HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nContent-Length: 0\r\n\r\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.body.decode("utf-8"), "")

    def test_body_shorter_than_reported_content_length(self) -> None:
        # Test: Body shorter than reported content length
        mock_reader = MockStreamReader(
            data="POST /submit HTTP/1.1\r\nHost: localhost:42069"
                 "\r\nContent-Length: 20\r\n\r\npartial content",
            num_bytes_per_read=3
        )
        with self.assertRaises(Exception):
            self.loop.run_until_complete(request_from_reader(mock_reader))

    def test_body_with_no_content_length(self) -> None:
        # Test: No Content-Length but Body Exists
        mock_reader = MockStreamReader(
            data="POST /submit HTTP/1.1\r\nHost: localhost:42069\r\n\r\nhello world!\n",
            num_bytes_per_read=3
        )
        r = self.loop.run_until_complete(request_from_reader(mock_reader))
        self.assertIsNotNone(r)
        self.assertEqual(r.body.decode("utf-8"), "")
