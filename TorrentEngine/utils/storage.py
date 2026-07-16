import os
import hashlib

class TorrentStorage:
    def __init__(self, downloadDir: str, metadata: dict):
        self.downloadDir = downloadDir
        self.metadata = metadata
        self.pieceLength = metadata['piece_length']
        self.files = metadata['files']
        self.totalSize = metadata['total_size']
        self._setup_files()

    def _setup_files(self):
        if not os.path.exists(self.downloadDir):
            os.makedirs(self.downloadDir)
            
        for fileInfo in self.files:
            path = os.path.join(self.downloadDir, fileInfo['path'])
            dirPath = os.path.dirname(path)
            if not os.path.exists(dirPath):
                os.makedirs(dirPath)
            if not os.path.exists(path):
                with open(path, 'wb') as f:
                    f.truncate(fileInfo['length'])

    def writeBlock(self, pieceIndex: int, begin: int, blockData: bytes):
        globalOffset = (pieceIndex * self.pieceLength) + begin
        bytesToWrite = len(blockData)
        dataOffset = 0
        currentOffset = 0

        for fileInfo in self.files:
            fileLength = fileInfo['length']
            fileStart = currentOffset
            fileEnd = fileStart + fileLength

            if globalOffset < fileEnd and (globalOffset + bytesToWrite) > fileStart:
                writeStart = max(globalOffset, fileStart)
                writeEnd = min(globalOffset + bytesToWrite, fileEnd)
                writeLength = writeEnd - writeStart

                filePath = os.path.join(self.downloadDir, fileInfo['path'])
                relativeOffset = writeStart - fileStart
                sliceData = blockData[dataOffset : dataOffset + writeLength]

                with open(filePath, 'r+b') as f:
                    f.seek(relativeOffset)
                    f.write(sliceData)

                dataOffset += writeLength

            currentOffset += fileLength

    def readPiece(self, pieceIndex: int) -> bytes:
        globalOffset = pieceIndex * self.pieceLength
        bytesToRead = self.pieceLength
        if (pieceIndex + 1) * self.pieceLength > self.totalSize:
            bytesToRead = self.totalSize - globalOffset

        pieceData = b''
        currentOffset = 0

        for fileInfo in self.files:
            fileLength = fileInfo['length']
            fileStart = currentOffset
            fileEnd = fileStart + fileLength

            if globalOffset < fileEnd and (globalOffset + bytesToRead) > fileStart:
                readStart = max(globalOffset, fileStart)
                readEnd = min(globalOffset + bytesToRead, fileEnd)
                readLength = readEnd - readStart

                filePath = os.path.join(self.downloadDir, fileInfo['path'])
                relativeOffset = readStart - fileStart

                with open(filePath, 'rb') as f:
                    f.seek(relativeOffset)
                    pieceData += f.read(readLength)

            currentOffset += fileLength

        return pieceData

    def verifyPiece(self, pieceIndex: int, expectedHash: bytes) -> bool:
        pieceData = self.readPiece(pieceIndex)
        calculatedHash = hashlib.sha1(pieceData).digest()
        return calculatedHash == expectedHash