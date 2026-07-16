from django.shortcuts import render
import os
from django.http import JsonResponse
from django.conf import settings
from .services import TorrentMetaDataService
from .utils.downloader import TorrentDownloader

def index(request):
    if request.method == 'POST' and request.FILES.get('torrentFile'):
        torrentFile = request.FILES['torrentFile']
        try:
            fileContent = torrentFile.read()
            metadata = TorrentMetaDataService.parse_torrent_file(fileContent)
            
            request.session['active_metadata'] = {
                'announce_url': metadata['announce_url'],
                'info_hash_hex': metadata['info_hash_hex'],
                'info_hash_bin_hex': metadata['info_hash'].hex(),
                'piece_length': metadata['piece_length'],
                'total_size': metadata['total_size'],
                'name': metadata['name'],
                'files': metadata['files']
            }
            
            return render(request, 'TorrentEngine/index.html', {'metadata': metadata})
        except Exception as e:
            return render(request, 'TorrentEngine/index.html', {'error': str(e)})

    return render(request, 'TorrentEngine/index.html')

def startDownload(request):
    if request.method == 'POST':
        metadataSession = request.session.get('active_metadata')
        if not metadataSession:
            return JsonResponse({'status': 'error', 'message': 'No active torrent metadata found'})

        metadata = {
            'announce_url': metadataSession['announce_url'],
            'info_hash': bytes.fromhex(metadataSession['info_hash_bin_hex']),
            'piece_length': metadataSession['piece_length'],
            'piece_hashes': [bytes.fromhex(metadataSession['info_hash_bin_hex'])], 
            'total_size': metadataSession['total_size'],
            'name': metadataSession['name'],
            'files': metadataSession['files']
        }

        downloadDir = os.path.join(settings.BASE_DIR, 'downloads')
        try:
            downloader = TorrentDownloader(metadata, downloadDir)
            downloader.start()
            return JsonResponse({'status': 'success', 'message': 'Download completed successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)