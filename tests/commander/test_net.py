"""Tests for net.download (what is saved when the server labels a file gzip), the count of requests the deck server shows
as progress, the MTG_FAIL_HOSTS test switch, and the temporary file names a cache write uses. The server is replaced by
a stand-in response, so nothing here touches the network."""
import gzip, io, json, os, shutil, tempfile, threading, unittest
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


class RequestCountTests(unittest.TestCase):
    def setUp(self):
        mock.patch.object(net, "_pace").start()
        self.addCleanup(mock.patch.stopall)
        self.start = net.STATS["requests"]

    def request(self, url="https://example.com/page", **kw):
        with mock.patch.object(net.urllib.request, "urlopen", return_value=FakeResponse(b"{}", {})):
            return net.request(url, source="test", **kw)

    def test_each_request_adds_one_to_the_count(self):
        # three pages fetched: the deck server shows "3 requests" while a deck is being prepared
        for _ in range(3):
            self.request()
        self.assertEqual(net.STATS["requests"] - self.start, 3)

    def test_a_request_that_fails_still_counts(self):
        # a request is a request, whether the site answered or not
        with mock.patch.object(net.urllib.request, "urlopen", side_effect=net.urllib.error.URLError("down")), \
                mock.patch.object(net.time, "sleep"):
            with self.assertRaises(net.FetchError):
                net.request("https://example.com/page", source="test")
        self.assertEqual(net.STATS["requests"] - self.start, 1)      # the retries inside one call are not extra requests

    def test_a_cache_hit_makes_no_request_and_does_not_count(self):
        # fetch_json serves a fresh copy from disk
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with mock.patch.object(net, "CACHE", tmp):
            self.request()
            net.atomic_json(net.cache_file("test", "page"), {"fetched": net.time.time(), "url": "u", "payload": {"a": 1}})
            before = net.STATS["requests"]
            payload, info = net.fetch_json("https://example.com/page", source="test", key="page", ttl=3600)
        self.assertEqual((payload, info["cache"], net.STATS["requests"] - before), ({"a": 1}, "fresh", 0))


class FailingHostsTests(unittest.TestCase):
    """MTG_FAIL_HOSTS: a test switch that makes the named sites fail at once, as if they were down."""

    def setUp(self):
        mock.patch.object(net, "_pace").start()
        self.addCleanup(mock.patch.stopall)
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.urlopen = mock.patch.object(net.urllib.request, "urlopen", return_value=FakeResponse(b"{}", {})).start()

    def test_it_is_off_unless_the_variable_is_set(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MTG_FAIL_HOSTS", None)
            self.assertEqual(net.failing_hosts(), set())
            self.assertEqual(net.request("https://json.edhrec.com/x", source="edhrec"), b"{}")

    def test_hosts_are_comma_separated_trimmed_and_not_case_sensitive(self):
        with mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": " JSON.edhrec.com ,edhtop16.com,, "}):
            self.assertEqual(net.failing_hosts(), {"json.edhrec.com", "edhtop16.com"})

    def test_a_request_to_a_named_host_fails_at_once_without_touching_the_network(self):
        # EDHREC is "down": FetchError naming the host and the switch; the site was never asked
        with mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.edhrec.com"}):
            with self.assertRaises(net.FetchError) as caught:
                net.request("https://json.edhrec.com/pages/commanders/hazel.json", source="edhrec")
        self.assertEqual(caught.exception.source, "edhrec")
        self.assertIn("MTG_FAIL_HOSTS", caught.exception.reason)
        self.urlopen.assert_not_called()

    def test_other_hosts_are_not_affected(self):
        with mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.edhrec.com"}):
            self.assertEqual(net.request("https://api.scryfall.com/cards/search", source="scryfall"), b"{}")

    def test_a_download_from_a_named_host_fails_too(self):
        # the combo file and the card index are sources as well
        with mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.commanderspellbook.com"}):
            with self.assertRaises(net.FetchError):
                net.download("https://json.commanderspellbook.com/variants.json.gz", os.path.join(self.tmp, "v"),
                             source="spellbook")
        self.assertEqual(os.listdir(self.tmp), [])
        self.urlopen.assert_not_called()

    def test_with_the_switch_and_a_refresh_the_cached_copy_is_served_as_stale(self):
        # --refresh skips the fresh cache, the site fails, and the old copy answers: the page shows its stale banner
        with mock.patch.object(net, "CACHE", self.tmp), mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.edhrec.com"}):
            net.atomic_json(net.cache_file("edhrec", "page"), {"fetched": net.time.time() - 60, "url": "u",
                                                               "payload": {"decks": 1125}})
            payload, info = net.fetch_json("https://json.edhrec.com/page.json", source="edhrec", key="page", refresh=True)
        self.assertEqual((payload, info["cache"]), ({"decks": 1125}, "stale"))

    def test_with_the_switch_and_nothing_cached_the_error_reaches_the_caller(self):
        with mock.patch.object(net, "CACHE", self.tmp), mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.edhrec.com"}):
            with self.assertRaises(net.FetchError):
                net.fetch_json("https://json.edhrec.com/page.json", source="edhrec", key="page", refresh=True)


class AtomicWriteTests(unittest.TestCase):
    def test_two_threads_writing_one_cache_file_never_share_a_temporary_file(self):
        # the deck server can save the same cache file from two requests at once; a shared temp file would interleave
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "x", "cache.json")
        seen, gate = [], threading.Barrier(2)
        real_replace = os.replace

        def replace(src, dst):
            seen.append(src)
            real_replace(src, dst)

        def write(value):
            gate.wait()
            net.atomic_json(path, {"value": value})
        with mock.patch.object(net.os, "replace", replace):
            threads = [threading.Thread(target=write, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        self.assertEqual(len(set(seen)), 2)
        for name in seen:
            self.assertTrue(name.startswith(path + "." + str(os.getpid()) + "."))
        with open(path) as f:
            self.assertIn(json.load(f)["value"], (0, 1))
        self.assertEqual(os.listdir(os.path.dirname(path)), ["cache.json"])


if __name__ == "__main__":
    unittest.main()
