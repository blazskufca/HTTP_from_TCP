import asyncio
import inspect
import signal
import sys
from typing import Callable

from .logger import get_logger
from .request import Request
from .response_writer import Writer
from .responses import StatusCode, get_default_headers

logger = get_logger(__name__)

Handler = Callable[[Writer, Request], None]

class Server:
    def __init__(self, host: str, port: int, connection_timeout: int = 30) -> None:
        self.host = host
        self.port = port
        self.connection_timeout = connection_timeout
        self.path_handlers = {}

    def register_handler(
        self, path: str, handler: Handler
    ) -> None:
        self.path_handlers[path] = handler

    async def __handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        addr = writer.get_extra_info("peername")
        client_id = f"{addr[0]}:{addr[1]}" if addr else "unknown"
        logger.debug(f"New connection from {client_id}")
        w = Writer(writer)

        try:
            logger.debug(f"Awaiting request from {client_id}")
            r = await asyncio.wait_for(
                Request.from_reader(reader), timeout=self.connection_timeout
            )
            method = r.request_line.method
            path = r.request_line.request_target
            logger.debug(f"Received request from {client_id}: {method} {path}")
            handler = self.path_handlers.get(path)
            if not handler:
                await self.__send_error_response(
                    w, StatusCode.NOT_FOUND, f"Path '{path}' not found"
                )
                drain_future = w.get_drain_future()
                if drain_future:
                    await drain_future
                return

            if inspect.iscoroutinefunction(handler):
                await handler(w, r)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, handler, w, r)

            drain_future = w.get_drain_future()
            if drain_future:
                await drain_future

        except Exception as e:
            await self.__send_error_response(
                w, StatusCode.INTERNAL_SERVER_ERROR, f"Error: {e}"
            )
            drain_future = w.get_drain_future()
            if drain_future:
                await drain_future
        finally:
            writer.close()
            await writer.wait_closed()

    async def __send_error_response(
        self, w: Writer, status_code: StatusCode, message: str
    ) -> None:
        headers = get_default_headers(len(message))
        w.write_status_line(status_code)
        w.write_headers(headers)
        w.write_body(message)

    def run(self) -> None:
        try:
            logger.debug("Trying to start server...")
            asyncio.run(self.__run_async())
        except KeyboardInterrupt:
            logger.info("Server shutdown initiated....")
        finally:
            logger.info("Server stopped cleanly....Goodbye!")

    async def __run_async(self) -> None:
        server = await asyncio.start_server(
            self.__handle_connection, self.host, self.port
        )
        logger.info(f"Server running on {self.host}:{self.port}")

        if sys.platform != "win32":
            loop = asyncio.get_running_loop()

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(self.__shutdown(server))
                )

        await server.serve_forever()

    @staticmethod
    async def __shutdown(server: asyncio.Server) -> None:
        logger.info("Shutting down server gracefully...")

        tasks = asyncio.all_tasks()
        for task in tasks:
            task.cancel()

        server.close()
        await server.wait_closed()

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Server shutdown complete.")
