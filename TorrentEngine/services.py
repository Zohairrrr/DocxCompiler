import hashlib
import os
from .utils.bencode import bencode, bdecode,BenCodeError

class TorrentMetaDataService:
    @staticmethod
    def parse_torrent_file(fileContent:bytes) -> dict:
        try:
            metaInfo = bdecode(fileContent)
        except BenCodeError as e:
            raise ValueError("BenCode Parsing Failed")
        if 'info' not in metaInfo:
            raise ValueError("IvalidTorrent File Structure")
        info_dict = metaInfo['info']
        serialized = bencode(info_dict)
        sha1_tracker = hashlib.sha1()
        sha1_tracker.update(serialized)
        info_hash = sha1_tracker.digest()
        rawInfo = info_dict.get('pieces',b'')
        if len(rawInfo) % 20 != 0:
            raise ValueError("Invalid Metaadata")
        pieceHash = [rawInfo[i:i+20] for i in range(0, len(rawInfo), 20)]
        filesMetaData = []
        total_size = 0
        if 'files' in info_dict:
            for file_entry in info_dict['files']:
                file_length = file_entry['length']
                total_size += file_length
                path_segments = [
                    seg.decode('utf-8') if isinstance(seg, bytes) else seg 
                    for seg in file_entry['path']
                ]
                file_path = os.path.join(*path_segments)
                filesMetaData.append({
                    'path': file_path,
                    'length': file_length
                })
        else:
            total_size = info_dict['length']
            raw_name = info_dict['name']
            file_name = raw_name.decode('utf-8') if isinstance(raw_name, bytes) else raw_name
            filesMetaData.append({
                'path': file_name,
                'length': total_size
            })
        announceURL = metaInfo.get('announce', b'')
        if isinstance(announceURL, bytes):
            announceURL = announceURL.decode('utf-8')
        rDname = info_dict['name']
        display_name = rDname.decode('utf-8') if isinstance(rDname, bytes) else rDname
        return {
            'announce_url': announceURL,
            'info_hash': info_hash,               
            'info_hash_hex': info_hash.hex(),     
            'piece_length': info_dict['piece length'],
            'piece_hashes': pieceHash,       
            'total_size': total_size,        
            'files': filesMetaData,          
            'name': display_name,             
        }
 