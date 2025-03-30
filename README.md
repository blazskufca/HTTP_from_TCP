# TCP to HTTP ![CI/CD Pipeline](https://github.com/blazskufca/HTTP_from_TCP/actions/workflows/ci.yml/badge.svg)

***This project implements a simple [Go](https://go.dev/)-like threaded [`HTTP 1.1`](https://datatracker.ietf.org/doc/html/rfc9112)
server in Python.***

## Usage

If you're familiar with the [Go `net/http`](https://pkg.go.dev/net/http) package, this should feel quite familiar.

### Serving HTML 

```python
from tcp_to_http import serve, Request, Writer, get_default_headers, StatusCode

def say_hello(w: Writer, r: Request):
    print("Got request from", r.request_line.method, r.request_line.request_target)
    print("Headers:", r.headers)
    print("Body:", r.body.decode())
    response_body = "<h1>Hello, World!</h1>"
    headers = get_default_headers(len(response_body))
    headers["content-type"] = "text/html"
    w.write_status_line(StatusCode.OK)
    w.write_headers(headers)
    w.write_body(response_body)


def curl_POST(w: Writer, r: Request):
    print("Got request from", r.request_line.method, r.request_line.request_target)
    print("Headers:", r.headers)
    print("Body:", r.body.decode())
    response_body = f"Got {len(r.body)} bytes of your data!\n"
    headers = get_default_headers(len(response_body))
    w.write_status_line(StatusCode.OK)
    w.write_headers(headers)
    w.write_body(response_body)


if __name__ == "__main__":
    s = serve("localhost", 42069)
    s.register_handler("/hello", say_hello)
    s.register_handler("/POST_some_data", curl_POST)
    s.listen()
```

![Served `HTML` page](https://github-production-user-asset-6210df.s3.amazonaws.com/3877198/428391565-b0ce1a46-0870-46a1-a1ae-50bb5d979c82.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20250330%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250330T115430Z&X-Amz-Expires=300&X-Amz-Signature=177af4c48654379a17541ecf9ddb18677fdb26fc8603e7301e2a083cbb846a0e&X-Amz-SignedHeaders=host)

```text
[INFO] 30-03-2025 13-27-16 - Server listening on port localhost:42069
[INFO] 30-03-2025 13-27-16 - Listening for incoming connections
Got request from GET /hello
Headers: {'host': 'localhost:42069', 'connection': 'keep-alive', 'cache-control': 'max-age=0', 'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'dnt': '1', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'none', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US,en;q=0.9', 'cookie': 'Goland-22107932=81c110d9-b6c8-47e0-8abe-9fb1ea4431eb'}
Body: 
[DEBUG] 30-03-2025 13-32-34 - New connection from ('127.0.0.1', 54640)
[DEBUG] 30-03-2025 13-32-34 - Handling connection from 127.0.0.1:54640
[DEBUG] 30-03-2025 13-32-34 - Reading request from 127.0.0.1:54640
[DEBUG] 30-03-2025 13-32-34 - New connection from ('127.0.0.1', 54641)
[DEBUG] 30-03-2025 13-32-34 - Request from 127.0.0.1:54640: GET /hello
[DEBUG] 30-03-2025 13-32-34 - Calling handler for GET /hello
[DEBUG] 30-03-2025 13-32-34 - Handling connection from 127.0.0.1:54641
[DEBUG] 30-03-2025 13-32-34 - Reading request from 127.0.0.1:54641
[INFO] 30-03-2025 13-32-34 - Handler completed successfully for 127.0.0.1:54640
[DEBUG] 30-03-2025 13-32-34 - Closing connection with 127.0.0.1:54640
```

### `POST`ing data

```shell
curl.exe -v -X POST -d "This is some test data I'm sending via POST" http://localhost:42069/POST_some_data
```
```text
Note: Unnecessary use of -X or --request, POST is already inferred.
* Host localhost:42069 was resolved.
* IPv6: ::1
* IPv4: 127.0.0.1
*   Trying [::1]:42069...
*   Trying 127.0.0.1:42069...
* Connected to localhost (127.0.0.1) port 42069
* using HTTP/1.x
> POST /POST_some_data HTTP/1.1
> Host: localhost:42069
> User-Agent: curl/8.10.1
> Accept: */*
> Content-Length: 43
> Content-Type: application/x-www-form-urlencoded
>
* upload completely sent off: 43 bytes
< HTTP/1.1 200 OK
< content-length: 27
< connection: close
< content-type: text/plain
<
Got 43 bytes of your data!
* shutting down connection #0
```
```text
[INFO] 30-03-2025 13-36-36 - Server listening on port localhost:42069
[INFO] 30-03-2025 13-36-36 - Listening for incoming connections
Got request from POST /POST_some_data
Headers: {'host': 'localhost:42069', 'user-agent': 'curl/8.10.1', 'accept': '*/*', 'content-length': '43', 'content-type': 'application/x-www-form-urlencoded'}
Body: This is some test data I'm sending via POST
[DEBUG] 30-03-2025 13-36-52 - New connection from ('127.0.0.1', 54850)
[DEBUG] 30-03-2025 13-36-52 - Handling connection from 127.0.0.1:54850
[DEBUG] 30-03-2025 13-36-52 - Reading request from 127.0.0.1:54850
[DEBUG] 30-03-2025 13-36-52 - Request from 127.0.0.1:54850: POST /POST_some_data
[DEBUG] 30-03-2025 13-36-52 - Calling handler for POST /POST_some_data
[INFO] 30-03-2025 13-36-52 - Handler completed successfully for 127.0.0.1:54850
[DEBUG] 30-03-2025 13-36-52 - Closing connection with 127.0.0.1:54850
```

## Features

This server also supports:
- [`Chunked-Encoding`](https://en.wikipedia.org/wiki/Chunked_transfer_encoding) for efficient streaming of data
- [`Trailer` headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Trailer) for sending metadata after the message body

## Acknowledgements

- [Learn the `HTTP` protocol](https://www.boot.dev/courses/learn-http-protocol-golang) on [Boot.dev](https://www.boot.dev/courses/learn-http-protocol-golang)
