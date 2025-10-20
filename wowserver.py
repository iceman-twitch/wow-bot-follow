# ...existing code...
import asyncio
import socket
import logging
import threading
import keyboard

class WowServer:
    def __init__(self):
        self.host = socket.gethostname()
        self.port = 5000
        self.running = True
        self.key = "."
        self.table = {
            "1","2","3","4","5","6","x","y","í","0","q","e","r","g",
            "f","u","t",".",
        }
        self._lock = threading.Lock()

    def on_keypress(self, event):
        # keyboard.on_press callback runs in keyboard library's thread.
        with self._lock:
            if event.name == 'á':
                self.running = False
            elif event.name == 'é':
                self.running = True
            elif event.name in self.table:
                self.key = event.name

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logging.info("Connection from: %s", addr)
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                incoming = data.decode()
                logging.info("from connected user: %s", incoming)

                # small delay to mimic original behavior
                await asyncio.sleep(0.2)

                with self._lock:
                    running = self.running
                    key = self.key

                if running and key in self.table:
                    send = key
                    logging.info("(Keyhook Enabled) Sending Key: %s", send)
                else:
                    send = "."
                    logging.info("(Keyhook Disabled) Sending Key: %s", send)

                writer.write(send.encode())
                await writer.drain()
        except (asyncio.CancelledError, ConnectionResetError) as e:
            logging.info("Client %s disconnected: %s", addr, e)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logging.info("Closed connection: %s", addr)

    async def start(self):
        # register keyboard hook (keyboard lib runs its own thread)
        keyboard.on_press(self.on_keypress)

        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        logging.info("Serving on %s", addr)
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("Starting Method")

    srv = WowServer()
    try:
        asyncio.run(srv.start())
    except KeyboardInterrupt:
        logging.info("Server shutting down")
# ...existing code...