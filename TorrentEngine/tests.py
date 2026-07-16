from django.test import TestCase
from .utils.bencode import bencode, bdecode, BenCodeError
from .utils.tracker import UDPTrackerClient

class BencodeTestCase(TestCase):
    def test_decode_integer(self):
        self.assertEqual(bdecode(b'i42e'), 42)
        self.assertEqual(bdecode(b'i-100e'), -100)

    def test_decode_bytes(self):
        self.assertEqual(bdecode(b'4:spam'), b'spam')
        self.assertEqual(bdecode(b'0:'), b'')

    def test_decode_list(self):
        self.assertEqual(bdecode(b'li42e4:spame'), [42, b'spam'])

    def test_decode_dict(self):
        self.assertEqual(bdecode(b'd3:bar4:spam3:fooi42ee'), {
            'bar': b'spam',
            'foo': 42
        })

    def test_invalid_bencode(self):
        with self.assertRaises(BenCodeError):
            bdecode(b'i42')
        with self.assertRaises(BenCodeError):
            bdecode(b'l')

class TrackerTestCase(TestCase):
    def test_invalid_announce_url(self):
        with self.assertRaises(ValueError):
            UDPTrackerClient.get_peers("ftp://example.com/announce", b'a'*20, 100)
        with self.assertRaises(ValueError):
            UDPTrackerClient.get_peers("udp://", b'a'*20, 100)
        with self.assertRaises(ValueError):
            UDPTrackerClient.get_peers("http://", b'a'*20, 100)
        with self.assertRaises(ConnectionError):
            UDPTrackerClient.get_peers("http://example.com/announce", b'a'*20, 100)

class TorrentMetaDataServiceTestCase(TestCase):
    def test_parse_torrent_file(self):
        from .services import TorrentMetaDataService
        meta_dict = {
            'announce': b'udp://tracker.coppersurfer.tk:6969/announce',
            'info': {
                'name': b'test_file.txt',
                'piece length': 16384,
                'pieces': b'a'*20,
                'length': 100
            }
        }
        encoded = bencode(meta_dict)
        parsed = TorrentMetaDataService.parse_torrent_file(encoded)
        self.assertEqual(parsed['name'], 'test_file.txt')
        self.assertEqual(parsed['piece_length'], 16384)
        self.assertEqual(parsed['total_size'], 100)
        self.assertEqual(parsed['announce_url'], 'udp://tracker.coppersurfer.tk:6969/announce')


