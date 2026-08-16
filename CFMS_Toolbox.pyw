

from __future__ import annotations

import base64
import collections
import hashlib
import io
import json
import os
import re
import secrets
import ssl
import struct
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as simpledialog
from tkinter import filedialog, messagebox as mb

import websocket
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()


APP_VERSION = "1.5.0"
VARIANT_NAME = ""            

SPECIAL = VARIANT_NAME == "遗闻特供版"
APP_TITLE = f"CFMS工具箱 v{APP_VERSION}"
if VARIANT_NAME:
    APP_TITLE += f" {VARIANT_NAME}"


CONFIG_PATH = APP_DIR / (
    "cfms_toolbox_config.json" if SPECIAL else "cfms_toolbox_config_regular.json"
)

DEFAULT_SETTINGS = {
    
    "host": "",
    "port": "",
    "username": "",
    "password": "",
    "output": "",
    "chatbox_path": "",
    "room_names": {},
    "user_names": {},
    "date_labels": {},
    "decoded_ids": {},
    "_legacy_viewer_migrated": 0,
    "html_title": "对话记录",
    "html_subtitle": "内部通讯",
    "auto_refresh": False,
    "interval": "5",
    "proxy_type": "",
    "proxy_host": "",
    "proxy_port": "",
}

def load_config() -> dict:
    
    cfg = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SPECIAL:
        cfg["output"] = str(APP_DIR / "cfms_downloads")
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text("utf-8"))
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in cfg})
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8"
        )
    except OSError:
        pass


ICON_B64 = "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"


_FALLBACK_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _icon_bytes() -> bytes:
    b64 = ICON_B64.strip()
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass
    cand = APP_DIR / "favicon.ico"
    if cand.exists():
        try:
            return cand.read_bytes()
        except Exception:
            pass
    return base64.b64decode(_FALLBACK_ICON_B64)


FRAME_HEADER_LEN = 5
FRAME_PROCESS = 0x00
FRAME_CONCLUSION = 0x01

SEARCH_CHARS = ["."]


def encode_frame(fid: int, kind: int, payload: bytes) -> bytes:
    return struct.pack(">I", fid) + bytes([kind]) + payload


def decode_frame(data: bytes) -> tuple[int, int, bytes]:
    return struct.unpack(">I", data[:4])[0], data[4], data[FRAME_HEADER_LEN:]


class CFMSClient:
    def __init__(self, host: str, port: int,
                 proxy_type: str = "", proxy_host: str = "", proxy_port: int = 0):
        self.host = host
        self.port = port
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.ws: websocket.WebSocket | None = None
        self.username: str | None = None
        self.password: str | None = None
        self.token: str | None = None
        self._next_sid = 1

    def connect(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kw: dict = {
            "url": f"wss://{self.host}:{self.port}",
            "sslopt": {"context": ctx}, "timeout": 15,
        }
        if self.proxy_type and self.proxy_host and self.proxy_port:
            kw["proxy_type"] = self.proxy_type
            kw["http_proxy_host"] = self.proxy_host
            kw["http_proxy_port"] = self.proxy_port
        self.ws = websocket.create_connection(**kw)

    def login(self, username: str, password: str) -> dict:
        r = self._rpc_raw(
            {"action": "login", "data": {"username": username, "password": password}}
        )
        if r.get("code") == 200:
            self.username = username
            self.password = password
            self.token = r["data"]["token"]
        return r

    def _ensure_connection(self):
        if self.ws is None or not self.ws.connected:
            self.connect()
            if self.username and self.password:
                self.login(self.username, self.password)

    def _rpc_raw(self, request: dict) -> dict:
        for attempt in range(2):
            try:
                self._ensure_connection()
                sid = self._next_sid
                self._next_sid += 2
                payload = json.dumps(request, ensure_ascii=False).encode()
                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, payload))
                chunks = []
                while True:
                    raw = self.ws.recv()
                    if isinstance(raw, bytes):
                        fid, kind, p = decode_frame(raw)
                        if fid == sid:
                            chunks.append(p)
                            if kind == FRAME_CONCLUSION:
                                break
                return json.loads(b"".join(chunks))
            except websocket.WebSocketConnectionClosedException:
                if attempt == 0:
                    self._ensure_connection()
                    continue
                else:
                    raise
            except Exception:
                raise
        raise RuntimeError("RPC 调用失败（重试后仍失败）")

    def rpc(self, action: str, data: dict) -> dict:
        return self._rpc_raw(
            {
                "action": action,
                "data": data,
                "username": self.username,
                "token": self.token,
                "timestamp": int(time.time()),
                "nonce": secrets.token_hex(16),
            }
        )

    def list_directory(self, folder_id: str | None) -> list[dict]:
        r = self.rpc("list_directory", {"folder_id": folder_id})
        if r.get("code") != 200:
            raise RuntimeError(r.get("message", str(r)))
        return r["data"].get("items", [])

    def download(self, document_id: str, progress_cb=None) -> bytes:
        for attempt in range(2):
            try:
                self._ensure_connection()
                r = self.rpc("get_document", {"document_id": document_id})
                if r.get("code") != 200:
                    raise RuntimeError(r.get("message", str(r)))
                task_id = r["data"]["task_data"]["task_id"]

                sid = self._next_sid
                self._next_sid += 2
                self.ws.send_binary(
                    encode_frame(
                        sid, FRAME_PROCESS,
                        json.dumps({
                            "action": "download_file",
                            "data": {"task_id": task_id, "offset": 0, "max_chunk_size": 65536},
                        }).encode(),
                    )
                )

                _, _, p = decode_frame(self.ws.recv())
                meta = json.loads(p)
                if meta.get("action") != "transfer_file":
                    raise RuntimeError(f"意外响应: {meta}")
                fs = meta["data"]["file_size"]
                tc = meta["data"]["total_chunks"]

                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"ready"))

                if fs == 0:
                    self.ws.recv()
                    self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"complete"))
                    self.ws.recv()
                    return b""

                chunk_data = []
                total_rcv = 0
                for _ in range(tc):
                    _, _, p = decode_frame(self.ws.recv())
                    cm = json.loads(p)
                    prefix = base64.b64decode(cm["data"]["prefix"] or "")
                    tag = base64.b64decode(cm["data"]["tag"] or "")
                    ct = base64.b64decode(cm["data"]["chunk"])
                    chunk_data.append((cm["data"]["index"], prefix, tag, ct))
                    total_rcv += len(ct)
                    if progress_cb:
                        progress_cb(total_rcv, fs)

                _, _, p = decode_frame(self.ws.recv())
                aes_key = base64.b64decode(json.loads(p)["data"]["key"])

                plaintext = bytearray()
                total_dec = 0
                for idx, prefix, tag, ct in chunk_data:
                    nonce = (prefix[:8] + struct.pack(">I", idx))[:12]
                    aesgcm = AESGCM(aes_key)
                    pt = aesgcm.decrypt(nonce, ct + tag, None)
                    plaintext.extend(pt)
                    total_dec += len(pt)
                    if progress_cb:
                        progress_cb(total_rcv + total_dec, fs + fs)

                self.ws.send_binary(encode_frame(sid, FRAME_PROCESS, b"complete"))
                self.ws.recv()
                return bytes(plaintext)

            except websocket.WebSocketConnectionClosedException:
                if attempt == 0:
                    self._ensure_connection()
                    continue
                else:
                    raise
            except Exception:
                raise
        raise RuntimeError("下载失败（重试后仍失败）")

    def close(self):
        if self.ws:
            self.ws.close()


def sanitize_path(path: str) -> str:
    path = re.sub(r'[<>:"|?*]', "_", path)
    return os.path.join(*(p for p in path.replace("\\", "/").split("/") if p))


def scan_server(client: CFMSClient) -> list[dict]:
    walked = []

    def walk(fid, prefix):
        try:
            items = client.list_directory(fid)
        except RuntimeError:
            return
        dirs = []
        for item in items:
            if item["type"] == "directory":
                dirs.append(item)
            elif item["type"] == "document":
                sp = f"{prefix}/{item['name']}" if prefix else item["name"]
                walked.append(
                    {
                        "path": sp,
                        "id": item["id"],
                        "sha": item.get("sha256", ""),
                        "size": item.get("size"),
                        "hidden": False,
                    }
                )
        for d in dirs:
            sub = f"{prefix}/{d['name']}" if prefix else d["name"]
            walk(d["id"], sub)

    walk(None, "")

    discovered = {}
    for ch in SEARCH_CHARS:
        cursor = None
        while True:
            data = {"query": ch}
            if cursor:
                data["cursor"] = cursor
            r = client.rpc("search", data)
            if r.get("code") != 200:
                break
            for item in r["data"].get("items", []):
                if item["id"] not in discovered:
                    discovered[item["id"]] = item
            if r["data"].get("has_more") and r["data"].get("next_cursor"):
                cursor = r["data"]["next_cursor"]
            else:
                break

    walked_ids = {f["id"] for f in walked}

    path_map = {}
    for item in client.list_directory(None):
        if item["type"] == "directory":
            path_map[item["id"]] = item["name"]
    q = collections.deque((iid, name) for iid, name in list(path_map.items()))
    while q:
        iid, prefix = q.popleft()
        try:
            for item in client.list_directory(iid):
                full = f"{prefix}/{item['name']}"
                if item["id"] not in path_map:
                    path_map[item["id"]] = full
                if item["type"] == "directory":
                    q.append((item["id"], full))
        except RuntimeError:
            pass

    for iid, item in discovered.items():
        if item["type"] == "document" and iid not in walked_ids:
            pid = item.get("parent_id", "")
            pname = path_map.get(pid, "")
            name = item.get("name", item.get("title", "?"))
            sp = f"{pname}/{name}" if pname else f"_hidden/{pid[:8]}_{name}"
            walked.append(
                {
                    "path": sp,
                    "id": iid,
                    "sha": item.get("sha256", ""),
                    "size": item.get("size"),
                    "hidden": True,
                }
            )

    walked.sort(key=lambda f: f["path"])
    return walked


