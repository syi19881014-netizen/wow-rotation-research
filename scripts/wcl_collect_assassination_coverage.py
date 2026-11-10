#!/usr/bin/env python3
"""Collect enemy-side Garrote/Rupture coverage evidence for top M+ Rogues."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path


TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
API_URL = "https://www.warcraftlogs.com/api/v2/client"
SAMPLE_DIR = Path("data/wcl/rogue/assassination-events/samples")
OUT_DIR = Path("data/wcl/rogue/assassination-events/coverage-raw")
DOT_IDS = (703, 1943)
LIMIT = int(os.environ.get("WCL_EVENT_REPORTS", "8"))


QUERY = """
query Events(
  $code: String!, $fightIDs: [Int!], $sourceID: Int, $start: Float,
  $kind: EventDataType!, $hostility: HostilityType, $abilityID: Float
) {
  reportData {
    report(code: $code) {
      events(
        fightIDs: $fightIDs, sourceID: $sourceID, startTime: $start,
        dataType: $kind, hostilityType: $hostility, abilityID: $abilityID,
        limit: 10000, useActorIDs: true, useAbilityIDs: true
      ) { data nextPageTimestamp }
    }
  }
}
"""


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def get_token() -> str:
    client_id = os.environ.get("WCL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("WCL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("WCL credentials are missing")
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())["access_token"]


def gql(token: str, variables: dict) -> dict:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode())
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], ensure_ascii=False))
    return payload["data"]["reportData"]["report"]["events"]


def events(
    token: str,
    code: str,
    fight_id: int,
    kind: str,
    source_id: int | None,
    hostility: str | None,
    ability_id: int | None = None,
) -> list[dict]:
    result: list[dict] = []
    start = None
    pages = 0
    while True:
        page = gql(
            token,
            {
                "code": code,
                "fightIDs": [fight_id],
                "sourceID": source_id,
                "start": start,
                "kind": kind,
                "hostility": hostility,
                "abilityID": ability_id,
            },
        )
        result.extend(page.get("data") or [])
        pages += 1
        start = page.get("nextPageTimestamp")
        if start is None:
            return result
        if pages >= 100:
            raise RuntimeError(f"Pagination runaway for {code}/{fight_id}/{kind}")
        time.sleep(0.08)


def candidates() -> list[dict]:
    result = []
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        old = json.loads(path.read_text(encoding="utf-8"))
        fight = old["report"]["fight"]
        result.append(
            {
                "file": path.name,
                "code": old["ranking"]["report_code"],
                "fight_id": int(old["ranking"]["fight_id"]),
                "source_id": int(old["player_actor"]["id"]),
                "player": old["ranking"]["player"],
                "level": int(old["ranking"].get("level") or 0),
                "fight_start": float(fight["startTime"]),
                "fight_end": float(fight["endTime"]),
                "actors": old.get("actors") or [],
                "casts": old["events"].get("Casts") or [],
            }
        )
    return result[:LIMIT]


def main() -> int:
    token = get_token()
    status = {"ok": True, "samples": [], "errors": []}
    for candidate in candidates():
        try:
            aura_events = []
            for ability_id in DOT_IDS:
                enemy_debuffs = events(
                    token,
                    candidate["code"],
                    candidate["fight_id"],
                    "Debuffs",
                    None,
                    "Enemies",
                    ability_id,
                )
                aura_events.extend(
                    event
                    for event in enemy_debuffs
                    if int(event.get("sourceID") or -1) == candidate["source_id"]
                )
            death_events = events(
                token,
                candidate["code"],
                candidate["fight_id"],
                "Deaths",
                None,
                "Enemies",
            )
            damage_events = events(
                token,
                candidate["code"],
                candidate["fight_id"],
                "DamageDone",
                candidate["source_id"],
                None,
            )
            payload = {
                "meta": {key: value for key, value in candidate.items() if key != "casts"},
                "events": {
                    "auras": sorted(aura_events, key=lambda event: event["timestamp"]),
                    "deaths": sorted(death_events, key=lambda event: event["timestamp"]),
                    "damage": sorted(damage_events, key=lambda event: event["timestamp"]),
                    "casts": candidate["casts"],
                },
            }
            save(OUT_DIR / candidate["file"], payload)
            row = {
                "file": candidate["file"],
                "player": candidate["player"],
                "auras": len(aura_events),
                "deaths": len(death_events),
                "damage": len(damage_events),
            }
            status["samples"].append(row)
            print(json.dumps(row, ensure_ascii=False))
        except Exception as exc:
            status["ok"] = False
            status["errors"].append({"file": candidate["file"], "error": str(exc)})
    save(OUT_DIR / "status.json", status)
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
