"""Tests for net.download: what is saved when the server labels a file gzip. The server is replaced by a stand-in
response, so nothing here touches the network."""
import gzip, io, os, shutil, tempfile, unittest
from unittest import mock

from mtgcommander import net

TEXT = b'{"variants": [1, 2, 3]}\n' * 50


class FakeResponse:
    """What urllib.request.urlopen hands back: headers and a body to read in pieces."""

    def __init__(self, body, headers):
        self.body, self.headers = io.BytesIO(body), headers

    def read(self, size=-1):
        return self.body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "saved")
        mock.patch.object(net, "_pace").start()
        self.addCleanup(mock.patch.stopall)

    def download(self, body, headers, **kw):
        with mock.patch.object(net.urllib.request, "urlopen", return_value=FakeResponse(body, headers)):
            net.download("https://example.com/file", self.path, source="test", **kw)
        with open(self.path, "rb") as f:
            return f.read()

    def test_a_file_labelled_gzip_is_unzipped_as_it_arrives(self):
        saved = self.download(gzip.compress(TEXT), {"Content-Encoding": "gzip"})
        self.assertEqual(saved, TEXT)

    def test_with_decode_off_the_bytes_are_saved_as_sent(self):
        # Commander Spellbook's file is a 29 MB gzip labelled Content-Encoding: gzip; unzipped it is 687 MB
        sent = gzip.compress(TEXT)
        saved = self.download(sent, {"Content-Encoding": "gzip"}, decode=False)
        self.assertEqual(saved, sent)
        self.assertEqual(gzip.decompress(saved), TEXT)

    def test_a_file_with_no_label_is_saved_as_it_is_either_way(self):
        for decode in (True, False):
            with self.subTest(decode=decode):
                self.assertEqual(self.download(TEXT, {}, decode=decode), TEXT)

    def test_a_gzip_without_the_label_is_saved_untouched_by_default(self):
        # Scryfall's CDN serves application/gzip without Content-Encoding: the saved file is the gzip itself
        sent = gzip.compress(TEXT)
        self.assertEqual(self.download(sent, {"Content-Type": "application/gzip"}), sent)

    def test_the_temporary_file_does_not_stay_behind(self):
        self.download(gzip.compress(TEXT), {"Content-Encoding": "gzip"}, decode=False)
        self.assertEqual(os.listdir(self.tmp), ["saved"])


if __name__ == "__main__":
    unittest.main()