class DownloadPanel:
    

    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()

        out = str(self.cfg.get("output") or "")
        self.output_dir: Path = Path(out) if out else APP_DIR / "cfms_downloads"

        self.client: CFMSClient | None = None
        self.files: list[dict] = []
        self.manifest: dict[str, str] = {}
        self.scanning = False
        self.downloading = False
        self.cancel_download = False
        self._auto_scan = False
        self._refresh_timer_id: str | None = None
        self.all_tree_items = []
        self._proxy_type = ""
        self._proxy_host = ""
        self._proxy_port = ""

        self._build_ui()
        self._load_settings()
        self._load_manifest()
        self._schedule_auto_refresh()

    
    def _build_ui(self):
        row1 = ttk.Frame(self.frame, padding=5)
        row1.pack(fill="x")

        ttk.Label(row1, text="地址：").pack(side="left")
        self.host_var = tk.StringVar()
        self._host_entry = tk.Entry(row1, textvariable=self.host_var, width=17)
        self._host_entry.pack(side="left", padx=2)

        ttk.Label(row1, text="端口：").pack(side="left")
        self.port_var = tk.StringVar()
        self._port_entry = tk.Entry(row1, textvariable=self.port_var, width=6)
        self._port_entry.pack(side="left", padx=2)

        ttk.Label(row1, text="用户名：").pack(side="left")
        self.user_var = tk.StringVar()
        self._user_entry = tk.Entry(row1, textvariable=self.user_var, width=14)
        self._user_entry.pack(side="left", padx=2)

        ttk.Label(row1, text="密码：").pack(side="left")
        self.pass_var = tk.StringVar()
        self._pass_entry = tk.Entry(row1, textvariable=self.pass_var, width=16, show="*")
        self._pass_entry.pack(side="left", padx=2)

        self.connect_btn = ttk.Button(row1, text="连接并扫描", command=self._do_scan)
        self.connect_btn.pack(side="left", padx=(8, 2))
        self.scan_status = ttk.Label(row1, text="")
        self.scan_status.pack(side="left", padx=5)

        row2 = ttk.Frame(self.frame, padding=(5, 0))
        row2.pack(fill="x")

        ttk.Button(row2, text="全选", command=lambda: self._toggle_all(True)).pack(side="left", padx=2)
        ttk.Button(row2, text="取消选择", command=lambda: self._toggle_all(False)).pack(side="left", padx=2)
        ttk.Button(row2, text="全选改动", command=self._select_new).pack(side="left", padx=2)
        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(row2, text="筛选:").pack(side="left", padx=2)
        self.filter_status_var = tk.StringVar(value="全部")
        self.filter_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_status_var,
            values=["全部", "新文件", "已修改", "已下载", "隐藏"],
            state="readonly",
            width=8,
        )
        self.filter_combo.pack(side="left", padx=2)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(row2, text="下载所选文件", command=self._do_download).pack(side="left", padx=2)
        ttk.Button(row2, text="取消", command=self._cancel).pack(side="left", padx=2)

        row3 = ttk.Frame(self.frame, padding=(5, 0))
        row3.pack(fill="x")

        ttk.Label(row3, text="输出：").pack(side="left")
        self.output_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(row3, textvariable=self.output_var, width=30).pack(side="left", padx=2)
        ttk.Button(row3, text="自定义文件夹", command=self._browse_output).pack(side="left")

        ttk.Separator(row3, orient="vertical").pack(side="left", fill="y", padx=6)
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_cb = ttk.Checkbutton(
            row3,
            text="自动刷新",
            variable=self.auto_refresh_var,
            command=self._on_auto_refresh_toggle,
        )
        self.auto_cb.pack(side="left", padx=(2, 2))

        ttk.Label(row3, text="间隔(分):").pack(side="left")
        self.interval_var = tk.StringVar(value="5")
        self.interval_combo = ttk.Combobox(
            row3,
            textvariable=self.interval_var,
            values=["0.5", "1", "5", "10", "30", "60"],
            state="readonly",
            width=4,
        )
        self.interval_combo.pack(side="left", padx=2)

        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("status",)
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings",
            selectmode="extended",
        )
        self.tree.heading("#0", text="文件名", anchor="w")
        self.tree.heading("status", text="状态", anchor="w")
        self.tree.column("#0", width=600, stretch=True)
        self.tree.column("status", width=120, anchor="w", stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_tree_dblclick)
        self.tree.bind("<space>", lambda e: self._toggle_selected())

        bottom_frame = ttk.Frame(self.frame)
        bottom_frame.pack(fill="x", padx=5, pady=(0, 2))

        self.progress = ttk.Progressbar(bottom_frame, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True)

        self.status_bar = ttk.Label(self.frame, text="就绪，请连接并扫描。", anchor="w")
        self.status_bar.pack(fill="x", padx=5, pady=(0, 5))

    
    def _get_val(self, var, key):
        
        v = var.get().strip()
        return v if v else self.cfg.get(key, DEFAULT_SETTINGS.get(key, ""))

    def _load_settings(self):
        for var, key in (
            (self.host_var, "host"),
            (self.port_var, "port"),
            (self.user_var, "username"),
            (self.pass_var, "password"),
        ):
            var.set(self.cfg.get(key) or DEFAULT_SETTINGS.get(key, ""))
        self.output_var.set(str(self.cfg.get("output") or ""))
        self.auto_refresh_var.set(bool(self.cfg.get("auto_refresh", False)))
        self.interval_var.set(str(self.cfg.get("interval", "5")))
        self._proxy_type = self.cfg.get("proxy_type", "")
        self._proxy_host = self.cfg.get("proxy_host", "")
        self._proxy_port = self.cfg.get("proxy_port", "")

    def _save_settings(self):
        out = self.output_var.get().strip()
        if out:
            self.output_dir = Path(out)
        self.cfg.update({
            "host": self._get_val(self.host_var, "host"),
            "port": self._get_val(self.port_var, "port"),
            "username": self._get_val(self.user_var, "username"),
            "password": self._get_val(self.pass_var, "password"),
            "output": str(self.output_dir),
            "auto_refresh": bool(self.auto_refresh_var.get()),
            "interval": self.interval_var.get(),
            "proxy_type": self._proxy_type,
            "proxy_host": self._proxy_host,
            "proxy_port": self._proxy_port,
        })
        
        if not self.cfg.get("chatbox_path"):
            self.cfg["chatbox_path"] = str(self.output_dir / ".runtime" / "chatbox")
        self.toolbox.save_config()

    
    def _on_auto_refresh_toggle(self):
        if self._refresh_timer_id:
            try:
                self.top.after_cancel(self._refresh_timer_id)
            except Exception:
                pass
            self._refresh_timer_id = None
        if self.auto_refresh_var.get():
            self._do_scan(auto=True)
            self._schedule_auto_refresh()

    def _schedule_auto_refresh(self):
        if not self.auto_refresh_var.get():
            return
        if not self.scanning and not self.downloading:
            self._do_scan(auto=True)
        try:
            interval_min = float(self.interval_var.get())
            interval_ms = int(interval_min * 60 * 1000)
        except ValueError:
            interval_ms = 300000
        self._refresh_timer_id = self.top.after(interval_ms, self._schedule_auto_refresh)

    
    def _load_manifest(self):
        mf = self.output_dir / ".cfms_manifest.json"
        if mf.exists():
            try:
                self.manifest = json.loads(mf.read_text("utf-8"))
            except Exception:
                self.manifest = {}
        else:
            self.manifest = {}

    def _file_status(self, f: dict) -> tuple[str, str]:
        sp = f["path"]
        sha = f["sha"]
        if sp in self.manifest:
            if sha and self.manifest[sp] != sha:
                return "已修改", "changed"
            else:
                local_path = self.output_dir / sanitize_path(sp)
                if local_path.exists():
                    return "已下载", "downloaded"
                else:
                    return "已修改", "changed"
        else:
            return "新文件", "new"

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.all_tree_items.clear()
        self._load_manifest()
        for f in self.files:
            status_display, tag = self._file_status(f)
            if f["hidden"]:
                tag = "hidden"
            item_id = self.tree.insert(
                "", "end",
                text=f["path"],
                values=(status_display,),
                tags=(tag,),
            )
            self.all_tree_items.append(item_id)
        self.tree.tag_configure("hidden", foreground="#9370DB")
        self.tree.tag_configure("new", foreground="#0067c0")
        self.tree.tag_configure("changed", foreground="#c42b1c")
        self._apply_filter()

    def _apply_filter(self):
        filter_val = self.filter_status_var.get()
        for item in self.all_tree_items:
            self.tree.reattach(item, "", "end")
        if filter_val == "全部":
            return
        status_map = {
            "新文件": "新文件",
            "已修改": "已修改",
            "已下载": "已下载",
            "隐藏": "hidden",
        }
        target = status_map.get(filter_val)
        if target is None:
            return
        for item in self.all_tree_items:
            tags = self.tree.item(item, "tags")
            if target == "hidden":
                if "hidden" not in tags:
                    self.tree.detach(item)
            else:
                values = self.tree.item(item, "values")
                if not values or values[0] != target:
                    self.tree.detach(item)

    def _toggle_all(self, select: bool):
        for item in self.tree.get_children():
            if select:
                self.tree.selection_add(item)
            else:
                self.tree.selection_remove(item)

    def _select_new(self):
        self.tree.selection_remove(*self.tree.selection())
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if vals and vals[0] in ("新文件", "已修改"):
                self.tree.selection_add(item)

    def _toggle_selected(self):
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def _on_tree_dblclick(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        idx = self.tree.index(item)
        if idx >= len(self.files):
            return
        f = self.files[idx]
        sp = f["path"]

        local_path = self.output_dir / sanitize_path(sp)
        if local_path.exists():
            try:
                text = local_path.read_text("utf-8", errors="replace")
            except Exception:
                mb.showinfo("预览", f"无法预览二进制文件:\n{sp}")
                return
        else:
            if not self.client:
                return
            try:
                self.status_bar.config(text=f"正在下载 {sp} 用于预览...")
                data = self.client.download(f["id"])
                text = data.decode("utf-8", errors="replace")
            except Exception as e:
                mb.showerror("错误", str(e))
                return
            self.status_bar.config(text="就绪。")

        pw = tk.Toplevel(self.top)
        pw.title(f"预览: {sp}")
        pw.geometry("700x500")
        txt = tk.Text(pw, wrap="word", font=("Consolas", 10))
        txt.insert("1.0", text)
        txt.config(state="disabled")
        sb = ttk.Scrollbar(pw, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _browse_output(self):
        d = filedialog.askdirectory(initialdir=str(self.output_dir))
        if d:
            self.output_dir = Path(d).resolve()
            self.output_var.set(str(self.output_dir))
            self._load_manifest()
            if self.files:
                self._populate_tree()

    
    def _do_scan(self, auto=False):
        if self.scanning:
            return
        self.scanning = True
        self._auto_scan = auto

        if not auto:
            self.connect_btn.config(state="disabled")
            self.scan_status.config(text="正在连接...")
            self.status_bar.config(text="正在扫描服务器...")
        else:
            self.scan_status.config(text="自动刷新中...")
            self.status_bar.config(text="自动刷新扫描服务器...")

        def task():
            try:
                host = self._get_val(self.host_var, "host").strip()
                port_str = self._get_val(self.port_var, "port").strip()
                user = self._get_val(self.user_var, "username").strip()
                pwd = self._get_val(self.pass_var, "password")
                if not host or not port_str:
                    raise RuntimeError("请先在顶部填写服务器地址和端口")
                if not user or not pwd:
                    raise RuntimeError("请先填写用户名和密码")
                port = int(port_str)

                c = CFMSClient(host, port,
                               proxy_type=self._proxy_type,
                               proxy_host=self._proxy_host,
                               proxy_port=int(self._proxy_port or "0"))
                c.connect()
                c.rpc("server_info", {})
                c.login(user, pwd)
                self.client = c
                self._save_settings()

                self.top.after(0, lambda: self.scan_status.config(text="正在扫描..."))
                files = scan_server(c)
                self.files = files

                def done():
                    self._populate_tree()
                    self.scan_status.config(text=f"共找到 {len(files)} 个文件")
                    self.status_bar.config(
                        text=f"扫描结束，共找到 {len(files)} 个文件。"
                             "蓝色-新文件，紫色-隐藏文件，红色-已修改文件"
                    )
                    if not auto:
                        self.connect_btn.config(state="normal")
                    self.scanning = False
                    self._notify_new_files()

                self.top.after(0, done)
            except Exception as exc:
                err_msg = str(exc)

                def fail():
                    if auto:
                        self.scan_status.config(text="自动刷新失败")
                        self.status_bar.config(text=f"自动刷新错误：{err_msg}")
                        try:
                            self.toolbox._notify(
                                "自动刷新错误", err_msg)
                        except Exception:
                            pass
                    else:
                        mb.showerror("扫描错误", err_msg)
                        self.scan_status.config(text="失败")
                        self.status_bar.config(text=f"错误：{err_msg}")
                    if not auto:
                        self.connect_btn.config(state="normal")
                    self.scanning = False

                self.top.after(0, fail)

        threading.Thread(target=task, daemon=True).start()

    def _notify_new_files(self):
        new_count = 0
        changed_count = 0
        for f in self.files:
            status, _ = self._file_status(f)
            if status == "新文件":
                new_count += 1
            elif status == "已修改":
                changed_count += 1
        if new_count or changed_count:
            self.scan_status.config(
                text=f"发现 {new_count} 个新文件 / {changed_count} 个已修改"
            )
            try:
                self.toolbox._notify(
                    "扫描发现",
                    f"新增 {new_count} 个文件，{changed_count} 个已修改。")
            except Exception:
                pass

    def _do_download(self):
        if self.downloading:
            return
        sel = self.tree.selection()
        if not sel:
            mb.showinfo("提示", "请先选择要下载的文件")
            return

        indices = [self.tree.index(s) for s in sel]
        if not indices:
            return
        to_dl = [self.files[i] for i in indices if i < len(self.files)]
        if not to_dl:
            return

        out = self.output_var.get().strip()
        if not out:
            mb.showinfo("提示", "请先设置输出文件夹（点击「自定义文件夹」选择保存位置）。")
            return
        self.output_dir = Path(out)
        self._save_settings()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_manifest()

        self.downloading = True
        self.cancel_download = False
        total_files = len(to_dl)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        def task():
            downloaded = 0
            failed = 0
            for i, f in enumerate(to_dl):
                if self.cancel_download:
                    break

                sp = f["path"]
                local_rel = sanitize_path(sp)
                local_path = self.output_dir / local_rel

                self.top.after(0, lambda i=i, sp=sp, total=total_files: (
                    self.status_bar.config(text=f"正在下载 [{i+1}/{total}] {sp} ..."),
                    self.progress.configure(value=i + 1)
                ))

                try:
                    data = self.client.download(f["id"])
                    local_sha = hashlib.sha256(data).hexdigest()
                    if f["sha"] and local_sha != f["sha"]:
                        raise RuntimeError(
                            f"SHA校验不匹配: 服务器={f['sha'][:16]}... 本地={local_sha[:16]}..."
                        )

                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_bytes(data)
                    self.manifest[sp] = local_sha
                    downloaded += 1

                except Exception as e:
                    failed += 1
                    self.top.after(0, lambda sp=sp, e=e: (
                        mb.showwarning("下载出错", f"{sp}\n{str(e)}")
                    ))

            mf = self.output_dir / ".cfms_manifest.json"
            mf.parent.mkdir(parents=True, exist_ok=True)
            mf.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False), "utf-8")

            def done():
                self.downloading = False
                self.progress["value"] = total_files
                self._populate_tree()
                self.status_bar.config(
                    text=f"下载完成：{downloaded} 个文件成功，{failed} 个失败，"
                         f"跳过 {total_files - downloaded - failed} 个"
                )

            self.top.after(0, done)

        threading.Thread(target=task, daemon=True).start()

    def _cancel(self):
        if self.downloading:
            self.cancel_download = True
            self.status_bar.config(text="正在取消...")

    def shutdown(self):
        try:
            if self._refresh_timer_id:
                self.top.after_cancel(self._refresh_timer_id)
                self._refresh_timer_id = None
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass


