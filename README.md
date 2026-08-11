# wow-rotation-research

WoW 12.1 rotation research code, schemas, tests and bounded WCL event samples.

## Repository contract

This repository no longer runs a second rankings collector. Public ranking snapshots are
owned by `syi19881014-netizen/wow-rotation-data`; this repository owns the deeper
report/event research path:

```text
ranking pointer
  -> report + fight
  -> masterData actors/abilities
  -> friendlyPlayers + friendlySpecs actor resolution
  -> playerDetails gear/talent fingerprint fallback
  -> source + target + owned-pet event streams
  -> casts/resources/auras/damage/targets/fight segments
```

`scripts/wcl_collect_report_sample.py` follows every `nextPageTimestamp`, pins report
revision and game/log versions, records query hashes and checksums, and refuses to publish
an incomplete stream. It writes only the configured fight or dungeon-pull window as a
bounded compressed sample under `data/samples/`.
Player names, realms and stable game IDs are redacted before a sample is committed; only
report-local actor IDs needed to join events are preserved.

The output is an **L5 event sample**. Reconstructing cooldowns, charges, the state before
each GCD, channel clipping and the final SimC/APL comparison remains the L6/L7 analysis
layer and is deliberately not claimed by this collector.

## Local validation

```bash
python3 -m compileall -q scripts tests
python3 -m unittest discover -s tests -v
python3 scripts/wcl_collect_report_sample.py --validate-only
```

Live sampling additionally requires `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET`.
