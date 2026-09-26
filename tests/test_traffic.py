import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from traffic import run


def test_traffic_counts_real_success_and_failure():
    class Handler(BaseHTTPRequestHandler):
        requests = 0

        def do_GET(self):
            Handler.requests += 1
            if Handler.requests % 2:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"version": "test", "hostname": "pod", "timestamp": "now"}).encode())
            else:
                self.send_response(503)
                self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = run(f"http://127.0.0.1:{server.server_port}", 0.1, 0.005, 1)
        assert report["successful"] > 0 and report["failed"] > 0
        assert report["total"] == report["successful"] + report["failed"]
        assert report["versions"] == {"test": report["successful"]}
        assert report["latency_ms"]["max"] >= report["latency_ms"]["p95"] > 0
    finally:
        server.shutdown()
        server.server_close()
