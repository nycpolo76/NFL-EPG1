"""Build a compatible NFL event XMLTV overlay with verified final scores."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import gzip
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = 'https://github.com/ferteque/Curated-M3U-Repository/raw/refs/heads/main/epg6.xml.gz'
SCORES = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
UTC = timezone.utc

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'PersonalNFLEPG/1.0'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read(60_000_001)
    if len(data) > 60_000_000:
        raise ValueError('Download exceeds limit')
    return data

def stamp(value):
    return datetime.strptime(value, '%Y%m%d%H%M%S %z').astimezone(UTC)

def transform(root, events, now):
    # These event IDs are the IDs already assigned in the supplied guide.
    ids = {p.get('channel') for p in root.findall('programme')
           if re.fullmatch(r'teamarr-event-\d+', p.get('channel', ''))
           and any('nfl' in (c.text or '').lower() for c in p.findall('category'))}
    if not ids:
        raise ValueError('No NFL event channels found; refusing to replace guide')
    out = ET.Element('tv', {'generator-info-name': 'NFL Final Scores'})
    for c in root.findall('channel'):
        if c.get('id') in ids:
            out.append(copy.deepcopy(c))
    changed = 0
    for original in root.findall('programme'):
        cid = original.get('channel')
        if cid not in ids:
            continue
        p = copy.deepcopy(original)
        event = events.get(cid.removeprefix('teamarr-event-'))
        title = p.find('title')
        # Only amend the postgame blocks; retain the original kickoff listings.
        if title is not None and (title.text or '').strip().upper().startswith('FINAL'):
            status = (event or {}).get('status', {}).get('type', {})
            if status.get('completed') is True and status.get('name') == 'STATUS_FINAL':
                competitors = event['competitions'][0]['competitors']
                sides = {c['homeAway']: c for c in competitors}
                away, home = sides['away'], sides['home']
                scores = [str(c.get('score', '')) for c in (away, home)]
                if not all(re.fullmatch(r'\d+', s) for s in scores):
                    raise ValueError('Final event has invalid scores')
                title.text = (f"FINAL: {away['team']['shortDisplayName']} {scores[0]} – "
                              f"{home['team']['shortDisplayName']} {scores[1]}")
                desc = p.find('desc')
                if desc is None:
                    desc = ET.SubElement(p, 'desc', {'lang': 'en'})
                desc.text = (f"{away['team']['displayName']} {scores[0]}, "
                             f"{home['team']['displayName']} {scores[1]}. Final. "
                             f"Score checked {now.strftime('%Y-%m-%d %H:%M UTC')}.")
                for live in p.findall('live'):
                    p.remove(live)
                changed += 1
            else:
                # A scheduled stop is not evidence that the game has ended.
                title.text = 'Game in progress — final pending' if status.get('state') == 'in' else 'Final score pending'
        out.append(p)
    return out, changed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file')
    parser.add_argument('--output', default='scores-output')
    args = parser.parse_args()
    data = Path(args.source_file).read_bytes() if args.source_file else fetch(SOURCE)
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    root = ET.fromstring(data)
    now = datetime.now(UTC)
    # Daily requests: the score service does not accept date ranges.
    dates = [(now+timedelta(days=offset)).strftime('%Y%m%d') for offset in range(-3, 2)]
    def scoreboard(date):
        payload = json.loads(fetch(SCORES + '?dates=' + date))
        if not isinstance(payload.get('events'), list):
            raise ValueError('Invalid scoreboard response; preserving previous output')
        return payload['events']
    with ThreadPoolExecutor(max_workers=5) as pool:
        events = {e['id']: e for day in pool.map(scoreboard, dates) for e in day}
    if not events:
        raise ValueError('No scores returned; preserving previous output')
    out, changed = transform(root, events, now)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    ET.indent(out)
    xml = ET.tostring(out, encoding='utf-8', xml_declaration=True)
    ET.fromstring(xml)
    (output/'nfl-scores.xml').write_bytes(xml)
    (output/'nfl-scores.xml.gz').write_bytes(gzip.compress(xml, mtime=0))
    print(f"Built {len(out.findall('channel'))} NFL event channels; {changed} final-score blocks updated.")
    for p in out.findall('programme'):
        if p.get('channel') == 'teamarr-event-401873053' and (p.findtext('title') or '').startswith('FINAL:'):
            print(p.findtext('title'))
            break

if __name__ == '__main__':
    main()
