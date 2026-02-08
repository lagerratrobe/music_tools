#!/usr/bin/env python3
"""GnuDB lookup functions for CD metadata."""

import discid
import urllib.request


def lookup_gnudb(disc):
    """Query gnudb.org for CD metadata.
    
    Args:
        disc: discid.Disc object from discid.read()
        
    Returns:
        Raw CDDB record as string, or None if not found
    """
    # Step 1: Query to get category and disc ID
    offsets = [track.offset for track in disc.tracks]
    offset_str = "+".join(str(o) for o in offsets)
    total_seconds = disc.sectors // 75

    query_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+query+{disc.freedb_id}+{len(disc.tracks)}"
        f"+{offset_str}+{total_seconds}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )
    
    try:
        req = urllib.request.Request(query_url)
        with urllib.request.urlopen(req) as response:
            result = response.read().decode("utf-8")
        
        # DEBUG: Uncomment to see query details
        print(f"Query URL: {query_url}")
        print(f"Query response:\n{result}")
        print()
            
        lines = result.strip().split("\n")
        status_line = lines[1]
        
        # Check for no match
        if status_line.startswith("202"):
            # DEBUG: Uncomment to see no-match status
            print("Status: No match (202)")
            return None
            
        # Parse category and disc ID from response
        # Format: "200 category discid ..." or "211 ... \n category discid ..."
        if status_line.startswith("200"):
            parts = status_line.split()
            category = parts[0]
            gnudb_id = parts[1]
        elif status_line.startswith("211"):
            # Multiple matches - use first one
            parts = lines[1].split()
            category = parts[0]
            gnudb_id = parts[1]
        else:
            return None
            
    except Exception as e:
        print(f"Query failed: {e}")
        return None

    # Step 2: Read the full record
    read_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+read+{category}+{gnudb_id}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )
    
    try:
        req = urllib.request.Request(read_url)
        with urllib.request.urlopen(req) as response:
            result = response.read().decode("utf-8")
        return result
    except Exception as e:
        print(f"Read failed: {e}")
        return None


def parse_gnudb_record(record):
    """Parse CDDB-format record into structured metadata.
    
    Args:
        record: Raw CDDB record string from lookup_gnudb()
        
    Returns:
        Dict with keys: artist, album, year, genre, tracks
        tracks is a list of dicts with: number, title
        Returns None if parsing fails
    """
    if not record:
        return None
        
    lines = record.strip().split("\n")
    
    # Skip header lines (comments and status line)
    data_lines = [line for line in lines if not line.startswith("#") and line.strip() and line != "."]
    
    # Parse key=value pairs
    fields = {}
    for line in data_lines[1:]:  # Skip status line
        if "=" in line:
            key, _, value = line.partition("=")
            fields[key] = value
    
    # Extract album-level metadata
    dtitle = fields.get("DTITLE", "")
    if " / " in dtitle:
        artist, album = dtitle.split(" / ", 1)
    else:
        artist = dtitle
        album = dtitle
    
    metadata = {
        "artist": artist.strip(),
        "album": album.strip(),
        "year": fields.get("DYEAR", ""),
        "genre": fields.get("DGENRE", ""),
        "tracks": []
    }
    
    # Extract track titles
    track_keys = sorted([k for k in fields.keys() if k.startswith("TTITLE")])
    for key in track_keys:
        track_num = int(key[6:]) + 1  # TTITLE0 -> track 1
        metadata["tracks"].append({
            "number": track_num,
            "title": fields[key]
        })
    
    return metadata


def format_for_abcde(metadata):
    """Format metadata for ABCDE environment variables.
    
    Args:
        metadata: Dict from parse_gnudb_record()
        
    Returns:
        String with shell variable assignments
    """
    if not metadata:
        return ""
    
    output = []
    output.append(f"ARTIST='{metadata['artist']}'")
    output.append(f"ALBUM='{metadata['album']}'")
    
    if metadata['year']:
        output.append(f"YEAR='{metadata['year']}'")
    
    if metadata['genre']:
        output.append(f"GENRE='{metadata['genre']}'")
    
    output.append(f"TRACKS={len(metadata['tracks'])}")
    
    for track in metadata["tracks"]:
        output.append(f"TRACK{track['number']}='{track['title']}'")
    
    return "\n".join(output)


if __name__ == "__main__":
    # Test with CD in drive
    disc = discid.read("/dev/cdrom")
    
    print(f"Disc ID: {disc.id}")
    print(f"FreeDB ID: {disc.freedb_id}")
    print(f"Tracks: {len(disc.tracks)}")
    print()
    
    print("Looking up on gnudb.org...")
    record = lookup_gnudb(disc)
    
    if record:
        print("✓ Found")
        print()
        
        metadata = parse_gnudb_record(record)
        
        if metadata:
            print(f"Artist: {metadata['artist']}")
            print(f"Album:  {metadata['album']}")
            print(f"Year:   {metadata['year']}")
            print(f"Genre:  {metadata['genre']}")
            print(f"Tracks: {len(metadata['tracks'])}")
            print()
            
            print("Track listing:")
            for track in metadata["tracks"]:
                print(f"  {track['number']:2d}. {track['title']}")
            
            print()
            print("=" * 60)
            print("ABCDE format:")
            print("=" * 60)
            print(format_for_abcde(metadata))
    else:
        print("✗ Not found")