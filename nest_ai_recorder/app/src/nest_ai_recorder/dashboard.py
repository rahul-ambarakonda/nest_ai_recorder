from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


class DashboardServer:
    def __init__(self, stats_path: Path, host: str, port: int) -> None:
        self.stats_path = stats_path
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        stats_path = self.stats_path

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path == "/api/stats":
                    body = stats_path.read_text(encoding="utf-8") if stats_path.exists() else "{}"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body.encode("utf-8"))
                    return
                if self.path not in {"/", "/index.html"}:
                    self.send_response(404)
                    self.end_headers()
                    return
                body = _dashboard_html()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


def _dashboard_html() -> str:
    initial = json.dumps({"events_total": 0, "clips_total": 0})
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nest AI Recorder</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #101418; color: #eef3f8; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ font-size: 28px; margin: 0 0 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #2c3844; border-radius: 8px; padding: 16px; background: #171e25; }}
    .value {{ font-size: 32px; font-weight: 700; margin-top: 8px; }}
    pre {{ white-space: pre-wrap; border: 1px solid #2c3844; border-radius: 8px; padding: 16px; }}
  </style>
</head>
<body>
  <main>
    <h1>Nest AI Recorder</h1>
    <section class="grid">
      <div class="card">Events<div id="events" class="value">0</div></div>
      <div class="card">Clips<div id="clips" class="value">0</div></div>
    </section>
    <h2>Raw Stats</h2>
    <pre id="raw">{initial}</pre>
  </main>
  <script>
    async function refresh() {{
      const stats = await fetch('/api/stats').then((r) => r.json()).catch(() => ({{}}));
      document.getElementById('events').textContent = stats.events_total ?? 0;
      document.getElementById('clips').textContent = stats.clips_total ?? 0;
      document.getElementById('raw').textContent = JSON.stringify(stats, null, 2);
    }}
    refresh();
    setInterval(refresh, 5000);
  </script>
</body>
</html>"""

