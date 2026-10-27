#!/usr/bin/env python3
"""
Aplica Opal - serviço local para inventário de dispositivos numa rede autorizada.
Usa apenas a biblioteca padrão do Python. Limitado a 192.168.0.1–192.168.1.254.
Não tenta autenticar-se nem aceder a vídeo; identifica apenas portas TCP acessíveis.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import ipaddress
import json
import socket
import threading
import time
import os

HOST = "127.0.0.1"
PORT = 8765
ALLOWED_START = int(ipaddress.ip_address("192.168.0.1"))
ALLOWED_END = int(ipaddress.ip_address("192.168.1.254"))
SCAN_LOCK = threading.Lock()
SCANNING = False

PORT_HINTS = {
    80: "HTTP / interface web",
    443: "HTTPS / interface web",
    554: "RTSP / possível vídeo",
    8000: "HTTP alternativo / possível dispositivo",
    8080: "HTTP alternativo",
    8899: "Porta usada por alguns dispositivos",
}

def parse_ip(value):
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        raise ValueError(f"IP inválido: {value}")
    if ip.version != 4 or int(ip) < ALLOWED_START or int(ip) > ALLOWED_END:
        raise ValueError("O IP tem de estar entre 192.168.0.1 e 192.168.1.254.")
    return ip

def check_port(ip, port, timeout=0.22):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((str(ip), port)) == 0
    except OSError:
        return False

def inspect_host(ip):
    open_ports = []
    for port in PORT_HINTS:
        if check_port(ip, port):
            open_ports.append({"port": port, "service": PORT_HINTS[port]})
    if not open_ports:
        return None
    return {
        "ip": str(ip),
        "ports": open_ports,
        "classification": "Possível câmara/dispositivo de rede",
        "verified_camera": False,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def log_message(self, fmt, *args):
        print("[Aplica Opal] " + (fmt % args))

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            return self.send_json(200, {
                "service": "Aplica Opal Local",
                "status": "running",
                "bind": f"{HOST}:{PORT}",
                "range": "192.168.0.1 - 192.168.1.254",
                "note": "Portas abertas são indícios; não confirmam que o dispositivo é uma câmara."
            })
        if path == "/api/scan":
            return self.send_json(405, {"error": "Usa POST para iniciar uma verificação."})
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        global SCANNING
        path = urlparse(self.path).path
        if path != "/api/scan":
            return self.send_json(404, {"error": "Endpoint não encontrado."})

        # Limitar tamanho do pedido.
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096:
                return self.send_json(413, {"error": "Pedido demasiado grande."})
            payload = json.loads(self.rfile.read(length) or b"{}")
            start = parse_ip(payload.get("start", "192.168.0.1"))
            end = parse_ip(payload.get("end", "192.168.1.254"))
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_json(400, {"error": str(e)})

        if int(start) > int(end):
            return self.send_json(400, {"error": "O IP inicial deve ser anterior ao IP final."})
        count = int(end) - int(start) + 1
        if count > 510:
            return self.send_json(400, {"error": "O intervalo máximo é de 510 endereços."})

        with SCAN_LOCK:
            if SCANNING:
                return self.send_json(409, {"error": "Já existe uma verificação em curso."})
            SCANNING = True

        started = time.time()
        results = []
        try:
            addresses = [ipaddress.ip_address(n) for n in range(int(start), int(end) + 1)]
            # Concorrência moderada e apenas portas comuns de gestão/vídeo.
            with ThreadPoolExecutor(max_workers=48) as pool:
                futures = {pool.submit(inspect_host, ip): ip for ip in addresses}
                for future in as_completed(futures):
                    try:
                        item = future.result()
                        if item:
                            results.append(item)
                    except Exception:
                        pass
            results.sort(key=lambda x: int(ipaddress.ip_address(x["ip"])))
        finally:
            with SCAN_LOCK:
                SCANNING = False

        return self.send_json(200, {
            "range": f"{start} - {end}",
            "addresses_checked": count,
            "devices_with_matching_ports": len(results),
            "duration_seconds": round(time.time() - started, 2),
            "results": results,
            "warning": "Isto é uma descoberta por portas TCP. Não confirma a identidade da câmara nem verifica ONVIF/RTSP."
        })

if __name__ == "__main__":
    print(f"Aplica Opal Local disponível em http://{HOST}:{PORT}")
    print("Apenas verifica o intervalo privado 192.168.0.1–192.168.1.254.")
    print("Mantém esta janela aberta enquanto usas a aplicação. Ctrl+C para parar.")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nA encerrar serviço...")
    finally:
        server.server_close()
