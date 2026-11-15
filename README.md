# NFL final-score EPG for TiviMate

EPG URL:

https://raw.githubusercontent.com/nycpolo76/NFL-EPG1/main/scores-output/nfl-scores.xml.gz

Add this as an additional EPG source in TiviMate, then assign it to the corresponding NFL event channels. Keep your existing guide for other channels. This guide retains the upstream teamarr-event IDs; newly created event IDs may require reassignment each week.

The updater checks roughly every 15 minutes. GitHub scheduling and TiviMate refreshes can add delay. It replaces postgame FINAL placeholders only after ESPN confirms a final result. Scheduled listings remain intact. The initial overlay covers the NFL event channels present in the upstream guide.

Sources: ferteque/Curated-M3U-Repository epg6.xml.gz and ESPN's public NFL scoreboard endpoint (undocumented and subject to change). On request failures the previous committed guide remains available.

No IPTV provider account or credentials are required.
