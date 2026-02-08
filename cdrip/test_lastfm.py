#!/usr/bin/env python3
"""Test Last.fm API for genre/tags."""

import os
import urllib.request
import urllib.parse
import json

with open(os.path.expanduser("~/.lastfm_token")) as f:
    api_key = f.read().strip()

# Test albums from your CDs
albums = [
    ("Harry Connick, Jr.", "Occasion"),
    ("The Strokes", "Is This It"),
    ("Primitive Radio Gods", "Rocket"),
    ("Nine Black Alps", "Everything Is"),
    ("The Crystal Method", "Vegas"),
    ("Duran Duran", "Paper Gods"),
    ("Lenny Kravitz", "Greatest Hits"),
]

for artist, album in albums:
    url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={api_key}&artist={urllib.parse.quote(artist)}&album={urllib.parse.quote(album)}&format=json"
    
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    print(f"{artist} - {album}")
    
    if "error" in data:
        print(f"  Error: {data['message']}")
    elif "album" in data:
        tags = data["album"].get("tags", {}).get("tag", [])
        if tags:
            tag_names = [t["name"] for t in tags[:3]]
            print(f"  Tags: {', '.join(tag_names)}")
        else:
            print("  Tags: None")
    print()