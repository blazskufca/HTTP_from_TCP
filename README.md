# TCP to HTTP ![CI/CD Pipeline](https://github.com/blazskufca/HTTP_from_TCP/actions/workflows/ci.yml/badge.svg)

***This project implements a simple [Go](https://go.dev/)-like threaded [`HTTP 1.1`](https://datatracker.ietf.org/doc/html/rfc9112)
server in Python.***

## Install
You can install the package by running: `pip install git+ssh://git@github.com/blazskufca/HTTP_from_TCP.git`

## Usage

If you're familiar with the [Go `net/http`](https://pkg.go.dev/net/http) package, this should feel quite familiar.

### Serving HTML 

```python
import hashlib

import requests

from tcp_to_http import (
    Headers,
    Request,
    Server,
    StatusCode,
    Writer,
    get_default_headers,
)


def say_hello(w: Writer, r: Request) -> None:
    print("Got request from", r.request_line.method, r.request_line.request_target)
    print("Headers:", r.headers)
    print("Body:", r.body.decode())
    response_body = "<h1>Hello, World!</h1>"
    headers = get_default_headers(len(response_body))
    headers["content-type"] = "text/html"
    w.write_status_line(StatusCode.OK)
    w.write_headers(headers)
    w.write_body(response_body)


def curl_POST(w: Writer, r: Request) -> None:
    print("Got request from", r.request_line.method, r.request_line.request_target)
    print("Headers:", r.headers)
    print("Body:", r.body.decode())
    response_body = f"Got {len(r.body)} bytes of your data!\n"
    headers = get_default_headers(len(response_body))
    w.write_status_line(StatusCode.OK)
    w.write_headers(headers)
    w.write_body(response_body)


def proxy_handler(w: Writer, r: Request) -> None:
    target = r.request_line.request_target.replace("/httpbin/", "")
    url = f"https://httpbin.org/{target}"
    print(f"Proxying to {url}")

    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    w.write_status_line(StatusCode.OK)

    content_type = resp.headers.get("content-type", "text/plain")

    h = get_default_headers(0)
    h["content-type"] = content_type
    h["transfer-encoding"] = "chunked"
    if "content-length" in h:
        del h["content-length"]

    if target == "html":
        h["trailers"] = "X-Content-SHA256"
        h["trailers"] = "X-Content-Length"
    w.write_headers(h)

    full_body = bytearray()
    max_chunk_size = 1024

    for chunk in resp.iter_content(chunk_size=max_chunk_size):
        if chunk:
            print(f"Read {len(chunk)} bytes")
            w.write_chunked_body(chunk)
            full_body.extend(chunk)

    if "trailers" in h:
        trailers = Headers()
        trailers["X-Content-SHA256"] = hashlib.sha256(full_body).hexdigest()
        trailers["X-Content-Length"] = str(len(full_body))
        w.write_trailers(trailers)
    else:
        w.write_chunked_body_done()


if __name__ == "__main__":
    s = Server("", 42069)
    s.register_handler("/hello", say_hello)
    s.register_handler("/POST_some_data", curl_POST)
    s.register_handler("/httpbin/stream/100", proxy_handler)
    s.register_handler("/httpbin/html", proxy_handler)
    s.run()
```

![Serving `HTML` pages](https://github.com/user-attachments/assets/7087a584-fff4-4ebb-89e6-52026b80f74f)


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

### `Trailer` headers
```shell
curl.exe --raw localhost:42069/httpbin/html
```

```text
400
<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
      <h1>Herman Melville - Moby-Dick</h1>

      <div>
        <p>
          Availing himself of the mild, summer-cool weather that now reigned in these latitudes, and in preparatio
n for the peculiarly active pursuits shortly to be anticipated, Perth, the begrimed, blistered old blacksmith, had
 not removed his portable forge to the hold again, after concluding his contributory work for Ahab's leg, but stil
l retained it on deck, fast lashed to ringbolts by the foremast; being now almost incessantly invoked by the heads
men, and harpooneers, and bowsmen to do some little job for them; altering, or repairing, or new shaping their var
ious weapons and boat furniture. Often he would be surrounded by an eager circle, all waiting to be served; holdin
g boat-spades, pike-heads, harpoons, and lances, and jealously watching his every sooty movement, as he toiled. Nevertheless, this old man's was a patient hammer wielded by a patient arm. No murmur, no impatience, no petu       
400
lance did come from him. Silent, slow, and solemn; bowing over still further his chronically broken back, he toile
d away, as if toil were life itself, and the heavy beating of his hammer the heavy beating of his heart. And so it
 was.—Most miserable! A peculiar walk in this old man, a certain slight but painful appearing yawing in his gait, 
had at an early period of the voyage excited the curiosity of the mariners. And to the importunity of their persis
ted questionings he had finally given in; and so it came to pass that every one now knew the shameful story of his
 wretched fate. Belated, and not innocently, one bitter winter's midnight, on the road running between two country
 towns, the blacksmith half-stupidly felt the deadly numbness stealing over him, and sought refuge in a leaning, d
ilapidated barn. The issue was, the loss of the extremities of both feet. Out of this revelation, part by part, at last came out the four acts of the gladness, and the one long, and as yet uncatastrophied fifth act of the gr    
400
ief of his life's drama. He was an old man, who, at the age of nearly sixty, had postponedly encountered that thin
g in sorrow's technicals called ruin. He had been an artisan of famed excellence, and with plenty to do; owned a h
ouse and garden; embraced a youthful, daughter-like, loving wife, and three blithe, ruddy children; every Sunday w
ent to a cheerful-looking church, planted in a grove. But one night, under cover of darkness, and further conceale
d in a most cunning disguisement, a desperate burglar slid into his happy home, and robbed them all of everything.
 And darker yet to tell, the blacksmith himself did ignorantly conduct this burglar into his family's heart. It wa
s the Bottle Conjuror! Upon the opening of that fatal cork, forth flew the fiend, and shrivelled up his home. Now,
 for prudent, most wise, and economic reasons, the blacksmith's shop was in the basement of his dwelling, but with a separate entrance to it; so that always had the young and loving healthy wife listened with no unhappy nervou  
29d
sness, but with vigorous pleasure, to the stout ringing of her young-armed old husband's hammer; whose reverberati
ons, muffled by passing through the floors and walls, came up to her, not unsweetly, in her nursery; and so, to st
out Labor's iron lullaby, the blacksmith's infants were rocked to slumber. Oh, woe on woe! Oh, Death, why canst th
ou not sometimes be timely? Hadst thou taken this old blacksmith to thyself ere his full ruin came upon him, then 
had the young widow had a delicious grief, and her orphans a truly venerable, legendary sire to dream of in their after years; and all of them a care-killing competency.
        </p>
      </div>
  </body>
</html>
0
x-content-sha256: 3f324f9914742e62cf082861ba03b207282dba781c3349bee9d7c1b5ef8e0bfe
x-content-length: 3741
```
```text
[DEBUG] 31-03-2025 18-29-55 - Trying to start server...
[DEBUG] 31-03-2025 18-29-55 - Using proactor: IocpProactor
[INFO] 31-03-2025 18-29-55 - Server running on :42069
Proxying to https://httpbin.org/html
[DEBUG] 31-03-2025 18-32-25 - New connection from ::1:56390
[DEBUG] 31-03-2025 18-32-25 - Awaiting request from ::1:56390
[DEBUG] 31-03-2025 18-32-25 - Received request from ::1:56390: GET /httpbin/html
[DEBUG] 31-03-2025 18-32-25 - Starting new HTTPS connection (1): httpbin.org:443
[DEBUG] 31-03-2025 18-32-26 - https://httpbin.org:443 "GET /html HTTP/1.1" 200 3741
Read 1024 bytes
Read 1024 bytes
Read 1024 bytes
Read 669 bytes
```
### Chunked Encoding

```shell
curl.exe --raw localhost:42069/httpbin/stream/10
```
```text
11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 0}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 1}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 2}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 3}

236
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 4}
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 5}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 6}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 7}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 8}

11b
{"url": "https://httpbin.org/stream/10", "args": {}, "headers": {"Host": "httpbin.org", "X-Amzn-Trace-Id": "Root=1
-67eac4b6-0a47252915dd843c1bf4eb82", "User-Agent": "python-requests/2.32.3", "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}, "origin": "146.212.160.157", "id": 9}

0

```
```text
[DEBUG] 31-03-2025 18-37-07 - Trying to start server...
[DEBUG] 31-03-2025 18-37-07 - Using proactor: IocpProactor
[INFO] 31-03-2025 18-37-07 - Server running on :42069
Proxying to https://httpbin.org/stream/10
[DEBUG] 31-03-2025 18-37-10 - New connection from ::1:56503
[DEBUG] 31-03-2025 18-37-10 - Awaiting request from ::1:56503
[DEBUG] 31-03-2025 18-37-10 - Received request from ::1:56503: GET /httpbin/stream/10
[DEBUG] 31-03-2025 18-37-10 - Starting new HTTPS connection (1): httpbin.org:443
[DEBUG] 31-03-2025 18-37-11 - https://httpbin.org:443 "GET /stream/10 HTTP/1.1" 200 None
Read 283 bytes
Read 283 bytes
Read 283 bytes
Read 283 bytes
Read 566 bytes
Read 283 bytes
Read 283 bytes
Read 283 bytes
Read 283 bytes
```

## Features

This server also supports:
- [`Chunked-Encoding`](https://en.wikipedia.org/wiki/Chunked_transfer_encoding) for efficient streaming of data
- [`Trailer` headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Trailer) for sending metadata after the message body

## Acknowledgements

- [Learn the `HTTP` protocol](https://www.boot.dev/courses/learn-http-protocol-golang) on [Boot.dev](https://www.boot.dev/courses/learn-http-protocol-golang)
