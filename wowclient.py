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
    def __init__(self, host: str = "26.23.110.199", port: int = 5000, cfg_path: Union[str, Path] = "windows.json"):
        self.host = host
        self.port = port
        self._writer = None
        self.cfg_path = Path(cfg_path)
        self.windows: List[Dict[str, int]] = self.load_windows()
        self.key = "."
        self.kb = pynput_keyboard.Controller()
        self.running = True
        self._lock = asyncio.Lock()

    def load_windows(self) -> List[Dict[str, int]]:
        try:
            if not self.cfg_path.exists():
                logging.info("No windows.json found - running in single window mode")
                return []
                
            data = json.loads(self.cfg_path.read_text())
            wins = data.get("windows", [])
            
            # validate entries - need at least 2 valid windows
            validated = []
            for w in wins:
                if isinstance(w, dict) and "x" in w and "y" in w:
                    validated.append({"x": int(w["x"]), "y": int(w["y"])})
            
            if len(validated) < 2:
                logging.info("Less than 2 valid windows found - running in single window mode")
                return []
                
            logging.info(f"Found {len(validated)} valid windows - running in multi-window mode")
            return validated
            
        except Exception as e:
            logging.info(f"Error reading windows config: {e} - running in single window mode")
            return []

    async def press_key(self, key: str):
        logging.info(f"Pressing key: {key}")
        try:
            # More forceful press-release with longer duration
            kb = self.kb
            await asyncio.to_thread(kb.press, key)
            await asyncio.sleep(0.05)  # Hold longer
            await asyncio.to_thread(kb.release, key)
            
            # Verify the press happened
            logging.info(f"Key {key} pressed and released")
            return True
        except Exception as e:
            logging.error(f"Key press failed for {key}: {e}")
            return False

    async def click_at(self, x: int, y: int):
        # wrap mouse operations in thread to avoid blocking event loop
        await asyncio.to_thread(lambda: mouse.move(x, y, absolute=True, duration=0.002))
        await asyncio.sleep(0.07)
        await asyncio.to_thread(mouse.click)
        await asyncio.sleep(0.07)

    async def bot_loop(self):
        """
        Consume whatever was last written into self.key (may be a chunk like "1" or "111").
        For each character in that string (except '.'), perform exactly one press sequence.
        After reading the value we immediately clear self.key to "." under the same lock so
        the client will only act once per server request; if the server sends the same key
        again later it will be processed again.
        """
        try:
            while self.running:
                # grab and clear the latest server payload atomically
                async with self._lock:
                    key_chunk = self.key
                    self.key = "."

                    # snapshot windows so clicks use a stable list
                    windows = list(self.windows)

                if not key_chunk:
                    await asyncio.sleep(0.05)
                    continue

                # process each character received in the chunk
                for ch in key_chunk:
                    if ch == ".":
                        # server idle marker — ignore
                        continue

                    # perform one press for this request (single or multi-window mode)
                    if not windows:
                        logging.info(f"Single window - Processing requested key: {ch}")
                        await self.press_key(ch)
                    else:
                        logging.info(f"Multi-window - Processing requested key: {ch} for {len(windows)} windows")
                        for pos in windows:
                            await self.click_at(pos["x"], pos["y"])
                            await asyncio.sleep(0.02)
                            await self.press_key(ch)
                            await asyncio.sleep(0.02)

                # small pause to yield and avoid busy loop
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            logging.debug("bot_loop cancelled")
            raise

    async def network_loop(self):
        while self.running:
            reader = writer = None
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
                self._writer = writer
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
                    except asyncio.CancelledError:
                        # make sure we propagate cancellation so run() can handle shutdown
                        raise
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.error("Failed to connect: %s", e)
                await asyncio.sleep(2)
                continue
            finally:
                # always close writer/transport while the loop is still running
                if writer is not None:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        logging.debug("Exception while closing writer", exc_info=True)
                    finally:
                        if self._writer is writer:
                            self._writer = None

    async def run(self):
        bot = asyncio.create_task(self.bot_loop())
        net = asyncio.create_task(self.network_loop())
        tasks = [bot, net]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except asyncio.CancelledError:
            logging.debug("run() cancelled, cancelling child tasks")
            for t in tasks:
                t.cancel()
            raise
        finally:
            # request stop, cancel and await all tasks
            self.running = False
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

            # ensure any remaining writer is closed before loop ends
            if self._writer:
                try:
                    w = self._writer
                    self._writer = None
                    w.close()
                    await w.wait_closed()
                except Exception:
                    logging.debug("Exception while closing leftover writer", exc_info=True)

            # allow scheduled cleanup callbacks to run
            await asyncio.sleep(0)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")  # Changed to DEBUG level
    
    client = WowClient()
    logging.info(f"Loaded windows configuration: {client.windows}")  # Added config logging
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logging.info("Shutting down client")