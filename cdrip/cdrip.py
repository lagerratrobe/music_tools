#!/usr/bin/env python3
"""
cdrip - CD ripping tool with proper metadata lookup
"""

import discid
import musicbrainzngs
import os
import discogs_client


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


def lookup_musicbrainz(disc):
    """Query MusicBrainz with disc ID, return release info."""
    musicbrainzngs.set_useragent("cdrip", "0.1", "randre@gmail.com")
    
    result = musicbrainzngs.get_releases_by_discid(
        disc.id,
        includes=["artists", "recordings"])
    
    if "disc" in result:
        releases = result["disc"]["release-list"]
    elif "cdstub" in result:
        print("Found a CD stub (unverified entry)")
        return None
    else:
        return None
    return releases


def print_releases(releases):
    """Display list of matching releases."""
    print(f"Found {len(releases)} release(s):")

    for i, release in enumerate(releases, 1):
        artist = release["artist-credit-phrase"]
        title = release["title"]
        print(f"  {i}. {artist} - {title}")
    print()


def get_tracks_from_release(release):
    """Extract track list from a MusicBrainz release."""
    tracks = []
    for medium in release["medium-list"]:
        disc_num = medium["position"]
        for track in medium["track-list"]:
            tracks.append({
                "disc": disc_num,
                "number": int(track["position"]),
                "title": track["recording"]["title"],
                "artist": release["artist-credit-phrase"],
                "album": release["title"],
            })
    return tracks


def lookup_discogs(artist, album):
    """Query Discogs for genre and cover art."""
    with open(os.path.expanduser("~/.discogs_token")) as f:
        token = f.read().strip()
    
    client = discogs_client.Client("cdrip/0.1", user_token=token)
    
    # Try full search first
    query = f"{artist} {album}"
    results = client.search(query=query, type="release")
    
    # If no results, try just artist + first word of album
    if not results:
        first_word = album.split()[0]
        query = f"{artist} {first_word}"
        results = client.search(query=query, type="release")
    
    if not results:
        return None
    
    release = results[0]
    return {
        "genre": release.genres[0] if release.genres else None,
        "style": release.styles[0] if release.styles else None,
        "year": release.year,
        "cover_url": release.images[0]["uri"] if release.images else None}


def print_discogs_info(discogs_info):
    """Display Discogs metadata."""
    print("Discogs lookup...")
    if discogs_info:
        print(f"  Genre: {discogs_info['genre']}")
        print(f"  Style: {discogs_info['style']}")
        print(f"  Year:  {discogs_info['year']}")
        print(f"  Cover: {discogs_info['cover_url']}")
    else:
        print("  No Discogs match found")


def print_tracks(tracks):
    """Display track listing."""
    print("Track listing:")
    for t in tracks:
        print(f"  {t['number']:02d} - {t['title']}")


if __name__ == "__main__":
    disc = get_disc_id()
    print_disc_info(disc)

    releases = lookup_musicbrainz(disc)
    print_releases(releases)

    tracks = get_tracks_from_release(releases[0])
    #print_tracks(tracks)

    artist = releases[0]["artist-credit-phrase"]
    album = releases[0]["title"]
    discogs_info = lookup_discogs(artist, album)
    print_discogs_info(discogs_info)