URL_PAT = re.compile(r"https?://[^\s)]+")

BUBBLE_COLORS = [
    "#ffffff",
    "#b8e4ff",
    "#c8f7c5",
    "#fff5b8",
    "#ffe0ec",
    "#e8d5ff",
    "#ffddc4",
    "#b8f0f0",
]

STRIP_COLORS = [
    "#e0e0e0",
    "#6cc4f5",
    "#5cd65c",
    "#f0d800",
    "#f580a8",
    "#b070f0",
    "#f09050",
    "#40c8c8",
]

REPLY_PAT = re.compile(r"\s*//\s*(\w{7})\s*->\s*(.*)$", re.DOTALL)


def _open_file(path: str) -> None:
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen(["start", "", path], shell=True)


class QuickViewPanel:
    

    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()

        self.chatbox_path: str = ""
        self.rooms: dict[str, dict] = {}
        self.room_names: dict[str, str] = {}
        self.user_names: dict[str, str] = {}
        self._cur_room: str | None = None

        self._room_canvas: tk.Canvas | None = None
        self._room_inner: tk.Frame | None = None
        self._room_cards: dict[str, tk.Frame] = {}
        self._chat_canvas: tk.Canvas | None = None
        self._msg_frame: tk.Frame | None = None
        self._attach_frame: tk.Frame | None = None
        self._canvas_win_id: int = 0
        self._status_lbl: ttk.Label | None = None

        self._load_cfg()
        self._build_ui()
        self._scan()

    
    def _load_cfg(self) -> None:
        self.chatbox_path = str(self.cfg.get("chatbox_path", ""))
        self.room_names = dict(self.cfg.get("room_names", {}))
        self.user_names = dict(self.cfg.get("user_names", {}))

    def _save_cfg(self) -> None:
        self.cfg["chatbox_path"] = self.chatbox_path
        self.cfg["room_names"] = self.room_names
        self.cfg["user_names"] = self.user_names
        self.toolbox.save_config()

    
    def _pick_folder(self) -> None:
        d = filedialog.askdirectory(title="选择 .runtime/chatbox 文件夹")
        if d:
            self.chatbox_path = d
            self._save_cfg()
            self._scan()

    def _show_help(self) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title("帮助")
        dlg.geometry("420x300")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 420, 300)

        tk.Label(dlg, text=f"{APP_TITLE} - 快速查看",
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=(16, 10))
        tk.Label(dlg, text=(
            "读取已下载的 .runtime/chatbox 下的聊天记录，\n"
            "以聊天气泡风格按时间顺序展示各房间的对话。"),
                 font=("Microsoft YaHei", 9), fg="#555", justify="center").pack()

        tk.Label(dlg, text=(
            "工具栏：选择文件夹 / 刷新 / 设置 / 帮助\n"
            "左侧列表：单击选房间，双击改房间名\n"
            "右侧对话：单击用户名可改名，文字可选中复制\n"
            "网址链接：点击气泡内链接可在弹窗中选择打开或复制"),
                 font=("Microsoft YaHei", 9), justify="left",
                 wraplength=370).pack(pady=(12, 0))

        tk.Label(dlg, text="QQ群号：668410643",
                 font=("Microsoft YaHei", 10, "bold"),
                 fg="#2980b9").pack(pady=(12, 6))

        tk.Button(dlg, text="确定", command=dlg.destroy,
                  font=("Microsoft YaHei", 10), padx=20).pack(pady=(4, 12))

    def _show_settings(self) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title("设置")
        dlg.geometry("600x460")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 600, 460)

        nb = ttk.Notebook(dlg)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="文件夹")

        ttk.Label(tab1, text="chatbox 文件夹路径:",
                  font=("Microsoft YaHei", 10)).pack(anchor="w", padx=16, pady=(16, 6))
        path_var = tk.StringVar(value=self.chatbox_path)
        path_entry = ttk.Entry(tab1, textvariable=path_var, width=70)
        path_entry.pack(padx=16, pady=2, fill="x")
        ttk.Button(tab1, text="浏览…", command=lambda: self._browse_settings(path_var)).pack(
            anchor="w", padx=16, pady=(4, 12))

        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="房间名")

        room_frame = tk.Frame(tab2, bg="#f0f0f0")
        room_frame.pack(fill="both", expand=True, padx=8, pady=8)

        room_lb = tk.Listbox(room_frame, font=("Consolas", 9), bg="white",
                              selectbackground="#cce5ff", activestyle="none",
                              borderwidth=1, highlightthickness=0)
        room_scroll = tk.Scrollbar(room_frame, orient="vertical", command=room_lb.yview)
        room_lb.configure(yscrollcommand=room_scroll.set)
        room_lb.pack(side="left", fill="both", expand=True)
        room_scroll.pack(side="right", fill="y")

        room_items: list[tuple[str, str]] = []
        for rid in self.rooms:
            cname = self.room_names.get(rid, "")
            room_items.append((rid, cname))
        room_items.sort(key=lambda x: x[1] or x[0])

        for rid, cname in room_items:
            disp = f"{cname if cname else '(默认)'}   → {rid}"
            room_lb.insert("end", disp)

        ttk.Label(tab2, text="双击列表项可编辑房间名",
                  font=("Microsoft YaHei", 8), foreground="#888").pack(anchor="w", padx=12, pady=(0, 6))

        def room_dblclick(e):
            sel = room_lb.curselection()
            if not sel:
                return
            idx = sel[0]
            rid, _ = room_items[idx]
            old = self.room_names.get(rid, "")
            new = simpledialog.askstring("重命名房间",
                f"房间 {rid[:16]}…\n输入自定义名称(留空恢复默认):",
                initialvalue=old, parent=dlg)
            if new is not None:
                if new.strip():
                    self.room_names[rid] = new.strip()
                else:
                    self.room_names.pop(rid, None)
                self._save_cfg()
                self._render_room_list()
                dlg.destroy()
                self._show_settings()

        room_lb.bind("<Double-Button-1>", room_dblclick)
        room_lb.bind("<MouseWheel>", lambda e: room_lb.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        tab3 = ttk.Frame(nb)
        nb.add(tab3, text="用户名")

        user_frame = tk.Frame(tab3, bg="#f0f0f0")
        user_frame.pack(fill="both", expand=True, padx=8, pady=8)

        user_lb = tk.Listbox(user_frame, font=("Consolas", 9), bg="white",
                              selectbackground="#cce5ff", activestyle="none",
                              borderwidth=1, highlightthickness=0)
        user_scroll = tk.Scrollbar(user_frame, orient="vertical", command=user_lb.yview)
        user_lb.configure(yscrollcommand=user_scroll.set)
        user_lb.pack(side="left", fill="both", expand=True)
        user_scroll.pack(side="right", fill="y")

        all_uids: set[str] = set()
        for rid in self.rooms:
            for m in self.rooms[rid]["msgs"]:
                all_uids.add(m["user"])

        user_items = sorted(all_uids)
        for uid in user_items:
            cname = self.user_names.get(uid, "")
            disp = f"{cname if cname else '(默认)'}   → {uid}"
            user_lb.insert("end", disp)

        ttk.Label(tab3, text="双击列表项可编辑用户名",
                  font=("Microsoft YaHei", 8), foreground="#888").pack(anchor="w", padx=12, pady=(0, 6))

        def user_dblclick(e):
            sel = user_lb.curselection()
            if not sel:
                return
            idx = sel[0]
            uid = user_items[idx]
            old = self.user_names.get(uid, "")
            new = simpledialog.askstring("重命名用户",
                f"用户 {uid[:16]}…\n输入自定义名称(留空恢复默认):",
                initialvalue=old, parent=dlg)
            if new is not None:
                if new.strip():
                    self.user_names[uid] = new.strip()
                else:
                    self.user_names.pop(uid, None)
                self._save_cfg()
                self._render_chat()
                dlg.destroy()
                self._show_settings()

        user_lb.bind("<Double-Button-1>", user_dblclick)
        user_lb.bind("<MouseWheel>", lambda e: user_lb.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        def save_path():
            new_path = path_var.get().strip()
            if new_path and new_path != self.chatbox_path:
                self.chatbox_path = new_path
                self._save_cfg()
                self._scan()
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(fill="x", padx=8, pady=(0, 10))
        ttk.Button(btn_frame, text="确定", command=save_path).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side="right", padx=4)

    def _browse_settings(self, path_var):
        d = filedialog.askdirectory(title="选择 .runtime/chatbox 文件夹")
        if d:
            path_var.set(d)

    
    def _build_ui(self) -> None:
        tbar = ttk.Frame(self.frame, padding=(8, 6))
        tbar.pack(fill="x")

        ttk.Button(tbar, text="选择文件夹", command=self._pick_folder).pack(side="left")
        ttk.Button(tbar, text="刷新", command=self._scan).pack(side="left", padx=(6, 0))
        ttk.Button(tbar, text="设置", command=self._show_settings).pack(side="left", padx=(6, 0))
        ttk.Button(tbar, text="帮助", command=self._show_help).pack(side="left", padx=(6, 0))

        self._path_lbl = ttk.Label(tbar, text="", foreground="#888")
        self._path_lbl.pack(side="left", padx=(12, 0))

        pw = ttk.PanedWindow(self.frame, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=(8, 8), pady=(2, 4))

        left_frame = ttk.Frame(pw, width=340)
        pw.add(left_frame, weight=0)

        ttk.Label(left_frame, text="聊天室", font=("Microsoft YaHei", 10, "bold"),
                  padding=(4, 4)).pack(fill="x")

        list_frame = tk.Frame(left_frame, bg="#e8e8e8")
        list_frame.pack(fill="both", expand=True)

        self._room_canvas = tk.Canvas(list_frame, bg="#f5f5f5",
                                       highlightthickness=0, bd=0)
        room_scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                                       command=self._room_canvas.yview)
        self._room_canvas.configure(yscrollcommand=room_scrollbar.set)

        self._room_inner = tk.Frame(self._room_canvas, bg="#f5f5f5")
        self._room_win_id = self._room_canvas.create_window(
            (0, 0), window=self._room_inner, anchor="nw")

        self._room_inner.bind("<Configure>",
            lambda e: self._room_canvas.configure(
                scrollregion=self._room_canvas.bbox("all")))

        self._room_canvas.bind("<Configure>",
            lambda e: self._room_canvas.itemconfig(self._room_win_id, width=e.width))

        self._room_canvas.grid(row=0, column=0, sticky="nsew")
        room_scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self._room_canvas.bind("<MouseWheel>", self._on_room_wheel)
        self._room_canvas.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
        self._room_canvas.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))

        right_frame = ttk.Frame(pw)
        pw.add(right_frame, weight=1)

        self._chat_canvas = tk.Canvas(right_frame, bg="#f0f0f0",
                                       highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(right_frame, orient="vertical",
                            command=self._chat_canvas.yview)
        self._chat_canvas.configure(yscrollcommand=vsb.set)

        self._msg_frame = tk.Frame(self._chat_canvas, bg="#f0f0f0")
        self._canvas_win_id = self._chat_canvas.create_window(
            (0, 0), window=self._msg_frame, anchor="nw")

        self._msg_frame.bind("<Configure>",
            lambda e: self._chat_canvas.configure(
                scrollregion=self._chat_canvas.bbox("all")))
        self._chat_canvas.bind("<Configure>", self._on_canvas_resize)
        for w in (self._chat_canvas, self._msg_frame, right_frame):
            w.bind("<MouseWheel>", self._on_mousewheel)
            w.bind("<Button-4>", self._on_mousewheel_up)
            w.bind("<Button-5>", self._on_mousewheel_down)

        self._chat_canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self._attach_frame = tk.Frame(right_frame, bg="#e0e0e0", height=36)
        self._attach_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._attach_frame.grid_propagate(False)

        self._status_lbl = ttk.Label(self.frame, text="就绪", anchor="w",
                                      padding=(8, 2))
        self._status_lbl.pack(fill="x")

    
    def _on_canvas_resize(self, event: tk.Event) -> None:
        self._chat_canvas.itemconfig(self._canvas_win_id, width=event.width)

    def _on_mousewheel(self, event):
        self._chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_up(self, event):
        self._chat_canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, event):
        self._chat_canvas.yview_scroll(1, "units")

    def _on_room_wheel(self, event: tk.Event) -> None:
        self._room_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_scroll_recursive(self, parent):
        for child in parent.winfo_children():
            child.bind("<MouseWheel>", self._on_mousewheel)
            child.bind("<Button-4>", self._on_mousewheel_up)
            child.bind("<Button-5>", self._on_mousewheel_down)
            if child.winfo_children():
                self._bind_scroll_recursive(child)

    def _bind_room_scroll(self):
        self._room_inner.bind("<MouseWheel>", self._on_room_wheel)
        self._room_inner.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
        self._room_inner.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))
        for child in self._room_inner.winfo_children():
            child.bind("<MouseWheel>", self._on_room_wheel)
            child.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
            child.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))
            for sub in child.winfo_children():
                sub.bind("<MouseWheel>", self._on_room_wheel)
                sub.bind("<Button-4>", lambda e: self._room_canvas.yview_scroll(-1, "units"))
                sub.bind("<Button-5>", lambda e: self._room_canvas.yview_scroll(1, "units"))

    
    def _scan(self) -> None:
        if not self.chatbox_path:
            if self.cfg.get("chatbox_path"):
                self._load_cfg()
        if not self.chatbox_path or not os.path.isdir(self.chatbox_path):
            self._path_lbl.config(text="请选择 chatbox 文件夹")
            self._status_lbl.config(text="未选择文件夹")
            return

        self._path_lbl.config(text=self.chatbox_path)
        self.rooms.clear()
        root = Path(self.chatbox_path)

        raw_rooms: list[tuple[str, Path, list[dict], list[Path]]] = []
        for d in root.iterdir():
            if not d.is_dir():
                continue
            if d.name == "00000000-0000-0000-000000000000":
                continue
            room_id = d.name
            msgs, atts = self._parse_room(d)
            raw_rooms.append((room_id, d, msgs, atts))

        raw_rooms.sort(
            key=lambda r: r[2][-1]["time"] if r[2] else "0000-00-00 00:00:00",
            reverse=True,
        )

        for room_id, d, msgs, atts in raw_rooms:
            name = self.room_names.get(room_id, room_id[:8] + "…")
            self.rooms[room_id] = {
                "name": name, "path": d, "msgs": msgs,
                "attachments": atts, "full_id": room_id,
            }

        self._render_room_list()
        self._status_lbl.config(text=f"共 {len(self.rooms)} 个聊天室")
        if self.rooms:
            if self._cur_room not in self.rooms:
                self._cur_room = next(iter(self.rooms))
            self._select_room(self._cur_room)

    def _parse_room(self, room_dir: Path) -> tuple[list[dict], list[Path]]:
        msgs: list[dict] = []
        attachments: list[Path] = []

        for f in sorted(room_dir.iterdir()):
            if f.name.startswith("."):
                continue
            if f.suffix.lower() == ".txt":
                user_id = f.stem
                try:
                    lines = f.read_text("utf-8", errors="replace").splitlines()
                except Exception:
                    continue
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if " | " in line:
                        ts, content = line.split(" | ", 1)
                        reply_ref: tuple[str, str] | None = None
                        m = REPLY_PAT.search(content)
                        if m:
                            reply_ref = (m.group(1), m.group(2).strip())
                            content = content[:m.start()]
                        msgs.append({
                            "user": user_id,
                            "time": ts,
                            "content": content,
                            "reply_ref": reply_ref,
                        })
            else:
                attachments.append(f)

        msgs.sort(key=lambda m: m["time"])
        return msgs, attachments

    def _render_room_list(self) -> None:
        for w in self._room_inner.winfo_children():
            w.destroy()
        self._room_cards.clear()

        for rid in self.rooms:
            room = self.rooms[rid]
            name = self.room_names.get(rid, rid[:16] + "…")
            cnt = len(room["msgs"])
            last_ts = ""
            if room["msgs"]:
                last_ts = room["msgs"][-1]["time"]

            card = tk.Frame(self._room_inner, bg="#ffffff", bd=0,
                            highlightthickness=1, highlightbackground="#e0e0e0",
                            cursor="hand2")
            card.pack(fill="x", padx=4, pady=(2, 2))

            name_lbl = tk.Label(card, text=name,
                                font=("Microsoft YaHei", 12, "bold"),
                                fg="#191919", bg="#ffffff", anchor="w",
                                justify="left", cursor="hand2")
            name_lbl.pack(fill="x", padx=(10, 10), pady=(8, 0))

            info_text = f"{cnt} 条信息"
            if last_ts:
                info_text += f"  ·  最后: {last_ts}"
            info_lbl = tk.Label(card, text=info_text,
                                font=("Microsoft YaHei", 8),
                                fg="#888", bg="#ffffff", anchor="w",
                                justify="left", cursor="hand2")
            info_lbl.pack(fill="x", padx=(10, 10), pady=(2, 8))

            self._room_cards[rid] = card

            for w in (card, name_lbl, info_lbl):
                w.bind("<Button-1>", lambda e, r=rid: self._select_room(r))
                w.bind("<Double-Button-1>", lambda e, r=rid: self._rename_room(r))

        self._bind_room_scroll()

    def _select_room(self, rid: str) -> None:
        for r, card in self._room_cards.items():
            if r == rid:
                card.configure(bg="#cce5ff", highlightbackground="#a0d0f0")
                for child in card.winfo_children():
                    child.configure(bg="#cce5ff")
            else:
                card.configure(bg="#ffffff", highlightbackground="#e0e0e0")
                for child in card.winfo_children():
                    child.configure(bg="#ffffff")
        self._cur_room = rid
        self._render_chat()

    def _rename_room(self, rid: str = "") -> None:
        if not rid:
            return
        old = self.room_names.get(rid, "")
        new = simpledialog.askstring(
            "重命名房间", "输入自定义房间名:",
            initialvalue=old, parent=self.top)
        if new and new.strip():
            self.room_names[rid] = new.strip()
        elif new is not None and not new.strip() and old:
            self.room_names.pop(rid, None)
        else:
            return
        self._save_cfg()
        self._render_room_list()
        self._select_room(rid)

    def _render_chat(self) -> None:
        for w in self._msg_frame.winfo_children():
            w.destroy()
        for w in self._attach_frame.winfo_children():
            w.destroy()

        if not self._cur_room or self._cur_room not in self.rooms:
            return

        room = self.rooms[self._cur_room]
        msgs = room["msgs"]
        atts = room["attachments"]

        if not msgs:
            tk.Label(self._msg_frame, text="暂无消息", bg="#f0f0f0",
                     fg="#999", font=("Microsoft YaHei", 12)).pack(pady=60)
        else:
            user_order: list[str] = []
            seen: set[str] = set()
            for m in msgs:
                u = m["user"]
                if u not in seen:
                    seen.add(u)
                    user_order.append(u)
            user_color: dict[str, tuple[str, str]] = {}
            for i, u in enumerate(user_order):
                user_color[u] = (
                    BUBBLE_COLORS[i % len(BUBBLE_COLORS)],
                    STRIP_COLORS[i % len(STRIP_COLORS)],
                )

            for m in msgs:
                u = m["user"]
                bg, strip = user_color[u]
                disp_name = self.user_names.get(u, u[:8] + "…")
                ts = m["time"]
                reply_ref = m.get("reply_ref")

                outer = tk.Frame(self._msg_frame, bg="#f0f0f0")
                outer.pack(fill="x", padx=12, pady=(4, 0))

                header = tk.Frame(outer, bg="#f0f0f0")
                header.pack(fill="x")

                name_lbl = tk.Label(
                    header, text=disp_name,
                    font=("Microsoft YaHei", 9, "bold"),
                    fg="#333", bg="#f0f0f0", cursor="hand2",
                )
                name_lbl.pack(side="left")
                name_lbl.bind("<Button-1>", lambda e, uid=u: self._rename_user(uid))

                time_lbl = tk.Label(
                    header, text=ts,
                    font=("Microsoft YaHei", 7), fg="#aaa", bg="#f0f0f0",
                )
                time_lbl.pack(side="left", padx=(6, 0))

                bubble = tk.Frame(
                    outer, bg=bg,
                    highlightbackground=strip,
                    highlightcolor=strip,
                    highlightthickness=2,
                    bd=0,
                )
                bubble.pack(anchor="w", padx=(0, 80), pady=(2, 0), fill="x")

                if reply_ref:
                    ref_uid, ref_text = reply_ref
                    ref_name = self.user_names.get(ref_uid, ref_uid[:7])
                    reply_frame = tk.Frame(bubble, bg=bg)
                    reply_frame.pack(fill="x", padx=10, pady=(6, 2))

                    tk.Label(
                        reply_frame, text="↩ ",
                        font=("Microsoft YaHei", 8),
                        fg="#6cc4f5", bg=bg,
                    ).pack(side="left")
                    tk.Label(
                        reply_frame, text=ref_name,
                        font=("Microsoft YaHei", 8, "bold"),
                        fg="#409eff", bg=bg,
                    ).pack(side="left")
                    tk.Label(
                        reply_frame, text=f"：{ref_text[:60]}{'…' if len(ref_text) > 60 else ''}",
                        font=("Microsoft YaHei", 8),
                        fg="#888", bg=bg,
                    ).pack(side="left")

                    sep = tk.Frame(bubble, bg="#e0e0e0", height=1)
                    sep.pack(fill="x", padx=10, pady=(3, 0))

                txt_content = m["content"]
                
                est = 0
                for line in (txt_content or "").split("\n"):
                    w = sum(13 if ord(c) > 127 else 7 for c in line)
                    est += max(1, -(-w // 550))
                dlines = max(1, est)
                txt = tk.Text(
                    bubble, font=("Microsoft YaHei", 10),
                    fg="#191919", bg=bg,
                    bd=0, highlightthickness=0,
                    wrap="char", relief="flat",
                    height=dlines,
                    cursor="xterm", state="normal",
                )
                txt.pack(fill="x", anchor="w",
                         padx=10, pady=(2 if reply_ref else 6, 8))
                txt.insert("1.0", txt_content)

                txt.tag_configure("url", foreground="#2980b9", underline=True)

                def _url_enter(e, widget=txt):
                    widget.configure(cursor="hand2")

                def _url_leave(e, widget=txt):
                    widget.configure(cursor="xterm")

                txt.tag_bind("url", "<Enter>", _url_enter)
                txt.tag_bind("url", "<Leave>", _url_leave)

                for match in URL_PAT.finditer(txt_content):
                    url = match.group()
                    s = f"1.0 + {match.start()} chars"
                    e = f"1.0 + {match.end()} chars"
                    txt.tag_add("url", s, e)
                    txt.tag_bind("url", "<Button-1>",
                                 self._make_url_handler(url))

                txt.configure(state="disabled")

        if atts:
            tk.Label(self._attach_frame, text="附件:",
                     font=("Microsoft YaHei", 8, "bold"),
                     fg="#666", bg="#e0e0e0").pack(side="left", padx=(10, 6))
            for i, fp in enumerate(atts, 1):
                btn = tk.Button(
                    self._attach_frame, text=f"附件{i}: {fp.name}",
                    font=("Microsoft YaHei", 8),
                    bg="#f5f5f5", fg="#333", relief="groove", bd=1,
                    cursor="hand2",
                    command=lambda p=str(fp): _open_file(p),
                )
                btn.pack(side="left", padx=4, pady=4)
        else:
            tk.Label(self._attach_frame, text="无附件",
                     font=("Microsoft YaHei", 8),
                     fg="#bbb", bg="#e0e0e0").pack(side="left", padx=10)

        self._chat_canvas.yview_moveto(0.0)
        self._bind_scroll_recursive(self._msg_frame)

    
    def _make_url_handler(self, url: str):
        return lambda e: self._handle_url(url)

    def _handle_url(self, url: str) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title("链接")
        dlg.geometry("420x140")
        dlg.resizable(False, False)
        dlg.transient(self.top)
        dlg.grab_set()
        self._center_window(dlg, 420, 140)

        tk.Label(dlg, text=url[:80], font=("Microsoft YaHei", 9),
                 fg="#2980b9", wraplength=380).pack(pady=(16, 12))

        btn_frame = tk.Frame(dlg)
        btn_frame.pack()

        def do_open():
            dlg.destroy()
            try:
                os.startfile(url)
            except Exception:
                subprocess.Popen(["start", "", url], shell=True)

        def do_copy():
            self.top.clipboard_clear()
            self.top.clipboard_append(url)
            dlg.destroy()

        tk.Button(btn_frame, text="打开链接", command=do_open,
                  font=("Microsoft YaHei", 10), padx=16).pack(side="left", padx=6)
        tk.Button(btn_frame, text="复制链接", command=do_copy,
                  font=("Microsoft YaHei", 10), padx=16).pack(side="left", padx=6)

    def _center_window(self, win, w, h):
        win.update_idletasks()
        pw = self.top.winfo_width()
        ph = self.top.winfo_height()
        rx = self.top.winfo_rootx()
        ry = self.top.winfo_rooty()
        x = rx + (pw - w) // 2
        y = ry + (ph - h) // 2
        win.geometry(f"+{x}+{y}")

    def _rename_user(self, uid: str) -> None:
        old = self.user_names.get(uid, "")
        new = simpledialog.askstring(
            "重命名用户", f"为 {uid[:10]}… 输入自定义名称:",
            initialvalue=old, parent=self.top)
        if new and new.strip():
            self.user_names[uid] = new.strip()
        elif new is not None and not new.strip() and old:
            self.user_names.pop(uid, None)
        else:
            return
        self._save_cfg()
        self._render_chat()


CHATBOX_DIR = APP_DIR / "downloads" / ".runtime" / "chatbox"
HTML_TITLE = "对话记录"
HTML_SUBTITLE = "内部通讯"
USER_NAME_MAP: dict[str, dict] = {}
ROOM_NAME_MAP: dict[str, str] = {}
DATE_GROUP_NAMES: dict[str, str] = {}
DECODED_IDS: dict[str, str] = {}

def get_user_name(user_id: str) -> str:
    
    return USER_NAME_MAP.get(user_id, {}).get("name", user_id[:6])

def get_room_name(room_id: str) -> str:
    
    return ROOM_NAME_MAP.get(room_id, room_id[:8] + "...")

def get_date_label(date_str: str) -> str:
    
    return DATE_GROUP_NAMES.get(date_str, "")

def get_user_info(file_hash: str) -> dict:
    
    if file_hash in USER_NAME_MAP:
        return USER_NAME_MAP[file_hash]
    
    colors = ["#576b95", "#07c160", "#e6a23c", "#409eff", "#f56c6c", "#909399"]
    avatars = ["👤", "👥", "🗣️", "💭", "📝", "🫥"]
    idx = hash(file_hash) % len(colors)
    new_user = {
        "name": f"用户{file_hash[:6]}",
        "avatar": avatars[idx],
        "color": colors[idx],
    }
    USER_NAME_MAP[file_hash] = new_user
    print(f"🆕 新用户已添加: {file_hash} → {new_user['name']}")
    return new_user

def parse_chat_file(filepath: Path) -> list[dict]:
    
    messages = []
    file_hash = filepath.stem  
    user_info = get_user_info(file_hash)

    
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(.*)", line)
        if match:
            time_str = match.group(1)
            content = match.group(2)

            
            comment_match = re.match(r"^(.*?)\s*//\s*(.*)$", content)
            if comment_match and not content.startswith("http"):
                content = comment_match.group(1).strip()
                
                ref = comment_match.group(2).strip()
                if ref:
                    ref_match = re.match(r"^([0-9a-fA-F]+)\s*->\s*(.*)$", ref)
                    if ref_match:
                        ref_user_id = ref_match.group(1)
                        ref_msg = ref_match.group(2)
                        ref_user_name = get_user_name(ref_user_id)
                        ref_display = f"{ref_user_name} → {ref_msg}"
                    else:
                        ref_display = ref
                    content += f' <span class="msg-ref">↩ {ref_display}</span>'

            messages.append({
                "user_id": file_hash,
                "user_name": user_info["name"],
                "user_avatar": user_info["avatar"],
                "user_color": user_info["color"],
                "time": time_str,
                "timestamp": datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S"),
                "content": content,
            })

    return messages

def load_all_chats() -> dict[str, list[dict]]:
    
    rooms = collections.defaultdict(list)

    if not CHATBOX_DIR.exists():
        print(f"❌ 目录不存在: {CHATBOX_DIR}")
        return rooms

    for room_dir in sorted(CHATBOX_DIR.iterdir()):
        if not room_dir.is_dir():
            continue

        room_id = room_dir.name
        
        if room_id.startswith("00000000-0000-0000"):
            print(f"⏭️ 忽略占位房间: {room_id}")
            continue
        for file in sorted(room_dir.glob("*.txt")):
            messages = parse_chat_file(file)
            rooms[room_id].extend(messages)

    
    for room_id in rooms:
        rooms[room_id].sort(key=lambda m: m["timestamp"])

    return rooms

def generate_html(rooms: dict[str, list[dict]]) -> str:
    
    
    room_list = []
    for room_id, msgs in rooms.items():
        if not msgs:
            continue
        room_list.append({
            "id": room_id,
            "name": get_room_name(room_id),
            "first_time": msgs[0]["timestamp"],
            "last_time": msgs[-1]["timestamp"],
            "message_count": len(msgs),
            "users": list(set(m["user_name"] for m in msgs)),
        })
    room_list.sort(key=lambda r: r["first_time"])

    
    rooms_json = json.dumps(room_list, ensure_ascii=False, default=str)
    chats_json_data = {}
    for room_id, msgs in rooms.items():
        chats_json_data[room_id] = [
            {k: str(v) if isinstance(v, datetime) else v for k, v in m.items()}
            for m in msgs
        ]
    chats_json = json.dumps(chats_json_data, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{HTML_TITLE}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
    background: #ededed;
    display: flex;
    height: 100vh;
    overflow: hidden;
}}


.sidebar {{
    width: 280px;
    min-width: 280px;
    background: #e6e6e6;
    border-right: 1px solid #d9d9d9;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}}
.sidebar-header {{
    padding: 20px 16px 12px;
    background: #e6e6e6;
    border-bottom: 1px solid #d9d9d9;
}}
.sidebar-header h1 {{
    font-size: 18px;
    font-weight: 600;
    color: #191919;
    margin-bottom: 4px;
}}
.sidebar-header .subtitle {{
    font-size: 12px;
    color: #888;
}}
.room-list {{
    flex: 1;
    overflow-y: auto;
}}
.room-item {{
    display: flex;
    align-items: center;
    padding: 14px 16px;
    cursor: pointer;
    transition: background 0.15s;
    border-bottom: 1px solid #dfdfdf;
}}
.room-item:hover {{ background: #dadada; }}
.room-item.active {{ background: #c9c9c9; }}
.room-avatar {{
    width: 44px;
    height: 44px;
    border-radius: 6px;
    background: #07c160;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin-right: 12px;
    flex-shrink: 0;
}}
.room-info {{ flex: 1; min-width: 0; }}
.room-name {{
    font-size: 15px;
    color: #191919;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.room-meta {{
    font-size: 12px;
    color: #999;
}}
.room-badge {{
    font-size: 11px;
    background: #f3514f;
    color: #fff;
    border-radius: 10px;
    padding: 2px 7px;
    min-width: 20px;
    text-align: center;
}}


.chat-area {{
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #f5f5f5;
    min-width: 0;
}}
.chat-header {{
    padding: 14px 20px;
    background: #ededed;
    border-bottom: 1px solid #d9d9d9;
    display: flex;
    align-items: center;
}}
.chat-header .title {{
    font-size: 17px;
    font-weight: 500;
    color: #191919;
}}
.chat-header .sub-info {{
    font-size: 12px;
    color: #999;
    margin-top: 2px;
}}
.chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
}}
.chat-messages::-webkit-scrollbar {{ width: 6px; }}
.chat-messages::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 3px; }}


.time-divider {{
    text-align: center;
    margin: 16px 0;
}}
.time-divider span {{
    font-size: 12px;
    color: #b0b0b0;
    background: #f5f5f5;
    padding: 4px 12px;
    border-radius: 2px;
}}
.time-divider .date-label {{
    display: block;
    font-size: 11px;
    color: #999;
    margin-top: 2px;
}}


.msg-row {{
    display: flex;
    margin-bottom: 16px;
    align-items: flex-start;
}}
.msg-row.self {{
    flex-direction: row-reverse;
}}
.msg-avatar {{
    width: 38px;
    height: 38px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    background: #e0e0e0;
}}
.msg-row.self .msg-avatar {{ margin-left: 10px; }}
.msg-row:not(.self) .msg-avatar {{ margin-right: 10px; }}

.msg-avatar {{
    cursor: pointer;
    transition: transform 0.15s;
    user-select: none;
}}
.msg-avatar:hover {{ transform: scale(1.15); }}
.msg-avatar.avatar-edited::before {{
    content: "";
    position: absolute;
    top: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    background: #07c160;
    border-radius: 50%;
    border: 1px solid #fff;
}}
.msg-bubble-wrap {{ max-width: 65%; }}
.msg-sender {{
    font-size: 12px;
    color: #999;
    margin-bottom: 4px;
    padding: 0 8px;
}}
.msg-row.self .msg-sender {{ text-align: right; }}
.msg-bubble {{
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 15px;
    line-height: 1.5;
    word-break: break-word;
    position: relative;
    color: #191919;
}}
.msg-row:not(.self) .msg-bubble {{
    background: #fff;
    border-top-left-radius: 2px;
}}
.msg-row.self .msg-bubble {{
    background: #95ec69;
    border-top-right-radius: 2px;
}}
.msg-time {{
    font-size: 11px;
    color: #b0b0b0;
    margin-top: 4px;
    padding: 0 8px;
}}
.msg-row.self .msg-time {{ text-align: right; }}
.msg-ref {{
    display: block;
    font-size: 11px;
    color: #888;
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px solid rgba(0,0,0,0.08);
    font-style: italic;
}}


.id-tooltip {{
    position: fixed;
    z-index: 999;
    background: rgba(0, 0, 0, 0.82);
    color: #fff;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-family: Consolas, "Courier New", monospace;
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
}}


.msg-sender {{
    cursor: pointer;
    padding: 2px 6px;
    margin: -2px -6px;
    border-radius: 4px;
    transition: background 0.2s;
    position: relative;
}}
.msg-sender:hover {{ background: rgba(0,0,0,0.06); }}
.msg-sender::after {{
    content: "✎";
    font-size: 10px;
    margin-left: 4px;
    opacity: 0;
    transition: opacity 0.2s;
}}
.msg-sender:hover::after {{ opacity: 0.4; }}
.msg-sender.edited {{ border-bottom: 2px dashed #07c160; }}
.msg-sender.edited::after {{ opacity: 0.7; content: "✓"; }}

.edit-mode .msg-sender {{
    cursor: text;
    background: rgba(7,193,96,0.06);
    border: 1px dashed #ccc;
    border-radius: 4px;
    padding: 2px 6px;
    margin: -2px -6px;
}}
.edit-mode .msg-sender:hover {{ background: rgba(7,193,96,0.12); }}
.edit-mode .msg-sender::after {{ opacity: 0; }}
.edit-mode .msg-avatar::after {{
    content: "✎";
    position: absolute;
    bottom: -2px;
    right: -2px;
    font-size: 10px;
    background: #07c160;
    color: #fff;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #fff;
}}
.msg-sender input {{
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    border: none;
    outline: none;
    background: transparent;
    width: 100%;
    padding: 0;
}}

.empty-state {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #ccc;
}}
.empty-state .icon {{ font-size: 64px; margin-bottom: 16px; }}
.empty-state .text {{ font-size: 16px; }}


.back-btn {{
    display: none;
    width: 32px;
    height: 32px;
    margin-right: 10px;
    font-size: 18px;
    line-height: 32px;
    text-align: center;
    cursor: pointer;
    color: #576b95;
    flex-shrink: 0;
    border-radius: 50%;
    -webkit-tap-highlight-color: transparent;
}}


@media (max-width: 768px) {{
    body {{ flex-direction: column; }}
    .sidebar {{
        width: 100%;
        min-width: 0;
        height: 100vh;
        height: 100dvh;
    }}
    .sidebar.mobile-hidden {{ display: none; }}
    .sidebar-header {{
        padding: calc(12px + env(safe-area-inset-top)) 16px 12px;
    }}
    .room-item {{
        padding: 12px 14px;
        -webkit-tap-highlight-color: transparent;
    }}
    .room-avatar {{
        width: 40px;
        height: 40px;
        font-size: 18px;
    }}
    .room-name {{ font-size: 14px; }}
    .room-badge {{
        font-size: 10px;
        padding: 2px 6px;
    }}

    .chat-area {{
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 10;
    }}
    .chat-area.mobile-active {{ display: flex; }}

    .chat-header {{
        padding: calc(10px + env(safe-area-inset-top)) 14px 10px;
    }}
    .chat-header .title {{ font-size: 16px; }}
    .back-btn {{ display: block; }}

    .chat-messages {{
        padding: 12px 12px calc(12px + env(safe-area-inset-bottom));
    }}

    .msg-bubble-wrap {{ max-width: 85%; }}
    .msg-bubble {{
        padding: 10px 12px;
        font-size: 15px;
    }}
    .msg-avatar {{
        width: 34px;
        height: 34px;
        font-size: 16px;
    }}
    .msg-row.self .msg-avatar {{ margin-left: 8px; }}
    .msg-row:not(.self) .msg-avatar {{ margin-right: 8px; }}

    .msg-sender {{ font-size: 11px; }}
    .msg-time {{ font-size: 10px; }}
    .msg-ref {{ font-size: 10px; }}

    .time-divider span {{
        font-size: 11px;
        padding: 3px 10px;
    }}
    .time-divider .date-label {{ font-size: 10px; }}
}}
</style>
</head>
<body>


<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <h1>💬 对话记录</h1>
        <div class="subtitle">{HTML_SUBTITLE}</div>
    </div>
    <div class="room-list" id="roomList"></div>
</div>


<div class="chat-area" id="chatArea">
    <div class="empty-state" id="emptyState">
        <div class="icon">💬</div>
        <div class="text">选择一个会话查看</div>
    </div>
    <div class="chat-header" id="chatHeader" style="display:none;">
        <div class="back-btn" id="backBtn" onclick="goBack()">←</div>
        <div>
            <div class="title" id="chatTitle"></div>
            <div class="sub-info" id="chatSubInfo"></div>
        </div>
    </div>
    <div class="chat-messages" id="chatMessages" style="display:none;"></div>
</div>


<div class="id-tooltip" id="idTooltip" style="display:none;"></div>

<script>
var ROOMS = {rooms_json};
var CHATS = {chats_json};
var DECODED_IDS = {json.dumps(DECODED_IDS, ensure_ascii=False)};
var USERS = {json.dumps(USER_NAME_MAP, ensure_ascii=False)};

var NAME_EDITS = {{}};
try {{
    NAME_EDITS = JSON.parse(localStorage.getItem('chatUserNames') || '{{}}');
}} catch(e) {{ NAME_EDITS = {{}}; }}
var AVATAR_EDITS = {{}};
try {{
    AVATAR_EDITS = JSON.parse(localStorage.getItem('chatUserAvatars') || '{{}}');
}} catch(e) {{ AVATAR_EDITS = {{}}; }}
var editMode = false;

function toggleEditMode() {{
    editMode = !editMode;
    var btn = document.getElementById('editModeBtn');
    var area = document.getElementById('chatArea');
    if (editMode) {{
        area.classList.add('edit-mode');
        btn.classList.add('export');
        btn.textContent = '✏️ 编辑中...';
        applyEditModeInputs();
    }} else {{
        area.classList.remove('edit-mode');
        btn.classList.remove('export');
        btn.textContent = '✏️ 编辑模式';
        applyNameEdits();
        applyAvatarEdits();
    }}
}}

function applyEditModeInputs() {{
    var all = document.querySelectorAll('.msg-sender');
    all.forEach(function(el) {{
        if (el.querySelector('input')) return;
        var uid = el.getAttribute('data-user-id');
        var orig = el.getAttribute('data-orig-name');
        if (!uid) return;
        var current = NAME_EDITS[uid] || orig;
        var input = document.createElement('input');
        input.type = 'text';
        input.value = current;
        function commit() {{
            var v = input.value.trim();
            if (v && v !== orig) {{
                NAME_EDITS[uid] = v;
            }} else {{
                delete NAME_EDITS[uid];
            }}
            localStorage.setItem('chatUserNames', JSON.stringify(NAME_EDITS));
        }}
        input.addEventListener('change', commit);
        input.addEventListener('blur', commit);
        input.addEventListener('keydown', function(ev) {{
            if (ev.key === 'Enter') {{ input.blur(); }}
            if (ev.key === 'Escape') {{
                input.value = orig;
                delete NAME_EDITS[uid];
                localStorage.setItem('chatUserNames', JSON.stringify(NAME_EDITS));
                input.blur();
            }}
        }});
        el.innerHTML = '';
        el.appendChild(input);
    }});
}}
var AVATAR_OPTIONS = ['🧑‍💻','🤔','👀','🔍','💬','🎭','😄','📡','🎧','🧩','📊','🔧','🤷‍♂️','🤫','💭','👤','👥','🗣️','📝','🫥','🤖','👻','💀','🎃','🤡','👺','🐱','🐶','🦊','🐼','⭐','🔥','💎','🎵','🎮','🌈','🍀','⚡','🌙','☀️'];

var currentRoom = null;
var currentUserId = null;
var isMobile = window.innerWidth <= 768;

function applyAvatarEdits(container) {{
    var all = (container || document).querySelectorAll('.msg-avatar');
    all.forEach(function(av) {{
        var uid = av.getAttribute('data-user-id');
        if (!uid) return;
        if (AVATAR_EDITS[uid]) {{
            av.textContent = AVATAR_EDITS[uid];
            av.classList.add('avatar-edited');
        }} else {{
            av.classList.remove('avatar-edited');
        }}
    }});
}}

function editAvatar(av, uid) {{
    var input = document.createElement('input');
    input.type = 'text';
    input.value = AVATAR_EDITS[uid] || av.textContent.trim();
    input.style.cssText = 'width:30px;height:30px;font-size:16px;text-align:center;border:1px solid #07c160;border-radius:4px;outline:none;background:#fff;';
    av.replaceChildren(input);
    input.focus();
    input.select();
    function commit() {{
        var v = input.value.trim().slice(0, 4); // 最多4个字符
        var orig = av.getAttribute('data-orig-avatar') || '';
        if (v && v !== orig) {{
            AVATAR_EDITS[uid] = v;
        }} else {{
            delete AVATAR_EDITS[uid];
        }}
        localStorage.setItem('chatUserAvatars', JSON.stringify(AVATAR_EDITS));
        input.remove();
        applyAvatarEdits();
    }}
    input.addEventListener('blur', commit);
    input.addEventListener('keydown', function(ev) {{
        if (ev.key === 'Enter') {{ input.blur(); }}
        if (ev.key === 'Escape') {{
            delete AVATAR_EDITS[uid];
            localStorage.setItem('chatUserAvatars', JSON.stringify(AVATAR_EDITS));
            input.blur();
        }}
    }});
}}

function applyNameEdits(container) {{
    var all = (container || document).querySelectorAll('.msg-sender');
    all.forEach(function(el) {{
        var uid = el.getAttribute('data-user-id');
        var orig = el.getAttribute('data-orig-name');
        if (!uid) return;
        var decoded = DECODED_IDS[uid] || '';
        if (NAME_EDITS[uid]) {{
            el.innerHTML = NAME_EDITS[uid];
            el.classList.add('edited');
        }} else {{
            el.innerHTML = orig;
            el.classList.remove('edited');
        }}
    }});
}}

function setupNameEdit(el) {{
    el.addEventListener('dblclick', function(e) {{
        e.stopPropagation();
        var uid = el.getAttribute('data-user-id');
        var orig = el.getAttribute('data-orig-name');
        if (!uid) return;
        var currentName = NAME_EDITS[uid] || orig;
        var input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;
        el.innerHTML = '';
        el.appendChild(input);
        input.focus();
        input.select();
        function commit() {{
            var v = input.value.trim();
            if (v && v !== orig) {{
                NAME_EDITS[uid] = v;
            }} else {{
                delete NAME_EDITS[uid];
            }}
            localStorage.setItem('chatUserNames', JSON.stringify(NAME_EDITS));
            applyNameEdits();
        }}
        input.addEventListener('blur', commit);
        input.addEventListener('keydown', function(ev) {{
            if (ev.key === 'Enter') {{ input.blur(); }}
            if (ev.key === 'Escape') {{
                input.value = orig;
                delete NAME_EDITS[uid];
                localStorage.setItem('chatUserNames', JSON.stringify(NAME_EDITS));
                input.blur();
            }}
        }});
    }});
}}

var TOOLTIP_DELAY = 800; // 悬停时长（毫秒），达到后显示原始 ID
var tooltipTimer = null;

function scheduleTooltip(e, id) {{
    clearTimeout(tooltipTimer);
    var x = e.clientX;
    var y = e.clientY;
    tooltipTimer = setTimeout(function() {{
        showIdTooltip(x, y, id);
    }}, TOOLTIP_DELAY);
}}

function showIdTooltip(x, y, userId) {{
    var tooltip = document.getElementById('idTooltip');
    var decoded = DECODED_IDS[userId] || '';
    if (decoded) {{
        tooltip.innerHTML = '<span style="color:#95ec69;">' + decoded + '</span> <span style="opacity:0.6;">' + userId + '</span>';
    }} else {{
        tooltip.textContent = userId;
    }}
    tooltip.style.display = 'block';
    var w = tooltip.offsetWidth;
    var h = tooltip.offsetHeight;
    var px = x + 14;
    var py = y + 14;
    if (px + w > window.innerWidth) px = x - w - 10;
    if (py + h > window.innerHeight) py = y - h - 10;
    tooltip.style.left = px + 'px';
    tooltip.style.top = py + 'px';
}}

function hideIdTooltip() {{
    clearTimeout(tooltipTimer);
    document.getElementById('idTooltip').style.display = 'none';
}}

window.addEventListener('resize', function() {{
    isMobile = window.innerWidth <= 768;
}});

function goBack() {{
    document.getElementById('chatArea').classList.remove('mobile-active');
    document.getElementById('sidebar').classList.remove('mobile-hidden');
    currentRoom = null;
    renderSidebar();
}}

function renderSidebar() {{
    var list = document.getElementById('roomList');
    list.innerHTML = '';
    ROOMS.forEach(function(room, index) {{
        var div = document.createElement('div');
        div.className = 'room-item' + (currentRoom === room.id ? ' active' : '');
        div.onclick = function() {{ selectRoom(room.id); }};

        var firstMsg = CHATS[room.id] && CHATS[room.id][0];
        var firstUser = firstMsg ? firstMsg.user_name : '未知';

        div.innerHTML =
            '<div class="room-avatar" data-room-id="' + room.id + '">' + (room.users[0] || '💬')[0] + '</div>' +
            '<div class="room-info">' +
                '<div class="room-name">' + room.name + '</div>' +
                '<div class="room-meta">' + room.users.slice(0, 3).join('、') +
                (room.users.length > 3 ? ' 等' + room.users.length + '人' : '') + '</div>' +
            '</div>' +
            '<div class="room-badge">' + room.message_count + '</div>';
        list.appendChild(div);

        var roomAvatar = div.querySelector('.room-avatar');
        roomAvatar.addEventListener('mouseenter', function(e) {{
            scheduleTooltip(e, room.id);
        }});
        roomAvatar.addEventListener('mouseleave', hideIdTooltip);
    }});
}}

function formatTime(ts) {{
    var d = new Date(ts);
    var h = d.getHours().toString().padStart(2, '0');
    var m = d.getMinutes().toString().padStart(2, '0');
    return h + ':' + m;
}}
function formatDate(ts) {{
    var d = new Date(ts);
    return d.getFullYear() + '年' + (d.getMonth()+1) + '月' + d.getDate() + '日';
}}

function selectRoom(roomId) {{
    currentRoom = roomId;
    var room = ROOMS.find(function(r) {{ return r.id === roomId; }});
    var msgs = CHATS[roomId] || [];

    if (isMobile) {{
        document.getElementById('sidebar').classList.add('mobile-hidden');
        document.getElementById('chatArea').classList.add('mobile-active');
    }}

    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('chatHeader').style.display = 'flex';
    document.getElementById('chatMessages').style.display = 'block';
    document.getElementById('chatTitle').textContent = room.name;
    document.getElementById('chatSubInfo').textContent =
        room.users.join('、') + ' · ' + room.message_count + ' 条消息';

    var container = document.getElementById('chatMessages');
    container.innerHTML = '';

    var lastDate = '';
    var userIds = [];
    msgs.forEach(function(m) {{
        if (userIds.indexOf(m.user_id) === -1) userIds.push(m.user_id);
    }});
    currentUserId = userIds[0];

    msgs.forEach(function(msg, i) {{
        var msgDate = msg.timestamp.split(' ')[0];
        if (msgDate !== lastDate) {{
            lastDate = msgDate;
            var dateLabel = DATE_GROUPS[msgDate] || '';
            container.innerHTML +=
                '<div class="time-divider">' +
                    '<span>' + formatDate(msg.timestamp) + '</span>' +
                    (dateLabel ? '<span class="date-label">' + dateLabel + '</span>' : '') +
                '</div>';
        }}

        var isSelf = msg.user_id === currentUserId;
        container.innerHTML +=
            '<div class="msg-row' + (isSelf ? ' self' : '') + '">' +
                '<div class="msg-avatar" data-user-id="' + msg.user_id + '" data-orig-avatar="' + msg.user_avatar + '" style="background:' + msg.user_color + '20;color:' + msg.user_color + '">' +
                    msg.user_avatar +
                '</div>' +
                '<div class="msg-bubble-wrap">' +
                    '<div class="msg-sender" data-user-id="' + msg.user_id + '" data-orig-name="' + msg.user_name.replace(/"/g, '&quot;') + '" style="color:' + msg.user_color + '">' +
                        msg.user_name +
                    '</div>' +
                    '<div class="msg-bubble">' +
                        msg.content +
                    '</div>' +
                    '<div class="msg-time">' + formatTime(msg.timestamp) + '</div>' +
                '</div>' +
            '</div>';
    }});

    var avatarEls = container.querySelectorAll('.msg-avatar');
    avatarEls.forEach(function(av) {{
        var uid = av.getAttribute('data-user-id');
        if (!uid) return;
        av.addEventListener('mouseenter', function(e) {{
            if (editMode) return;
            scheduleTooltip(e, uid);
        }});
        av.addEventListener('mouseleave', hideIdTooltip);
        av.addEventListener('click', function(e) {{
            e.stopPropagation();
            editAvatar(av, uid);
        }});
        av.title = '';
    }});

    if (editMode) {{
        applyEditModeInputs();
    }} else {{
        applyNameEdits(container);
        applyAvatarEdits(container);
        var senderEls = container.querySelectorAll('.msg-sender');
        senderEls.forEach(setupNameEdit);
    }}

    container.scrollTop = container.scrollHeight;

    renderSidebar();
}}

var DATE_GROUPS = {json.dumps(DATE_GROUP_NAMES, ensure_ascii=False)};

renderSidebar();
if (ROOMS.length > 0) {{
    selectRoom(ROOMS[0].id);
}}
</script>
</body>
</html>'''
    return html

def _default_avatar_color(user_id: str) -> tuple[str, str]:
    
    colors = ["#576b95", "#07c160", "#e6a23c", "#409eff", "#f56c6c", "#909399"]
    avatars = ["👤", "👥", "🗣️", "💭", "📝", "🫥"]
    idx = hash(user_id) % len(colors)
    return avatars[idx], colors[idx]


class HtmlGenPanel:
    

    def __init__(self, parent, toolbox):
        self.toolbox = toolbox
        self.cfg = toolbox.cfg
        self.frame = ttk.Frame(parent)
        self.top = self.frame.winfo_toplevel()
        self._build_ui()
        self._refresh_path_label()

    def _chatbox_path(self) -> str:
        p = str(self.cfg.get("chatbox_path") or "").strip()
        if not p:
            p = str(Path(str(self.cfg.get("output") or APP_DIR)) / ".runtime" / "chatbox")
        return p

    def _build_ui(self) -> None:
        pad = ttk.Frame(self.frame, padding=16)
        pad.pack(fill="both", expand=True)

        ttk.Label(pad, text="生成微信风格聊天记录网页",
                  font=("Microsoft YaHei", 14, "bold")).pack(anchor="w")
        ttk.Label(pad, text="数据源为下载后的 .runtime/chatbox 文件夹，"
                            "HTML 将保存到本程序所在目录并自动用浏览器打开。",
                  foreground="#666").pack(anchor="w", pady=(4, 10))

        path_row = ttk.Frame(pad)
        path_row.pack(fill="x", pady=6)
        ttk.Label(path_row, text="聊天数据：").pack(side="left")
        self.path_lbl = ttk.Label(path_row, text="", foreground="#1a6fb5")
        self.path_lbl.pack(side="left", padx=4)
        ttk.Button(path_row, text="选择文件夹", command=self._pick_folder).pack(side="left", padx=4)

        self.gen_btn = ttk.Button(
            pad, text="⚙  生成 HTML 并自动打开", command=self._generate, width=28)
        self.gen_btn.pack(anchor="w", pady=12)

        ttk.Label(pad, text="输出文件：", foreground="#888").pack(anchor="w")
        self.out_lbl = ttk.Label(pad, text="", foreground="#666")
        self.out_lbl.pack(anchor="w", pady=(0, 8))

        log_frame = ttk.Frame(pad)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=10, state="disabled", wrap="word",
                           font=("Consolas", 10))
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _pick_folder(self) -> None:
        d = filedialog.askdirectory(initialdir=self._chatbox_path(),
                                    title="选择 chatbox 文件夹（含各聊天室子文件夹）")
        if d:
            self.cfg["chatbox_path"] = d
            self.toolbox.save_config()
            self._refresh_path_label()

    def _refresh_path_label(self) -> None:
        self.path_lbl.config(text=self._chatbox_path())
        out = APP_DIR / f"chat_output_{datetime.now():%Y-%m-%d}.html"
        self.out_lbl.config(text=str(out))

    def _log(self, text: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _generate(self) -> None:
        chatbox = self._chatbox_path()
        if not Path(chatbox).is_dir():
            mb.showerror(
                "错误",
                f"聊天数据文件夹不存在：\n{chatbox}\n\n"
                "请先在「下载」页下载数据，或点击「选择文件夹」手动指定。")
            return
        self.gen_btn.config(state="disabled")
        self._log("开始生成……")

        def task():
            global CHATBOX_DIR, USER_NAME_MAP, ROOM_NAME_MAP, DATE_GROUP_NAMES
            global DECODED_IDS, HTML_TITLE, HTML_SUBTITLE, get_user_info
            try:
                
                
                buf = io.StringIO()
                old_out = sys.stdout
                try:
                    sys.stdout = buf
                    
                    
                    user_names = self.cfg.get("user_names") or {}
                    room_names = self.cfg.get("room_names") or {}
                    date_labels = self.cfg.get("date_labels") or {}
                    decoded_ids = self.cfg.get("decoded_ids") or {}

                    
                    HTML_TITLE = (self.cfg.get("html_title") or "").strip() or "对话记录"
                    HTML_SUBTITLE = (self.cfg.get("html_subtitle") or "").strip() or "内部通讯"

                    chatbox_dir = Path(chatbox)

                    
                    all_user_ids: set[str] = set()
                    if chatbox_dir.is_dir():
                        for room_dir in chatbox_dir.iterdir():
                            if not room_dir.is_dir():
                                continue
                            if room_dir.name.startswith("00000000-0000-0000"):
                                continue
                            for f in room_dir.glob("*.txt"):
                                all_user_ids.add(f.stem)

                    
                    USER_NAME_MAP = {}
                    for uid in sorted(all_user_ids):
                        name = user_names.get(uid, "")
                        if not name:
                            name = f"用户{uid[:6]}"
                        avatar, color = _default_avatar_color(uid)
                        USER_NAME_MAP[uid] = {
                            "name": name, "avatar": avatar, "color": color,
                        }
                    for uid, name in user_names.items():
                        if not name:
                            continue
                        if uid in USER_NAME_MAP:
                            USER_NAME_MAP[uid]["name"] = name
                        else:
                            avatar, color = _default_avatar_color(uid)
                            USER_NAME_MAP[uid] = {
                                "name": name, "avatar": avatar, "color": color,
                            }

                    ROOM_NAME_MAP = dict(room_names)
                    DATE_GROUP_NAMES = dict(date_labels)
                    DECODED_IDS = dict(decoded_ids)

                    
                    def _get_user_info(file_hash):
                        if file_hash in USER_NAME_MAP:
                            return USER_NAME_MAP[file_hash]
                        name = user_names.get(file_hash, f"用户{file_hash[:6]}")
                        avatar, color = _default_avatar_color(file_hash)
                        entry = {"name": name, "avatar": avatar, "color": color}
                        USER_NAME_MAP[file_hash] = entry
                        return entry
                    get_user_info = _get_user_info

                    CHATBOX_DIR = chatbox_dir
                    rooms = load_all_chats()
                    if not rooms:
                        raise RuntimeError("未找到任何聊天数据（chatbox 目录为空或无消息）")
                    total = sum(len(msgs) for msgs in rooms.values())
                    html = generate_html(rooms)
                    out = APP_DIR / f"chat_output_{datetime.now():%Y-%m-%d}.html"
                    out.write_text(html, encoding="utf-8")
                finally:
                    sys.stdout = old_out
                    gc_out = buf.getvalue().strip()

                self.top.after(0, lambda: self._log(gc_out) if gc_out else None)
                self.top.after(0, lambda: self._done(out, len(rooms), total))
            except Exception as exc:
                self.top.after(0, lambda: self._fail(str(exc)))

        threading.Thread(target=task, daemon=True).start()

    def _done(self, out: Path, rooms: int, total: int) -> None:
        self.gen_btn.config(state="normal")
        self._log(f"✅ 已生成：{out}")
        self._log(f"   共 {rooms} 个会话房间，{total} 条消息")
        try:
            os.startfile(str(out))
            self._log("已用默认浏览器打开。")
        except Exception as e:
            self._log(f"自动打开失败（可手动打开）：{e}")

    def _fail(self, err: str) -> None:
        self.gen_btn.config(state="normal")
        self._log(f"❌ 生成失败：{err}")
        mb.showerror("生成失败", err)


class ToolboxApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1280x760")
        self.root.minsize(960, 600)
        self.cfg = load_config()
        if SPECIAL:
            
            self._migrate_legacy_config()
        self.tray_icon = None
        self.tray_thread = None
        self._closing = False

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.download_panel = DownloadPanel(nb, self)
        self.view_panel = QuickViewPanel(nb, self)
        self.html_panel = HtmlGenPanel(nb, self)

        
        if not self.view_panel.chatbox_path:
            cand = Path(str(self.cfg.get("output") or "")) / ".runtime" / "chatbox"
            if cand.is_dir():
                self.cfg["chatbox_path"] = str(cand)
                self.view_panel._load_cfg()
                self.view_panel._scan()
                self.html_panel._refresh_path_label()

        nb.add(self.download_panel.frame, text="下载")
        nb.add(self.view_panel.frame, text="快速查看")
        nb.add(self.html_panel.frame, text="生成网页")
        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_window_icon()
        self._create_tray_icon()

    def save_config(self) -> None:
        save_config(self.cfg)

    def _migrate_legacy_config(self) -> None:
        
        fresh = not CONFIG_PATH.exists()
        legacy_dir = APP_DIR.parent / "cfms_downloader"
        try:
            if fresh:
                dl = legacy_dir / "cfms_downloader_settings.json"
                if dl.exists():
                    d = json.loads(dl.read_text("utf-8"))
                    for k in ("host", "port", "username", "password", "auto_refresh",
                              "interval", "proxy_type", "proxy_host", "proxy_port", "output"):
                        if d.get(k) not in (None, ""):
                            self.cfg[k] = d[k]
                vw = legacy_dir / "chatbox_viewer_config.json"
                if vw.exists():
                    v = json.loads(vw.read_text("utf-8"))
                    if v.get("chatbox_path"):
                        self.cfg["chatbox_path"] = v["chatbox_path"]
        except Exception:
            pass

        changed = False
        
        viewer_sources = [
            legacy_dir / "chatbox_viewer_config.json",
            legacy_dir / "dist" / "chatbox_viewer_config.json",
        ]
        override = not self.cfg.get("_legacy_viewer_migrated")
        try:
            for vw in viewer_sources:
                if not vw.exists():
                    continue
                v = json.loads(vw.read_text("utf-8"))
                if not isinstance(v, dict):
                    continue
                
                for rid, name in (v.get("room_names") or {}).items():
                    if name and (override or rid not in self.cfg["room_names"]):
                        self.cfg["room_names"][rid] = name
                        changed = True
                
                for uid, name in (v.get("user_names") or {}).items():
                    if name and (override or uid not in self.cfg["user_names"]):
                        self.cfg["user_names"][uid] = name
                        changed = True
                    
                    if name and uid not in self.cfg["decoded_ids"]:
                        self.cfg["decoded_ids"][uid] = name
                        changed = True
                if v.get("chatbox_path") and not self.cfg.get("chatbox_path"):
                    self.cfg["chatbox_path"] = v["chatbox_path"]
                    changed = True
        except Exception:
            pass
        if override:
            self.cfg["_legacy_viewer_migrated"] = 1
            changed = True

        
        try:
            for src, key in (
                (APP_DIR / "users.json", "user_names"),
                (APP_DIR / "rooms.json", "room_names"),
                (APP_DIR / "dates.json", "date_labels"),
            ):
                if not src.exists():
                    continue
                d = json.loads(src.read_text("utf-8"))
                if not isinstance(d, dict):
                    continue
                if key == "user_names":
                    for uid, info in d.items():
                        if not isinstance(info, dict):
                            continue
                        if info.get("name") and uid not in self.cfg["user_names"]:
                            self.cfg["user_names"][uid] = info["name"]
                            changed = True
                        if info.get("id") and uid not in self.cfg["decoded_ids"]:
                            self.cfg["decoded_ids"][uid] = info["id"]
                            changed = True
                elif key == "room_names":
                    for rid, name in d.items():
                        if name and rid not in self.cfg["room_names"]:
                            self.cfg["room_names"][rid] = name
                            changed = True
                elif key == "date_labels":
                    for date_str, label in d.items():
                        if label and date_str not in self.cfg["date_labels"]:
                            self.cfg["date_labels"][date_str] = label
                            changed = True
        except Exception:
            pass

        if changed:
            save_config(self.cfg)

    def _on_tab_changed(self, event=None) -> None:
        try:
            nb = event.widget
            sel = nb.nametowidget(nb.select())
            if sel is self.view_panel.frame:
                self.view_panel._scan()
        except Exception:
            pass

    
    def _set_window_icon(self) -> None:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            tmp.write(_icon_bytes())
            tmp.close()
            self.root.iconbitmap(tmp.name)
            os.unlink(tmp.name)
        except Exception:
            pass

    def _create_tray_icon(self) -> None:
        if not TRAY_AVAILABLE:
            return
        try:
            image = Image.open(io.BytesIO(_icon_bytes())).resize((64, 64))
            menu = pystray.Menu(
                pystray.MenuItem("显示窗口", self._show_window, default=True),
                pystray.MenuItem("退出", self._quit_app),
            )
            tray_id = "cfms_toolbox" + ("_special" if SPECIAL else "_regular")
            self.tray_icon = pystray.Icon(tray_id, image, APP_TITLE, menu)
            self.tray_thread = threading.Thread(
                target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception:
            self.tray_icon = None

    def _show_window(self) -> None:
        try:
            self.root.after(0, self._restore_window)
        except Exception:
            pass

    def _restore_window(self) -> None:
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def _quit_app(self) -> None:
        self._closing = True
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.after(0, self._force_close)
        except Exception:
            pass

    def _force_close(self) -> None:
        try:
            self.download_panel.shutdown()
        except Exception:
            pass
        try:
            self.view_panel._save_cfg()
        except Exception:
            pass
        try:
            self.html_panel._refresh_path_label()
        except Exception:
            pass
        save_config(self.cfg)
        self.root.destroy()

    def _on_close(self) -> None:
        if self._closing:
            return
        if TRAY_AVAILABLE and self.tray_icon is not None:
            
            self.root.withdraw()
            try:
                self.tray_icon.notify(
                    "程序已最小化到托盘，自动刷新仍在运行。",
                    APP_TITLE)
            except Exception:
                pass
        else:
            self._quit_app()

    def _notify(self, title: str, message: str) -> None:
        try:
            if TRAY_AVAILABLE and self.tray_icon is not None:
                self.tray_icon.notify(f"{title}\n{message}", APP_TITLE)
        except Exception:
            pass


def main() -> None:
    app = ToolboxApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
