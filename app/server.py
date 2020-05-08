"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                duplicated_login = False
                for client in self.server.clients:
                    if client.login == login:
                        duplicated_login = True
                        self.transport.write(
                            f"Логин {login} занят, попробуйте другой".encode()
                        )
                        self.connection_lost()
                else:
                    if not duplicated_login:
                        self.login = login
                        self.send_history()
                        self.transport.write(
                            f"Привет, {self.login}!".encode()
                        )
        else:
            self.server.history.append(f"{self.login} {decoded}")
            self.send_message(decoded)

    def send_history(self):
        if len(self.server.history) > 10:
            send_history_len = len(self.server.history)-10
        else:
            send_history_len = 0
        for i in range(send_history_len, len(self.server.history), 1):
            self.transport.write(self.server.history[i].encode())

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        self.transport.close()
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
