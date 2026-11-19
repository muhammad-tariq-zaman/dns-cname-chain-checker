import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unittest
from main import load_records, check_chain

RECORDS = """www.example.com CNAME cdn.example.com
cdn.example.com CNAME edge.provider.net
edge.provider.net A 203.0.113.10
loop.example.com CNAME loop2.example.com
loop2.example.com CNAME loop.example.com
dangling.example.com CNAME gone.example.net
mail.example.com A 203.0.113.20
"""

class TestCnameChain(unittest.TestCase):
    def test_chain_resolves(self):
        records = load_records(RECORDS)
        status, chain, hops = check_chain(records, "www.example.com")
        self.assertEqual(status, "OK")
        self.assertEqual(chain, ["www.example.com", "cdn.example.com",
                                 "edge.provider.net", "203.0.113.10"])
        self.assertEqual(hops, 2)

    def test_loop_detected(self):
        records = load_records(RECORDS)
        status, chain, _ = check_chain(records, "loop.example.com")
        self.assertEqual(status, "LOOP")
        self.assertEqual(chain[-1], "loop.example.com")

    def test_dangling_detected(self):
        records = load_records(RECORDS)
        status, chain, _ = check_chain(records, "dangling.example.com")
        self.assertEqual((status, chain[-1]), ("DANGLING", "gone.example.net"))

    def test_too_long_chain(self):
        lines = [f"n{i}.example.com CNAME n{i + 1}.example.com" for i in range(12)]
        lines.append("n12.example.com A 203.0.113.1")
        records = load_records("\n".join(lines))
        status, _, hops = check_chain(records, "n0.example.com", max_hops=10)
        self.assertEqual(status, "TOO LONG")
        self.assertEqual(hops, 11)

    def test_exactly_max_hops_is_ok(self):
        lines = [f"n{i}.example.com CNAME n{i + 1}.example.com" for i in range(10)]
        lines.append("n10.example.com A 203.0.113.1")
        records = load_records("\n".join(lines))
        status, _, hops = check_chain(records, "n0.example.com", max_hops=10)
        self.assertEqual((status, hops), ("OK", 10))

    def test_direct_a_record(self):
        records = load_records(RECORDS)
        status, chain, hops = check_chain(records, "mail.example.com")
        self.assertEqual((status, chain, hops),
                         ("OK", ["mail.example.com", "203.0.113.20"], 0))

    def test_comments_and_blanks_ignored(self):
        records = load_records("# comment\n\na.example.com CNAME b.example.com\nb.example.com A 203.0.113.5\n")
        self.assertEqual(check_chain(records, "a.example.com")[0], "OK")

    def test_empty_records(self):
        self.assertEqual(load_records(""), {})
