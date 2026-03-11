from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import xml.etree.ElementTree as ET

class CallbackHandler(BaseHTTPRequestHandler):
    """Обработчик для приёма POST-уведомлений."""
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        # Пытаемся разобрать как XML
        try:
            root = ET.fromstring(post_data)
            # Преобразуем в словарь (плоский, без учёта порядка)
            data = {elem.tag: elem.text for elem in root.iter() if elem.text}
        except ET.ParseError:
            # Если не XML, сохраняем как строку
            data = {'raw': post_data.decode('utf-8')}

        # Сохраняем полученное уведомление в глобальный список
        callback_server.received.append(data)

        # Отвечаем "ok" (text/plain) как требует ПЦ
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, format, *args):
        pass  # отключаем логи

class CallbackServer:
    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.received = []

    def start(self):
        """Запускает сервер в отдельном потоке."""
        self.server = HTTPServer((self.host, self.port), CallbackHandler)
        self.port = self.server.server_port  # реальный порт
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        return self

    def stop(self):
        """Останавливает сервер."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()

    def clear(self):
        """Очищает список полученных уведомлений."""
        self.received.clear()

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/callback"

# Глобальный экземпляр для доступа из хендлера
callback_server = CallbackServer()