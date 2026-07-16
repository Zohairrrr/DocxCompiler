# TorrentEngine/utils/peer.py
import socket
import struct
import time

class PeerConnection:
    def __init__(self, ip: str, port: int, infoHash: bytes, peer_id: bytes):
        self.ip = ip
        self.port = port
        self.infoHash = infoHash
        self.peer_id = peer_id
        self.sock = None

        self.amchoking = True
        self.aminterested = False
        self.peerChoking = True
        self.peerInterested = False

        self.bitfield = None 
    
    def connect(self, timeout: float = 5.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.ip, self.port))

    def _recv_all(self, length: int) -> bytes:
        buffer = b''
        while len(buffer) < length:
            needed = length - len(buffer)
            try:
                chunk = self.sock.recv(needed)
                if not chunk:
                    raise ConnectionResetError()
                buffer += chunk
            except socket.timeout:
                raise TimeoutError()
        return buffer

    def send_handshake(self):
        pstrlen = b'\x13'
        pstr = b'BitTorrent protocol'
        reserved = b'\x00' * 8
        packet = pstrlen + pstr + reserved + self.infoHash + self.peer_id
        self.sock.sendall(packet)

    def receive_handshake(self) -> bytes:
        pstrlen_raw = self._recv_all(1)
        pstrlen = pstrlen_raw[0]
        
        if pstrlen != 19:
            raise ValueError()
        handshake_payload = self._recv_all(67)
        pstr = handshake_payload[:19]
        if pstr != b'BitTorrent protocol':
            raise ValueError()    
        received_hash = handshake_payload[27:47]
        if received_hash != self.infoHash:
            raise ValueError()  
        peer_id = handshake_payload[47:]
        return peer_id

    def send_message(self, message_id: int, payload: bytes = b''):
        msg_length = 1 + len(payload)
        header = struct.pack('!Ib', msg_length, message_id)
        self.sock.sendall(header + payload)

    def read_message(self) -> tuple[int | None, bytes]:
        length_bytes = self._recv_all(4)
        msg_length = struct.unpack('!I', length_bytes)[0]
        if msg_length == 0:
            return None, b''  
        payload_bytes = self._recv_all(msg_length)
        message_id = payload_bytes[0]
        payload = payload_bytes[1:]
        if message_id == 0:
            self.peerChoking = True
        elif message_id == 1:
            self.peerChoking = False
        return message_id, payload

    def parse_bitfield(self, payload: bytes, total_pieces: int):
        self.bitfield = []
        for byte_idx, byte in enumerate(payload):
            for bit_idx in range(8):
                piece_idx = (byte_idx * 8) + bit_idx
                if piece_idx < total_pieces:
                    has_piece = (byte >> (7 - bit_idx)) & 1
                    self.bitfield.append(bool(has_piece))

    def send_interested(self):
        self.aminterested = True
        self.send_message(2)

    def send_request(self, index: int, begin: int, length: int):
        payload = struct.pack('!III', index, begin, length)
        self.send_message(6, payload)

    def close(self):
        if self.sock:
            self.sock.close()