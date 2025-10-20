# ...existing code...
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Union

import mouse
from pynput import keyboard as pynput_keyboard


DEFAULT_POSITIONS = [
    {"x": 430, "y": 13},
    {"x": 1683, "y": 13},
    {"x": 430, "y": 810},
    {"x": 1683, "y": 810},
]


class WowClient:
    def __init__(self, host: str = "26.16.153.117", port: int = 5000, cfg_path: Union[str, Path] = "windows.json"):
        self.host = host
        self.port = port
        self._writer = None  # Add this line
        self.cfg_path = Path(cfg_path)
        self.windows: List[Dict[str, int]] = self.load_windows()
        self.key = "."
        self.kb = pynput_keyboard.Controller()
        self.running = True
        self._lock = asyncio.Lock()

    def load_windows(self) -> List[Dict[str, int]]:
        try:
            if not self.cfg_path.exists():
                return []
                
            data = json.loads(self.cfg_path.read_text())
            wins = data.get("windows", [])
            
            # validate entries and ensure minimum 2 windows
            validated = []
            for w in wins:
                if isinstance(w, dict) and "x" in w and "y" in w:
                    validated.append({"x": int(w["x"]), "y": int(w["y"])})
                    
            # Return empty list if less than 2 valid windows
            return validated if len(validated) >= 2 else []
            
        except Exception:
            return []

    async def press_key(self, key: str):
        # use to_thread because pynput is blocking
        await asyncio.to_thread(self.kb.press, key)
        await asyncio.sleep(0.02)
        await asyncio.to_thread(self.kb.release, key)
        await asyncio.sleep(0.02)
        # press again (keeps old behavior)
        await asyncio.to_thread(self.kb.press, key)
        await asyncio.sleep(0.02)
        await asyncio.to_thread(self.kb.release, key)

    async def click_at(self, x: int, y: int):
        # wrap mouse operations in thread to avoid blocking event loop
        await asyncio.to_thread(lambda: mouse.move(x, y, absolute=True, duration=0.002))
        await asyncio.sleep(0.07)
        await asyncio.to_thread(mouse.click)
        await asyncio.sleep(0.07)

    async def bot_loop(self):
        # main bot loop uses async sleeps and offloads mouse/keyboard to threads
        while self.running:
            async with self._lock:
                key = self.key
                windows = list(self.windows)

            if not key or key == ".":
                await asyncio.sleep(0.05)
                continue

            single_window = len(windows) == 1
            for pos in windows:
                if not single_window:
                    await self.click_at(pos["x"], pos["y"])
                # small gap before keypress to mimic original timing
                await asyncio.sleep(0.01)
                await self.press_key(key)
                # tiny pause between windows
                await asyncio.sleep(0.01)

            # little rest before next cycle
            await asyncio.sleep(0.05)

    async def network_loop(self):
        while self.running:
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
                self._writer = writer  # Add this line
                logging.info("Connected to server %s:%s", self.host, self.port)
                message = "Check Server Alive"
                
                while self.running:
                    try:
                        writer.write(message.encode())
                        await writer.drain()
                        data = await reader.read(1024)
                        if not data:
                            logging.info("Server closed connection")
                            break
                        resp = data.decode().strip()
                        if resp:
                            async with self._lock:
                                self.key = resp
                            logging.info("Server Asked To Spam Key: ( %s )", resp)
                        await asyncio.sleep(0.2)
                    except (ConnectionResetError, BrokenPipeError):
                        logging.info("Connection lost, retrying...")
                        break
                
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                
            except Exception as e:
                self._writer = None  # Add this line
                logging.error("Failed to connect: %s", e)
                # Wait before retry
                await asyncio.sleep(2)
                continue

    async def run(self):
        bot = asyncio.create_task(self.bot_loop())
        net = asyncio.create_task(self.network_loop())
        try:
            await asyncio.wait([bot, net], return_when=asyncio.FIRST_COMPLETED)
        finally:
            self.running = False
            bot.cancel()
            net.cancel()
            await asyncio.sleep(0)  # yield

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    client = WowClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logging.info("Shutting down client")
# ...existing code...