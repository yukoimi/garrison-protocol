"""卫戍协议 — LAN联机网络模块

TCP长度前缀JSON协议:
  [4字节大端长度] [UTF-8 JSON载荷]

主机 = player_id 0, 客户端 = player_id 1,2,3...
"""

import json, socket, struct, threading
from queue import Queue
from typing import Optional


def _encode(msg: dict) -> bytes:
    data = json.dumps(msg, ensure_ascii=False).encode('utf-8')
    return struct.pack('>I', len(data)) + data


class _BufferedReader:
    """带缓冲的TCP帧读取器 (单次recv可能收不完整)"""
    def __init__(self):
        self.buf = b''

    def read_msg(self, sock: socket.socket) -> Optional[dict]:
        while len(self.buf) < 4:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            self.buf += chunk
        length = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4 + length:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            self.buf += chunk
        body = self.buf[4:4+length]
        self.buf = self.buf[4+length:]
        return json.loads(body.decode('utf-8'))


class NetManager:
    """网络管理器 — 支持主机/客户端双模式"""

    def __init__(self):
        self.mode = 'single'  # single | host | client
        self.rx_queue: Queue = Queue()   # 网络线程→主线程
        self.tx_queue: Queue = Queue()   # 主线程→网络线程

        self.player_id = -1
        self.players: list[dict] = []    # [{id, name, ready, hp, alive}]

        self._host_sock: Optional[socket.socket] = None
        self._client_socks: list[tuple[int, socket.socket]] = []  # host视角
        self._client_sock: Optional[socket.socket] = None          # client视角
        self._reader: Optional[_BufferedReader] = None
        self._running = False
        self._connected = threading.Event()
        self._lock = threading.Lock()

    # ── 启动 ────────────────────────────────────────

    def start_host(self, port: int = 5555):
        """以主机模式启动"""
        self.mode = 'host'
        self.player_id = 0
        self._running = True
        self._connected.set()  # 主机总是"已连接"
        threading.Thread(target=self._accept_thread, args=(port,), daemon=True).start()
        threading.Thread(target=self._sender_thread, daemon=True).start()

    def start_client(self, host: str = '127.0.0.1', port: int = 5555):
        """以客户端模式连接主机"""
        self.mode = 'client'
        self._running = True
        self._connected.clear()
        threading.Thread(target=self._client_thread, args=(host, port), daemon=True).start()
        threading.Thread(target=self._sender_thread, daemon=True).start()

    # ── 收发 ────────────────────────────────────────

    def send(self, msg: dict, target_id: int = -1):
        """发送消息。target_id=-1为广播(host)或发往server(client)"""
        self.tx_queue.put((msg, target_id))

    def poll(self) -> list[dict]:
        """非阻塞取出所有已收到的消息"""
        msgs = []
        while not self.rx_queue.empty():
            msgs.append(self.rx_queue.get_nowait())
        return msgs

    def stop(self):
        self._running = False
        self._connected.set()
        with self._lock:
            for _, s in self._client_socks:
                try: s.close()
                except: pass
        if self._client_sock:
            try: self._client_sock.close()
            except: pass
        if self._host_sock:
            try: self._host_sock.close()
            except: pass

    # ── 内部: 主机线程 ─────────────────────────────

    def _accept_thread(self, port: int):
        self._host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._host_sock.bind(('0.0.0.0', port))
        self._host_sock.listen(4)
        self._host_sock.settimeout(1.0)

        next_id = 1
        while self._running:
            try:
                cs, addr = self._host_sock.accept()
                cid = next_id; next_id += 1
                self._client_socks.append((cid, cs))
                threading.Thread(target=self._host_reader_thread,
                                 args=(cid, cs), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _host_reader_thread(self, cid: int, sock: socket.socket):
        reader = _BufferedReader()
        while self._running:
            try:
                msg = reader.read_msg(sock)
            except:
                msg = None
            if msg is None:
                self._on_disconnect(cid)
                return
            msg['_client_id'] = cid
            self.rx_queue.put(msg)

    def _on_disconnect(self, cid: int):
        with self._lock:
            self._client_socks = [(i, s) for i, s in self._client_socks if i != cid]
        self.rx_queue.put({'type': 'disconnect', 'client_id': cid})

    # ── 内部: 客户端线程 ─────────────────────────────

    def _client_thread(self, host: str, port: int):
        self._client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._client_sock.connect((host, port))
        except OSError as e:
            self.rx_queue.put({'type': 'connect_error', 'error': str(e)})
            return
        self._reader = _BufferedReader()
        self._connected.set()
        while self._running:
            try:
                msg = self._reader.read_msg(self._client_sock)
            except:
                msg = None
            if msg is None:
                self.rx_queue.put({'type': 'disconnect', 'client_id': self.player_id})
                return
            self.rx_queue.put(msg)

    # ── 内部: 发送线程 ─────────────────────────────

    def _sender_thread(self):
        while self._running:
            try:
                msg, target = self.tx_queue.get(timeout=0.5)
            except:
                continue
            data = _encode(msg)
            if self.mode == 'host':
                socks = list(self._client_socks)
                for cid, sock in socks:
                    if target != -1 and cid != target:
                        continue
                    try:
                        sock.sendall(data)
                    except:
                        pass
            elif self.mode == 'client':
                self._connected.wait(timeout=5)
                if self._client_sock:
                    try:
                        self._client_sock.sendall(data)
                    except:
                        pass
