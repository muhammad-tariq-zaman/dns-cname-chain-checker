"""Follow CNAME chains in a DNS records file and flag problems.

Usage: python3 main.py records.txt [--max-hops 10]
records.txt lines are "name TYPE value", e.g. "www.example.com
CNAME cdn.example.com" or "edge.provider.net A 203.0.113.10".
"#" lines and blank lines are ignored. Every name with a CNAME
record is checked by following the chain:
- OK: the chain ends at an A record.
- LOOP: the chain returns to a name already visited.
- DANGLING: the chain ends at a name with no record at all.
- TOO LONG: the chain needs more than --max-hops CNAME hops.
"""
import argparse, sys

def load_records(text):
    records = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        name, rtype, value = parts[0], parts[1].upper(), parts[2]
        records.setdefault(name, []).append((rtype, value))
    return records

def check_chain(records, start, max_hops=10):
    chain = [start]
    current = start
    seen = {start}
    hops = 0
    while True:
        entries = records.get(current, [])
        cname = next((v for t, v in entries if t == "CNAME"), None)
        if cname is None:
            a_record = next((v for t, v in entries if t == "A"), None)
            if a_record is not None:
                chain.append(a_record)
                return ("OK", chain, hops)
            return ("DANGLING", chain, hops)
        hops += 1
        if hops > max_hops:
            chain.append(cname)
            return ("TOO LONG", chain, hops)
        if cname in seen:
            chain.append(cname)
            return ("LOOP", chain, hops)
        seen.add(cname)
        chain.append(cname)
        current = cname

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--max-hops", type=int, default=10)
    args = parser.parse_args(argv)
    with open(args.path, encoding="utf-8") as f:
        records = load_records(f.read())
    starts = sorted(name for name, entries in records.items()
                    if any(t == "CNAME" for t, _ in entries))
    results = [(start, *check_chain(records, start, args.max_hops)) for start in starts]
    for start, status, chain, hops in results:
        joined = " -> ".join(chain)
        if status == "OK":
            print(f"{start}: OK - {joined} ({hops} CNAME hop(s))")
        elif status == "LOOP":
            print(f"{start}: LOOP - {joined} (cycle detected)")
        elif status == "DANGLING":
            print(f"{start}: DANGLING - {joined} (target has no record)")
        else:
            print(f"{start}: TOO LONG - {joined} (over {args.max_hops} hops)")
    counts = {s: sum(1 for _, status, _, _ in results if status == s)
              for s in ("OK", "LOOP", "DANGLING", "TOO LONG")}
    print(f"{len(results)} CNAME chain(s) checked: {counts['OK']} ok, "
          f"{counts['LOOP']} loop, {counts['DANGLING']} dangling, "
          f"{counts['TOO LONG']} too long.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
