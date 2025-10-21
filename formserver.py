import threading
import asyncio
import logging
import tkinter as tk
from tkinter import ttk
from wowserver import WowServer

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")

class FormServerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WoW Bot Server Controller")

        self.server: WowServer | None = None
        self.thread: threading.Thread | None = None

        main = ttk.Frame(root, padding=10)
        main.grid(sticky="nsew")

        # Server info display
        ttk.Label(main, text="Server IP:").grid(column=0, row=0, sticky="w")
        self.ip_var = tk.StringVar(value="Detecting...")
        ttk.Label(main, textvariable=self.ip_var).grid(column=1, row=0, sticky="w")

        ttk.Label(main, text="Port:").grid(column=0, row=1, sticky="w")
        self.port_var = tk.StringVar(value="5000")
        ttk.Entry(main, textvariable=self.port_var, width=10).grid(column=1, row=1, sticky="w")

        # Control buttons
        self.start_btn = ttk.Button(main, text="Start Server", command=self.start_server)
        self.start_btn.grid(column=0, row=2, sticky="ew", pady=(10, 0))
        
        self.stop_btn = ttk.Button(main, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_btn.grid(column=1, row=2, sticky="ew", pady=(10, 0))

        # Status display
        ttk.Label(main, text="Status:").grid(column=0, row=3, sticky="w", pady=(10, 0))
        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(main, textvariable=self.status_var).grid(column=1, row=3, sticky="w", pady=(10, 0))

        # Key display
        ttk.Label(main, text="Current Key:").grid(column=0, row=4, sticky="w", pady=(10, 0))
        self.key_var = tk.StringVar(value="None")
        ttk.Label(main, textvariable=self.key_var).grid(column=1, row=4, sticky="w", pady=(10, 0))

        # Help text
        help_text = "Press keys 1-6, x, y, í, 0, q, e, r, g, f, u, t to send commands\nPress '-' to pause, ',' to resume"
        ttk.Label(main, text=help_text).grid(column=0, row=5, columnspan=2, pady=(10, 0))

        for i in range(2):
            main.columnconfigure(i, weight=1)

        # Update IP address
        self.update_ip()

    def update_ip(self):
        import socket
        try:
            # Get IPv4 address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Doesn't need to be reachable
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except Exception:
                ip = '127.0.0.1'
            finally:
                s.close()
            self.ip_var.set(ip)
        except Exception:
            self.ip_var.set("Could not detect IP")

    def start_server(self):
        if self.thread and self.thread.is_alive():
            return

        try:
            port = int(self.port_var.get())
        except ValueError:
            self.status_var.set("Invalid port number")
            return

        self.server = WowServer()
        self.server.port = port

        def run_server():
            try:
                asyncio.run(self.server.start())
            except Exception as e:
                logging.exception("Server thread exception: %s", e)
            finally:
                self.root.after(0, self._on_thread_exit)

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Starting...")

        self.root.after(200, self._update_status)

    def stop_server(self):
        if not self.server:
            return
        self.status_var.set("Stopping...")
        try:
            self.server.running = False
        except Exception:
            pass

        if self.thread:
            self.thread.join(timeout=2)

        self._on_thread_exit()

    def _on_thread_exit(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopped")
        self.key_var.set("None")
        self.server = None
        self.thread = None

    def _update_status(self):
        if self.thread and self.thread.is_alive():
            if self.server:
                self.status_var.set("Running")
                self.key_var.set(self.server.key)
            else:
                self.status_var.set("Starting...")
            self.root.after(500, self._update_status)
        else:
            if self.server:
                self.status_var.set("Stopped")
            else:
                self.status_var.set("Offline")
            self.key_var.set("None")

def main():
    root = tk.Tk()
    app = FormServerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()