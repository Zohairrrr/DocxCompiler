
import time
import random
import struct
from .storage import TorrentStorage
from .peer import PeerConnection
from .tracker import UDPTrackerClient

class TorrentDownloader:
    def __init__(self, metadata: dict, downloadDir: str):
        self.metadata = metadata
        self.downloadDir = downloadDir
        self.infoHash = metadata['info_hash']
        self.pieceLength = metadata['piece_length']
        self.pieceHashes = metadata['piece_hashes']
        self.totalSize = metadata['total_size']
        self.totalPieces = len(self.pieceHashes)
        
        self.peerId = b"-ZH0001-" + bytes(random.randint(0, 9) for _ in range(12))
        self.storage = TorrentStorage(downloadDir, metadata)
        self.completedPieces = [False] * self.totalPieces
        self.blockSize = 16384

    def start(self):
        peers = UDPTrackerClient.get_peers(
            self.metadata['announce_url'],
            self.infoHash,
            self.totalSize
        )
        
        if not peers:
            raise Exception()

        for ip, port in peers:
            peer = None
            try:
                peer = PeerConnection(ip, port, self.infoHash, self.peerId)
                peer.connect()
                peer.send_handshake()
                peer.receive_handshake()
                
                msgId, payload = peer.read_message()
                if msgId == 5:
                    peer.parse_bitfield(payload, self.totalPieces)
                
                peer.send_interested()
                
                unchoked = False
                startTime = time.time()
                while time.time() - startTime < 10:
                    msgId, payload = peer.read_message()
                    if msgId == 1:
                        unchoked = True
                        break
                        
                if not unchoked:
                    peer.close()
                    continue
                    
                self._download_loop(peer)
                break
            except Exception:
                if peer:
                    peer.close()

    def _download_loop(self, peer: PeerConnection):
        for pieceIdx in range(self.totalPieces):
            if self.completedPieces[pieceIdx]:
                continue
                
            if peer.bitfield and not peer.bitfield[pieceIdx]:
                continue
                
            success = self._download_piece(peer, pieceIdx)
            if success:
                self.completedPieces[pieceIdx] = True

    def _download_piece(self, peer: PeerConnection, pieceIdx: int) -> bool:
        currentPieceLength = self.pieceLength
        if pieceIdx == self.totalPieces - 1:
            currentPieceLength = self.totalSize - (pieceIdx * self.pieceLength)
            
        numBlocks = (currentPieceLength + self.blockSize - 1) // self.blockSize
        blocksData = [None] * numBlocks
        
        maxRequests = 5
        requested = 0
        received = 0
        
        while received < numBlocks:
            while requested < numBlocks and (requested - received) < maxRequests:
                begin = requested * self.blockSize
                length = min(self.blockSize, currentPieceLength - begin)
                peer.send_request(pieceIdx, begin, length)
                requested += 1
                
            try:
                msgId, payload = peer.read_message()
                if msgId == 7:
                    index, begin = struct.unpack_from('!II', payload)
                    blockData = payload[8:]
                    blockIdx = begin // self.blockSize
                    
                    if index == pieceIdx and blockIdx < numBlocks and blocksData[blockIdx] is None:
                        blocksData[blockIdx] = blockData
                        self.storage.writeBlock(pieceIdx, begin, blockData)
                        received += 1
            except Exception:
                return False
                
        expectedHash = self.pieceHashes[pieceIdx]
        return self.storage.verifyPiece(pieceIdx, expectedHash)