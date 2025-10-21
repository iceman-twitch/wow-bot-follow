# ...existing code...
import threading
import asyncio
import json
from pathlib import Path
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from wowclient import WowClient  # must be in the same folder or on PYTHONPATH

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")


class FormClientApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WoW Bot Client Controller")

        self.client: WowClient | None = None
        self.thread: threading.Thread | None = None

        main = ttk.Frame(root, padding=10)
        main.grid(sticky="nsew")

        ttk.Label(main, text="Host:").grid(column=0, row=0, sticky="w")
        self.host_var = tk.StringVar(value="26.23.110.199")
        ttk.Entry(main, textvariable=self.host_var, width=30).grid(column=1, row=0, sticky="ew")

        ttk.Label(main, text="Port:").grid(column=0, row=1, sticky="w")
        self.port_var = tk.StringVar(value="5000")
        ttk.Entry(main, textvariable=self.port_var, width=10).grid(column=1, row=1, sticky="w")

        ttk.Label(main, text="Windows JSON:").grid(column=0, row=2, sticky="w")
        self.cfg_var = tk.StringVar(value="windows.json")
        ttk.Entry(main, textvariable=self.cfg_var, width=40).grid(column=1, row=2, sticky="ew")
        ttk.Button(main, text="Browse...", command=self.browse_cfg).grid(column=2, row=2, sticky="w")

        self.load_btn = ttk.Button(main, text="Show Windows", command=self.show_windows)
        self.load_btn.grid(column=1, row=3, sticky="w", pady=(6, 0))

        self.start_btn = ttk.Button(main, text="Start Client", command=self.start_client)
        self.start_btn.grid(column=0, row=4, sticky="ew", pady=(10, 0))
        self.stop_btn = ttk.Button(main, text="Stop Client", command=self.stop_client, state="disabled")
        self.stop_btn.grid(column=1, row=4, sticky="ew", pady=(10, 0))

        ttk.Label(main, text="Status:").grid(column=0, row=5, sticky="w", pady=(10, 0))
        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(main, textvariable=self.status_var).grid(column=1, row=5, sticky="w", pady=(10, 0))

        for i in range(3):
            main.columnconfigure(i, weight=1)

    def browse_cfg(self):
        path = filedialog.askopenfilename(title="Select windows.json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            self.cfg_var.set(path)

    def show_windows(self):
        cfg = Path(self.cfg_var.get())
        try:
            if not cfg.exists():
                messagebox.showinfo("Windows", f"{cfg} not found. A default will be created when client runs.")
                return
            data = json.loads(cfg.read_text())
            wins = data.get("windows", [])
            message = f"Found {len(wins)} windows:\n" + "\n".join(f"{i+1}: x={w.get('x')} y={w.get('y')}" for i, w in enumerate(wins))
            messagebox.showinfo("Windows", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read {cfg}:\n{e}")

    def start_client(self):
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Client already running")
            return

        host = self.host_var.get().strip()
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be an integer")
            return
        cfg_path = self.cfg_var.get().strip() or "windows.json"

        # instantiate client
        self.client = WowClient(host=host, port=port, cfg_path=cfg_path)

        # start asyncio client in background thread
        def run_client():
            try:
                asyncio.run(self.client.run())
            except Exception as e:
                logging.exception("Client thread exception: %s", e)
            finally:
                # ensure UI is updated when thread ends
                self.root.after(0, self._on_thread_exit)

        self.thread = threading.Thread(target=run_client, daemon=True)
        self.thread.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Starting...")

        # poll to update status while running
        self.root.after(200, self._update_status)

    def stop_client(self):
        if not self.client:
            return
        self.status_var.set("Stopping...")
        # request shutdown
        try:
            self.client.running = False
        except Exception:
            pass

        # try to join thread briefly
        if self.thread:
            self.thread.join(timeout=2)

        # if still alive, leave it as daemon; update UI
        self._on_thread_exit()

    def _on_thread_exit(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Offline")
        self.client = None
        self.thread = None

    def _update_status(self):
        if self.thread and self.thread.is_alive():
            if self.client:
                try:
                    # Check if client has active connection
                    if hasattr(self.client, '_writer') and self.client._writer:
                        self.status_var.set("Connected")
                    else:
                        self.status_var.set("Connection Failed - Retrying...")
                except Exception:
                    self.status_var.set("Connection Failed - Retrying...")
            else:
                self.status_var.set("Starting...")
            self.root.after(500, self._update_status)
        else:
            # thread died or not started
            if self.client and not self.thread:
                self.status_var.set("Offline")
            elif not self.client:
                self.status_var.set("Offline")

def main():
    root = tk.Tk()
    app = FormClientApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
# ...existing code...