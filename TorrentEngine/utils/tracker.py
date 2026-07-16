import random
import struct
import socket
import urllib.request
import urllib.parse
from urllib.parse import urlparse
from .bencode import bdecode

class SecurityError(Exception):
    pass

class UDPTrackerClient:
    @staticmethod
    def get_peers(announceURL: str, info_hash: bytes, totalSize: int, local_port: int = 6881) -> list[tuple[str, int]]:
        if announceURL.startswith("udp://"):
            return UDPTrackerClient._get_peers_udp(announceURL, info_hash, totalSize, local_port)
        elif announceURL.startswith("http://") or announceURL.startswith("https://"):
            return UDPTrackerClient._get_peers_http(announceURL, info_hash, totalSize, local_port)
        else:
            raise ValueError(f"Unsupported tracker protocol: {announceURL}")

    @staticmethod
    def _get_peers_http(announceURL: str, info_hash: bytes, totalSize: int, local_port: int) -> list[tuple[str, int]]:
        parsedURL = urlparse(announceURL)
        if not parsedURL.hostname:
            raise ValueError("Malformed Tracker Connection endpoint")
        client_peer_id = b"-ZH0001-" + bytes(random.randint(0, 9) for _ in range(12))
        
        params = {
            'port': local_port,
            'uploaded': 0,
            'downloaded': 0,
            'left': totalSize,
            'compact': 1
        }
        
        url_params = urllib.parse.urlencode(params)
        info_hash_encoded = urllib.parse.quote_from_bytes(info_hash)
        peer_id_encoded = urllib.parse.quote_from_bytes(client_peer_id)
        
        separator = '&' if '?' in announceURL else '?'
        request_url = f"{announceURL}{separator}{url_params}&info_hash={info_hash_encoded}&peer_id={peer_id_encoded}"
        
        req = urllib.request.Request(
            request_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=8.0) as response:
                response_data = response.read()
                
            decoded_response = bdecode(response_data)
            if not isinstance(decoded_response, dict):
                return []
                
            failure_reason = decoded_response.get(b'failure reason', decoded_response.get('failure reason'))
            if failure_reason:
                if isinstance(failure_reason, bytes):
                    failure_reason = failure_reason.decode('utf-8')
                raise ValueError(f"Tracker failed: {failure_reason}")
                
            peers = decoded_response.get(b'peers', decoded_response.get('peers'))
            peer_list = []
            
            if isinstance(peers, bytes):
                for offset in range(0, len(peers) - (len(peers) % 6), 6):
                    peer_bytes = peers[offset:offset+6]
                    ip_bytes = peer_bytes[:4]
                    port_bytes = peer_bytes[4:]
                    ip_string = socket.inet_ntoa(ip_bytes)
                    peer_port = struct.unpack('!H', port_bytes)[0]
                    peer_list.append((ip_string, peer_port))
            elif isinstance(peers, list):
                for p in peers:
                    ip = p.get(b'ip', p.get('ip'))
                    port = p.get(b'port', p.get('port'))
                    if isinstance(ip, bytes):
                        ip = ip.decode('utf-8')
                    if ip and port:
                        peer_list.append((ip, port))
                        
            return peer_list
        except Exception as e:
            raise ConnectionError(f"HTTP tracker request failed: {str(e)}")

    @staticmethod
    def _get_peers_udp(announceURL: str, info_hash: bytes, totalSize: int, local_port: int) -> list[tuple[str, int]]:
        parsedURL = urlparse(announceURL)
        host = parsedURL.hostname
        port = parsedURL.port
        if not host or port is None:
            raise ValueError("Malformed Tracker Connection endpoint")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(8.0)
        try:
            trackerAddress = (host, port)
            connection_magic_constant = 0x41727101980
            action_connect = 0
            transaction_id = random.randint(0, 2147483647)
            connect_packet = struct.pack('!qii', connection_magic_constant, action_connect, transaction_id)
            sock.sendto(connect_packet, trackerAddress)
            response, _ = sock.recvfrom(16)
            if len(response) < 16:
                raise ConnectionError("Truncated responseeceived during tracker connection")
            res_action, res_transaction_id, current_connection_id = struct.unpack('!iiq', response)
            if res_transaction_id != transaction_id or res_action != 0:
                raise SecurityError("hash mismatch or invalid socket")
            action_announce = 1
            announce_transaction_id = random.randint(0, 2147483647)
            client_peer_id = b"-ZH0001-" + bytes(random.randint(0, 9) for _ in range(12))
            
            downloaded = 0
            uploaded = 0
            bytes_left = totalSize
            event = 2        
            ip_address = 0   
            key = random.randint(0, 2147483647)
            num_want = 50
            announce_packet = struct.pack(
                '!qii20s20sqqqiiiih',
                current_connection_id,
                action_announce,
                announce_transaction_id,
                info_hash,
                client_peer_id,
                downloaded,
                bytes_left,
                uploaded,
                event,
                ip_address,
                key,
                num_want,
                local_port
            )
            sock.sendto(announce_packet, trackerAddress)
            response_payload, _ = sock.recvfrom(2048)
            if len(response_payload) < 20:
                raise ConnectionError("Malformed network stream")
            header_data = response_payload[:20]
            res_ann_action, res_ann_trans_id, interval, leechers, seeders = struct.unpack('!iiiii', header_data)
            if res_ann_trans_id != announce_transaction_id or res_ann_action != 1:
                raise SecurityError("Invalid transaction alignment ")
            raw_peers_buffer = response_payload[20:]
            peer_list = []
            for offset in range(0, len(raw_peers_buffer) - (len(raw_peers_buffer) % 6), 6):
                peer_bytes = raw_peers_buffer[offset:offset+6]
                ip_bytes = peer_bytes[:4]
                port_bytes = peer_bytes[4:]
                ip_string = socket.inet_ntoa(ip_bytes)
                peer_port = struct.unpack('!H', port_bytes)[0]  
                peer_list.append((ip_string, peer_port))
            return peer_list
        finally:
            sock.close()

    # Backward compatibility alias
    getPeers = get_peers