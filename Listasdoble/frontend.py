import json
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bacterial_generation import BacterialGeneration
from mutation_history import MutationHistory


INDEX_FILE = Path(__file__).with_name("index.html")


def generation_data(generation):
    if generation is None:
        return None
    return {
        "number": generation.number,
        "mutation": generation.mutation,
        "mutation_type": generation.mutation_type,
        "date": generation.date,
        "observation": generation.observation,
    }


class MutationRequestHandler(BaseHTTPRequestHandler):
    history = MutationHistory()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_FILE.read_bytes())
            return

        if parsed.path == "/api/state":
            generations = self.history.forward_list()
            self.send_json(200, {
                "current": generation_data(self.history.current),
                "generations": [generation_data(item) for item in generations],
                "first": generations[0].number if generations else None,
                "last": generations[-1].number if generations else None,
            })
            return

        if parsed.path == "/api/history":
            order = parse_qs(parsed.query).get("order", ["forward"])[0]
            generations = (self.history.backward_list() if order == "reverse"
                           else self.history.forward_list())
            self.send_json(200, {"generations": [generation_data(item) for item in generations]})
            return

        self.send_json(404, {"error": "Ruta no encontrada."})

    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            action = urlparse(self.path).path
            if action == "/api/generations":
                result = self.add_generation(payload)
            elif action == "/api/search":
                result = self.search_generation(payload)
            elif action == "/api/navigate":
                result = self.navigate(payload)
            elif action == "/api/delete":
                result = self.delete_generation()
            else:
                self.send_json(404, {"error": "Ruta no encontrada."})
                return
            self.send_json(200, result)
        except (ValueError, TypeError, KeyError) as error:
            self.send_json(400, {"error": str(error)})

    def add_generation(self, payload):
        try:
            number = int(payload.get("number", ""))
        except (ValueError, TypeError):
            raise ValueError("El número de generación debe ser un entero.") from None
        if number < 0:
            raise ValueError("El número de generación no puede ser negativo.")
        mutation = str(payload.get("mutation", "")).strip()
        if not mutation:
            raise ValueError("Describe la mutación antes de guardar.")
        if self.history.search(number) is not None:
            raise ValueError(f"La generación {number} ya existe.")

        generation = BacterialGeneration(
            number,
            mutation,
            str(payload.get("mutation_type", "")).strip(),
            str(payload.get("observation", "")).strip(),
            str(payload.get("date", "")).strip() or date.today().isoformat(),
        )
        if self.history.is_empty() or number > self.history.last.number:
            self.history.add(generation)
        else:
            self.history.insert(generation)
        return {"message": f"Generación {number} guardada."}

    def search_generation(self, payload):
        try:
            number = int(payload.get("number", ""))
        except (ValueError, TypeError):
            raise ValueError("Escribe un número de generación válido.") from None
        generation = self.history.search(number)
        if generation is None:
            raise ValueError(f"La generación {number} no existe.")
        self.history.current = generation
        return {"message": f"Generación {number} seleccionada."}

    def navigate(self, payload):
        direction = payload.get("direction")
        moved = (self.history.move_previous() if direction == "previous"
                 else self.history.move_next() if direction == "next" else False)
        if not moved:
            raise ValueError("No hay otra generación en esa dirección.")
        return {"message": "Generación actualizada."}

    def delete_generation(self):
        generation = self.history.current
        if generation is None:
            raise ValueError("No hay una generación seleccionada para eliminar.")
        number = generation.number
        self.history.delete(generation)
        return {"message": f"Generación {number} eliminada."}

    def send_json(self, status, data):
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def run_web_server(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), MutationRequestHandler)
    print(f"Bacterial Mutation Tracker disponible en http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()