import logging
import signal
import socket
import threading
from types import FrameType
from typing import Callable

from request import Request, request_from_reader
from response_writer import Writer
from responses import StatusCode, get_default_headers

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H-%M-%S",
)

logger = logging.getLogger(__name__)

Handler = Callable[[Writer, Request], None]

class Server:
    def __init__(self, listener: socket, connection_timeout: int = 30) -> None:
        self.listener: socket = listener
        self.path_handlers: dict[str, Handler] = {}
        self.running: bool = True
        self.threads: list[threading.Thread] = []
        self.connection_timeout = connection_timeout
        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)

    def __signal_handler(self, sig: int, frame: FrameType) -> None:
        logger.info(f"Received signal {sig}, shutting down...")
        self.close()

    def register_handler(self, path: str, handler: Handler) -> None:
        self.path_handlers[path] = handler

    def close(self) -> None:
        logger.info("Initiating server shutdown...")
        self.running = False

        try:
            self.listener.close()
        except Exception as e:
            logger.error(f"Error closing listener socket: {e}")

        active_threads = [t for t in self.threads if t.is_alive()]
        if active_threads:
            logger.info(
                f"Waiting for {len(active_threads)} active connections to complete..."
            )
            for t in active_threads:
                t.join(timeout=2.0)

            remaining = [t for t in active_threads if t.is_alive()]
            if remaining:
                logger.warning(
                    f"{len(remaining)} connections did not complete gracefully"
                )

        logger.info("Server shutdown complete. Goodbye!")

    def listen(self) -> None:
        self.running = True
        logger.info("Listening for incoming connections")
        self.listener.settimeout(1.0)

        while self.running:
            try:
                conn, addr = self.listener.accept()
                logger.debug(f"New connection from {addr}")

                conn.settimeout(self.connection_timeout)

                thread = threading.Thread(target=self.__handle, args=(conn, addr))
                thread.daemon = True
                self.threads = [t for t in self.threads if t.is_alive()]
                self.threads.append(thread)
                thread.start()
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    logger.error(f"Socket error: {e}")
                continue

    def __send_error_response(
        self, w: Writer, status_code: StatusCode, message: str
    ) -> None:
        logger.error(f"Sending error response: {message}")
        headers = get_default_headers(len(message))
        try:
            w.write_status_line(status_code)
            w.write_headers(headers)
            w.write_body(message)
        except Exception as e:
            logger.error(f"Error sending response: {e}")

    def __handle(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        client_id = f"{addr[0]}:{addr[1]}"
        logger.debug(f"Handling connection from {client_id}")
        w = None

        try:
            w = Writer(conn)

            try:
                logger.debug(f"Reading request from {client_id}")
                r = request_from_reader(conn)
                method = r.request_line.method
                path = r.request_line.request_target
                logger.debug(f"Request from {client_id}: {method} {path}")
            except socket.timeout:
                logger.warning(
                    f"Connection timeout while reading request from {client_id}"
                )
                self.__send_error_response(
                    w, StatusCode.INTERNAL_SERVER_ERROR, "Request timed out"
                )
                return
            except Exception as e:
                logger.error(f"Error parsing request from {client_id}: {e}")
                self.__send_error_response(
                    w, StatusCode.BAD_REQUEST, f"Error parsing request: {e}"
                )
                return

            try:
                handler = self.path_handlers.get(r.request_line.request_target)

                if not handler:
                    logger.warning(f"No handler found for {method} {path}")
                    error_msg = f"Path '{path}' not found for method {method}"
                    self.__send_error_response(w, StatusCode.NOT_FOUND, error_msg)
                    return

                logger.debug(f"Calling handler for {method} {path}")
                handler(w, r)
                logger.info(f"Handler completed successfully for {client_id}")

            except Exception as e:
                logger.error(f"Unhandled error in handler for {client_id}: {e}")
                self.__send_error_response(
                    w, StatusCode.INTERNAL_SERVER_ERROR, f"Internal server error: {e!s}"
                )

        except Exception as e:
            logger.error(f"Unexpected error handling {client_id}: {e}")
            if w:
                self.__send_error_response(
                    w, StatusCode.INTERNAL_SERVER_ERROR, f"Unexpected error: {e!s}"
                )
        finally:
            try:
                logger.debug(f"Closing connection with {client_id}")
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection with {client_id}: {e}")


def serve(address: str, port: int, connection_timeout: int = 30) -> Server:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        listener.bind((address, port))
        listener.listen(5)
        logger.info(f"Server listening on port {address}:{port}")
    except OSError as e:
        listener.close()
        msg = f"Failed to start server: {e}"
        raise RuntimeError(msg) from e

    return Server(listener, connection_timeout)
