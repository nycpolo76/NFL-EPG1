import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from update_nfl_scores import transform

class ScoresTest(unittest.TestCase):
    def test_only_verified_finals_replace_postgame(self):
        source = ET.fromstring('''<tv><channel id="teamarr-event-1"><display-name>Game</display-name></channel><programme channel="teamarr-event-1"><title>Patriots @ Lions</title><category>NFL Gamepass</category></programme><programme channel="teamarr-event-1"><title>FINAL:</title><desc>Awaiting result</desc><category>NFL Gamepass</category></programme></tv>''')
        event = {'status': {'type': {'completed': True, 'name': 'STATUS_FINAL'}}, 'competitions': [{'competitors': [
            {'homeAway':'home','score':'35','team':{'shortDisplayName':'Lions','displayName':'Detroit Lions'}},
            {'homeAway':'away','score':'10','team':{'shortDisplayName':'Patriots','displayName':'New England Patriots'}}]}]}
        out, n = transform(source, {'1': event}, datetime.now(timezone.utc))
        self.assertEqual(n, 1)
        self.assertEqual(out.findall('programme')[0].findtext('title'), 'Patriots @ Lions')
        self.assertEqual(out.findall('programme')[1].findtext('title'), 'FINAL: Patriots 10 – Lions 35')
        for status in ({'completed':False,'state':'in'}, {}, {'completed':True,'name':'STATUS_CANCELED'}):
            event['status']['type'] = status
            out, n = transform(source, {'1':event}, datetime.now(timezone.utc))
            self.assertEqual(n, 0)
            self.assertNotIn('FINAL:',out.findall('programme')[1].findtext('title'))
        self.assertEqual(source.findall('programme')[1].findtext('title'),'FINAL:')

if __name__ == '__main__':
    unittest.main()
