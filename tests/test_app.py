import json
import os
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["QA_MOCK"] = "1"

import app  # noqa: E402
from qa import bm25, core  # noqa: E402
from qa.citations import check_citations  # noqa: E402

CHUNKS = core.load_chunks()


class Basics(unittest.TestCase):
    def test_labels_unique_and_nonempty(self):
        labels = [c["nhan"] for c in CHUNKS]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertTrue(all(c["noi_dung"].strip() for c in CHUNKS))

    def test_citation_check(self):
        r = check_citations("a [TT148/2018 | Điều 4 | Khoản 1] b [TT148/2018 | Điều 99 | Khoản 1] "
                            "c [TT148/2018 | Điều 4 | Khoản 1]", CHUNKS)
        self.assertEqual([x["exists"] for x in r], [True, False])

    def test_bm25_finds_age(self):
        top = [c["nhan"] for c in bm25.retrieve("độ tuổi gọi nhập ngũ", CHUNKS)]
        self.assertTrue(any("Điều 30" in l or "Điều 4 | Khoản 1" in l for l in top), top)

    def test_prompt_has_all_labels(self):
        text = core.format_chunks(CHUNKS)
        self.assertTrue(all(f"[{c['nhan']}]" in text for c in CHUNKS))


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def post(self, body, raw=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/ask",
                                     data=raw if raw is not None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_ok_flags_bad_citation(self):
        s, d = self.post({"question": "Độ tuổi nhập ngũ?", "mode": "long_context"})
        self.assertTrue(d["ok"])
        ex = {c["label"]: c["exists"] for c in d["result"]["citations"]}
        self.assertTrue(ex["TT148/2018 | Điều 4 | Khoản 1"])
        self.assertFalse(ex["TT148/2018 | Điều 99 | Khoản 1"])
        self.assertIn("seconds", d["result"])

    def test_refusal(self):
        s, d = self.post({"question": "Thủ đô của Pháp là gì?", "mode": "bm25"})
        self.assertTrue(d["result"]["refused"])

    def test_validation(self):
        self.assertEqual(self.post({"question": "  ", "mode": "bm25"})[0], 400)
        self.assertEqual(self.post({"question": "x", "mode": "zzz"})[0], 400)
        self.assertEqual(self.post(None, raw=b"not json")[0], 400)

    def test_api_failure_is_friendly(self):
        for mode, code in [("rate_limit", "rate_limit"), ("auth", "auth"), ("timeout", "network")]:
            os.environ["QA_MOCK"] = mode
            s, d = self.post({"question": "x", "mode": "long_context"})
            self.assertEqual((s, d["ok"], d["error"]["code"]), (200, False, code))
        os.environ["QA_MOCK"] = "1"

    def test_chunk_lookup(self):
        url = f"http://127.0.0.1:{self.port}/api/chunk?label=" + urllib.parse.quote("TT148/2018 | Điều 4 | Khoản 1")
        with urllib.request.urlopen(url) as r:
            self.assertIn("18 tuổi", json.loads(r.read())["chunk"]["noi_dung"])


if __name__ == "__main__":
    unittest.main()
