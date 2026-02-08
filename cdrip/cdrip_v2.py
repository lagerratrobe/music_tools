#!/usr/bin/env python3
"""
cdrip - CD ripping tool with proper metadata lookup
"""

import discid
import urllib.request


def get_disc_id(device="/dev/cdrom"):
    """Read disc and return discid object with TOC info."""
    disc = discid.read(device)
    return disc


def print_disc_info(disc):
    """Display disc identification info."""
    print(f"Disc ID:      {disc.id}")
    print(f"FreeDB ID:    {disc.freedb_id}")
    print(f"Tracks:       {len(disc.tracks)}")
    print()


def lookup_gnudb(disc):
    """Two-step gnudb lookup: query to get category, then read full record.
    Returns raw record text, or None if not found."""

    # Build query params from disc TOC
    offsets = [track.offset for track in disc.tracks]
    offset_str = "+".join(str(o) for o in offsets)
    total_seconds = disc.sectors // 75

    # Step 1: query — returns category and gnudb disc ID
    query_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+query+{disc.freedb_id}+{len(disc.tracks)}"
        f"+{offset_str}+{total_seconds}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )

    with urllib.request.urlopen(urllib.request.Request(query_url)) as response:
        query_result = response.read().decode("utf-8")

    # Response status codes: 200=exact, 210=exact matches, 211=close matches
    status = query_result.split()[0]
    if status not in ("200", "210", "211"):
        print(f"gnudb query returned status {status}")
        return None

    # Parse category and disc ID from second line
    # Format: "210 Found exact matches...\ndata bd0f4f84 Artist - Album"
    lines = query_result.strip().split("\n")
    parts = lines[1].split()
    category = parts[0]
    gnudb_id = parts[1]

    # Step 2: read — returns full CDDB record
    read_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+read+{category}+{gnudb_id}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )

    with urllib.request.urlopen(urllib.request.Request(read_url)) as response:
        record = response.read().decode("utf-8")

    return record


def parse_gnudb_record(record):
    """Parse a CDDB-format record into a list of track dicts.

    Expected fields in the record:
        PERFORMER or ARTIST  — album-level artist
        ALBUM                — album title
        TTITLE=N             — track titles (0-indexed)
        YEAR                 — (optional) release year

    Returns list of dicts with keys: disc, number, title, artist, album
    """
    fields = {}
    for line in record.strip().split("\n"):
        if "=" in line:
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()

    # Artist: PERFORMER is preferred; fall back to ARTIST
    artist = fields.get("PERFORMER") or fields.get("ARTIST", "Unknown Artist")
    album = fields.get("ALBUM", "Unknown Album")

    # Collect TTITLE entries (0-indexed in the record)
    track_titles = {}
    for key, value in fields.items():
        if key.startswith("TTITLE"):
            num = int(key.split("=")[0].replace("TTITLE", "") or key[6:])
            track_titles[num] = value

    tracks = []
    for i in sorted(track_titles):
        # Per-track artist: some CDDB records have "Track Artist - Title"
        title = track_titles[i]
        track_artist = artist
        if " - " in title:
            parts = title.split(" - ", 1)
            # Only treat as artist-title split if the first part looks like
            # a different artist (not a subtitle or part number)
            if parts[0] != artist and not parts[0].startswith("Part"):
                track_artist = parts[0]
                title = parts[1]

        tracks.append({
            "disc": 1,
            "number": i + 1,          # CDDB is 0-indexed, we want 1-indexed
            "title": title,
            "artist": track_artist,
            "album": album,
        })

    return tracks


def print_tracks(tracks):
    """Display track listing."""
    print("Track listing:")
    for t in tracks:
        print(f"  {t['number']:02d} - {t['title']}")


if __name__ == "__main__":
    disc = get_disc_id()
    print_disc_info(disc)

    record = lookup_gnudb(disc)
    if record:
        tracks = parse_gnudb_record(record)
        print_tracks(tracks)
    else:
        print("No gnudb match found")