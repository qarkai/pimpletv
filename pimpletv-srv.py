#!/usr/bin/env python3

from pimpletv_parser import get_broadcasts, get_playlist_entry


def get_playlist() -> str:
    playlist = '#EXTM3U\n'

    broadcasts = get_broadcasts()
    for b in broadcasts:
        print(f'{b.teams}, {b.channel}, {"Live" if b.live else b.time}, {b.link}')
        m3u = get_playlist_entry(b)
        if m3u:
            playlist += m3u

    return playlist


def app(environ, start_response):
    if environ['PATH_INFO'] == '/test':
        start_response("200 OK", [])
        return iter([b""])

    query = environ['QUERY_STRING']
    if not query:
        query = '127.0.0.1:6878'

    playlist = get_playlist()
    data = playlist.replace('acestream://', f'http://{query}/ace/getstream?id=').encode()

    start_response("200 OK", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(data))),
    ])

    return iter([data])
