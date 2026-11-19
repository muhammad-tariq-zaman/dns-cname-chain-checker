# dns-cname-chain-checker

Follow CNAME chains in a DNS records file and flag problems: each line is "name TYPE value" — every name with a CNAME record is checked by following the chain to OK (ends at an A record), LOOP (returns to a name already visited), DANGLING (ends at a name with no record at all), or TOO LONG (needs more than --max-hops CNAME hops, default 10).

Sample input is included (sample.txt with seven DNS records).

## How to run

```sh
python3 main.py sample.txt
```

## Example output

```
cdn.example.com: OK - cdn.example.com -> edge.provider.net -> 203.0.113.10 (1 CNAME hop(s))
dangling.example.com: DANGLING - dangling.example.com -> gone.example.net (target has no record)
loop.example.com: LOOP - loop.example.com -> loop2.example.com -> loop.example.com (cycle detected)
loop2.example.com: LOOP - loop2.example.com -> loop.example.com -> loop2.example.com (cycle detected)
www.example.com: OK - www.example.com -> cdn.example.com -> edge.provider.net -> 203.0.113.10 (2 CNAME hop(s))
5 CNAME chain(s) checked: 2 ok, 2 loop, 1 dangling, 0 too long.
```

Standard library only. Run the tests with `python3 -m unittest discover`.
