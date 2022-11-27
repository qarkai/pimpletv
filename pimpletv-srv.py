#!/usr/bin/env python3

import os

import psycopg2

from pimpletv_parser import get_broadcasts, get_playlist_entry


DATABASE_URL = os.environ['DATABASE_URL']


def get_playlist() -> str:
    playlist = '#EXTM3U\n'
    broadcasts = get_broadcasts()

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    try: 
        with conn:
            with conn.cursor() as curs:
                curs.execute("DELETE FROM pimple WHERE query_ts < NOW() - INTERVAL '24 hours';")

                if not broadcasts:
                    curs.execute('SELECT m3u FROM pimple;')
                    m3us = curs.fetchall()
                    playlist += ''.join(m3u[0] for m3u in m3us)

                for b in broadcasts:
                    print(f'{b.teams}, {b.channel}, {"Live" if b.live else b.time}, {b.link}')
                    SQL = 'SELECT m3u FROM pimple WHERE link = %s;'
                    curs.execute(SQL, (b.link, ))
                    m3u = curs.fetchone()
                    if not m3u:
                        m3u = get_playlist_entry(b)
                        if not m3u:
                            continue
                        SQL = 'INSERT INTO pimple (link, m3u, query_ts) VALUES (%s, %s, NOW());'
                        curs.execute(SQL, (b.link, m3u))
                    else:
                        m3u = m3u[0]

                    playlist += m3u
    finally:
        conn.close()
    return playlist


def app(environ, start_response):
    query = environ['QUERY_STRING']
    if not query:
        query = '127.0.0.1:6878'

    playlist = get_playlist()
    data = playlist.replace('acestream://', f'http://{query}/ace/getstream?id=').encode()

    start_response("200 OK", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(data)))
    ])

    return iter([data])
