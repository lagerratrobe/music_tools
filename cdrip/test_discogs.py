#!/usr/bin/env python3
"""Test MusicBrainz artist tags."""

import musicbrainzngs

musicbrainzngs.set_useragent("cdrip", "0.1", "randre@gmail.com")

disc_id = "ut.9jeFzCNpYNGV4jNFsbG9L0Do-"

result = musicbrainzngs.get_releases_by_discid(
    disc_id,
    includes=["artists", "recordings"])

release = result["disc"]["release-list"][0]
artist_id = release["artist-credit"][0]["artist"]["id"]
artist_name = release["artist-credit-phrase"]

print(f"Artist: {artist_name}")
print(f"Artist ID: {artist_id}")
print()

# Now fetch the artist with tags
artist_data = musicbrainzngs.get_artist_by_id(
    artist_id,
    includes=["tags"])

print("Artist tags:")
if "tag-list" in artist_data["artist"]:
    for tag in sorted(artist_data["artist"]["tag-list"], key=lambda x: int(x["count"]), reverse=True):
        print(f"  {tag['name']} (count: {tag['count']})")
else:
    print("  None")