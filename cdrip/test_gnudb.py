#!/usr/bin/env python3
"""Test gnudb.org lookup - full read."""

import discid
import urllib.request

# Read disc
disc = discid.read("/dev/cdrom")

# Query first to get category and disc ID
offsets = [track.offset for track in disc.tracks]
offset_str = "+".join(str(o) for o in offsets)
total_seconds = disc.sectors // 75

query_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+query+{disc.freedb_id}+{len(disc.tracks)}"
        f"+{offset_str}+{total_seconds}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )
req = urllib.request.Request(query_url)
with urllib.request.urlopen(req) as response:
    result = response.read().decode("utf-8")
    print("Query response:")
    print(result)
    print()

lines = result.strip().split("\n")
parts = lines[1].split()
category = parts[0]
gnudb_id = parts[1]

# Now read the full record
read_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+read+{category}+{gnudb_id}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )
req = urllib.request.Request(read_url)
with urllib.request.urlopen(req) as response:
    result = response.read().decode("utf-8")
    print("Full record:")
    print(result)