import os
import re
import sys
import socket
import urllib.parse
import logging
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http import HTTPStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")


class RangeHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

    def log_error(self, format, *args):
        logger.error(f"{self.client_address[0]} - {format % args}")

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts.scheme, parts.netloc, parts.path + '/',
                             parts.query, parts.fragment)
                self.send_header("Location", urllib.parse.urlunsplit(new_parts))
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index_path = os.path.join(path, index)
                if os.path.exists(index_path):
                    return self.send_file_response(index_path)
            return self.list_directory(path)

        ctype = self.guess_type(path)
        if not os.path.exists(path):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None

        return self.send_file_response(path, ctype)

    def send_file_response(self, path, ctype=None):
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        if ctype is None:
            ctype = self.guess_type(path)

        fs = os.fstat(f.fileno())
        file_size = fs.st_size
        range_header = self.headers.get('Range')

        if range_header:
            return self.send_partial_content(f, file_size, ctype, range_header)

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

    def send_partial_content(self, f, file_size, ctype, range_header):
        match = re.match(r'bytes=(\d+)-(\d*)$', range_header)
        if not match:
            f.close()
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid Range header")
            return None

        start = int(match.group(1))
        end_str = match.group(2)
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size:
            f.close()
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            return None

        end = min(end, file_size - 1)
        content_length = end - start + 1

        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Last-Modified", self.date_time_string(os.fstat(f.fileno()).st_mtime))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        f.seek(start)
        return FileSegmentedWrapper(f, start, end, self)

    def do_GET(self):
        if self.path == '/@vite/client':
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if self.path.startswith('/@vite/'):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                logger.debug(f"Client disconnected during transfer: {self.client_address}")
            finally:
                f.close()

    def do_HEAD(self):
        if self.path.startswith('/@vite'):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        f = self.send_head()
        if f:
            f.close()

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, socket.error):
            pass


class FileSegmentedWrapper:
    def __init__(self, fileobj, start, end, handler):
        self.fileobj = fileobj
        self.start = start
        self.end = end
        self.handler = handler
        self.remaining = end - start + 1

    def read(self, size=-1):
        if self.remaining <= 0:
            return b''
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.fileobj.read(size)
        if data:
            self.remaining -= len(data)
        return data

    def __getattr__(self, name):
        return getattr(self.fileobj, name)

    def close(self):
        self.fileobj.close()


def run_server(host="0.0.0.0", port=8080, directory=None):
    if directory:
        os.chdir(directory)

    server = HTTPServer((host, port), RangeHTTPRequestHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    logger.info(f"Server started at http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    logger.info(f"Serving directory: {os.getcwd()}")
    logger.info(f"Audio Range Requests (HTTP 206) — supported")
    logger.info(f"Connection reset errors — gracefully suppressed")
    logger.info(f"Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    directory = os.getenv("DIR", None)

    run_server(host=host, port=port, directory=directory)
