#!/usr/bin/env python3

import html
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

PIMPLETV_URL = 'https://www.pimpletv.ru/'

MSK = ZoneInfo('Europe/Moscow')


class Broadcast:
    def __init__(self):
        self.link = None
        self.home_team = None
        self.away_team = None
        self.channel = None
        self.time = None
        self.live = False

    @property
    def teams(self) -> str:
        return f'{self.home_team} – {self.away_team}'

    def is_suitable(self) -> bool:
        if self.live:
            return True

        now_time = datetime.now(tz=MSK)
        start_time = now_time + timedelta(minutes=30)

        b_start_time = datetime.combine(now_time.date(), datetime.strptime(self.time, '%H:%M').time(), now_time.tzinfo)
        b_end_time = b_start_time + timedelta(hours=3)
        # print(f'b_time: {b_time}, b_start_time: {b_start_time}, b_end_time: {b_end_time}, now_time: {now_time}, start_time: {start_time}')
        # print(f'{b_end_time} >= {now_time} and {b_start_time} <= {start_time}')
        return b_end_time >= now_time and b_start_time <= start_time

    def to_m3u(self, acestream_id: str) -> str:
        channel_id = get_ssiptv_channel_id(self.channel)
        return f'#EXTINF:-1 type="stream" channelId="{channel_id}", {self.time} {self.teams} ({self.channel})\n{acestream_id}\n'


def load_page(path: str):
    try:
        with urllib.request.urlopen(f'{PIMPLETV_URL}/{path}') as f:
            return html.unescape(f.read().decode('utf-8'))
    except urllib.error.HTTPError:
        return ''


def get_acestream_ids(html_text: str):
    return re.findall('(acestream://.{40})', html_text)


def get_broadcast_time(html_text: str):
    # <div class="match-info__date" itemprop="startDate" content="2022-10-08T14:00:00+03:00"> 8 октября 2022, 14:00</div>
    return re.findall('<div class="match-info__date" itemprop="startDate".*, (.*)</div>', html_text)


def get_ssiptv_channel_id(channel: str) -> int:
    known_channels = {
        'МАТЧ! HD': 4,
        'МАТЧ! СТРАНА HD': 84,
        'МАТЧ ПРЕМЬЕР HD': 277,
        'Беларусь 2 HD': 346,
        'МАТЧ! Футбол 1 (HD)': 553,
        'МАТЧ! Футбол 2 (HD)': 554,
        'МАТЧ! ИГРА (HD)': 569,
        'Setanta Sports HD': 665,
        'Футбол HD': 919,
        'Беларусь 5 HD': 1511,
        'Sky Sport 1 HD': 1640,
        'МАТЧ! Футбол 3 (HD)': 2831,
        'CANAL+ Sport 2 HD': 3193,
        'Eleven Sports 2 HD': 4620,
        'Setanta Qazaqstan HD': 4841,
        'Setanta Sports 1 HD': 4848,
        'Setanta Sports 2 HD': 4849,
    }

    try:
        return known_channels[channel]
    except KeyError:
        print(f'Unknown channel {channel}')

    return -1


def get_value(line: str, pattern: re.Pattern):
    result = pattern.search(line)
    return result.group(1) if result else None


def parse_today_links(fh):
    link_re = re.compile(r'(/football/\d+[^/]*/)')
    home_team_re = re.compile('<span class="table-item__home-name">([^<]*)</span>')
    away_team_re = re.compile('<span class="table-item__away-name">(.*)</span>')
    channel_re = re.compile('<div class="match-item__logo-channel">(.*)</div>')
    time_re = re.compile(r'<div>(\d{2}:\d{2})</div>')
    live_str = '<div class="match-item__title-date liveTime">'
    finished_str = '<div>Завершен</div>'

    broadcasts = []
    b = None

    for line in fh:
        if line.find('streams-day') != -1:
            break

        if line.find('class="match-item _rates"') != -1:
            b = Broadcast()
            is_finished = False

        if b is None:
            continue

        if b.link is None:
            b.link = get_value(line, link_re)
        if b.home_team is None:
            b.home_team = get_value(line, home_team_re)
        if b.away_team is None:
            b.away_team = get_value(line, away_team_re)
        if b.channel is None:
            b.channel = get_value(line, channel_re)
        if b.time is None:
            b.time = get_value(line, time_re)
        if not b.live:
            b.live = live_str in line
        if not is_finished:
            is_finished = finished_str in line

        if b.channel is not None:  # last meaningful line was parsed
            if not is_finished and b.is_suitable():
                broadcasts.append(b)
            b = None

    return broadcasts


def parse_broadcast_links(html_text: str) -> list:
    today = datetime.now(tz=MSK) - timedelta(hours=3)
    streams_today_pattern = re.compile(f'<div class="streams-day">({today.day}.*)')
    # print(today)
    lines = iter(html_text.splitlines())
    for line in lines:
        # print(f'line: {line}')
        if get_value(line, streams_today_pattern):
            return parse_today_links(lines)
    return []


def get_broadcasts() -> list:
    page = load_page('/category/football/')
    return parse_broadcast_links(page)


def get_playlist_entry(b: Broadcast) -> str:
    page = load_page(b.link)
    acestream_ids = get_acestream_ids(page)
    if not acestream_ids:
        return None

    if b.live:
        b.time = get_broadcast_time(page)[0]
    
    return b.to_m3u(acestream_ids[0])


def load_playlist() -> str:
    broadcasts = get_broadcasts()
    # print(len(broadcasts))

    with StringIO() as fh:
        fh.write('#EXTM3U\n')

        for b in broadcasts:
            print(f'{b.teams}, {b.channel}, {"Live" if b.live else b.time}, {b.link}')

            m3u = get_playlist_entry(b)
            if not m3u:
                continue

            fh.write(m3u)

        playlist = fh.getvalue()

    return playlist


if __name__ == '__main__':
    load_playlist()
