# ...existing code...
import asyncio
import socket
import logging
import threading
import keyboard

class WowServer:
    def __init__(self):
        self.host = "0.0.0.0"  # Changed from socket.gethostname() to explicitly bind to all IPv4 interfaces
        self.port = 5000
        self.running = True
        self.key = "."
        self.table = {
            "1","2","3","4","5","6","x","y","í","0","q","e","r","g",
            "f","u","t",".",
        }
        self._lock = threading.Lock()
        self._send_limit = 3
        self._current_key = None
        self._send_count = 0
        self._key_ready = True  # Flag to indicate if we're ready for a new key

    def on_keypress(self, event):
        with self._lock:
            if event.name in self.table and self._key_ready:
                # Only accept new key if we're ready
                self.key = event.name
                self._current_key = event.name
                self._send_count = 0
                self._key_ready = False  # Mark that we're processing this key

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
                    if self._current_key and not self._key_ready:
                        if self._send_count < self._send_limit:
                            send = self._current_key
                            self._send_count += 1
                            logging.info(f"Sending key: {send} (press {self._send_count}/3)")
                            
                            if self._send_count >= self._send_limit:
                                self._key_ready = True  # Ready for next key
                                self._current_key = None
                                logging.info("3 presses complete - ready for next key")
                        else:
                            send = "."
                    else:
                        send = "."
                        if self._key_ready:
                            logging.info("Waiting for new key")
                        
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
        
        try:
            server = await asyncio.start_server(
                self.handle_client, 
                self.host, 
                self.port,
                family=socket.AF_INET  # Force IPv4
            )
            addr = server.sockets[0].getsockname()
            logging.info("Serving on %s", addr)
            
            async with server:
                await server.serve_forever()
        except Exception as e:
            logging.error("Server failed to start: %s", e)
            raise


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("Starting Method")

    srv = WowServer()
    try:
        asyncio.run(srv.start())
    except KeyboardInterrupt:
        logging.info("Server shutting down")