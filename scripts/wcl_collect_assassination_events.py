#!/usr/bin/env python3
"""Collect event-level WCL samples for top Assassination Rogue M+ rankings."""

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
API_URL = "https://www.warcraftlogs.com/api/v2/client"
RANKING_DIR = Path("data/wcl/rogue/rankings/55")
OUT = Path("data/wcl/rogue/assassination-events")
DOT_IDS = {703: "Garrote", 1943: "Rupture"}
MAX_REPORTS = int(os.environ.get("WCL_EVENT_REPORTS", "8"))


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def token(client_id, secret):
    auth = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        method="POST",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())["access_token"]


def gql(access_token, query, variables):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = json.loads(response.read().decode())
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], ensure_ascii=False))
    return payload["data"]


META_QUERY = """
query Meta($code: String!, $fightIDs: [Int!]) {
  reportData {
    report(code: $code) {
      title
      startTime
      fights(fightIDs: $fightIDs) { id name startTime endTime kill }
      masterData { actors { id name type subType server } }
    }
  }
}
"""

EVENT_QUERY = """
query Events($code: String!, $fightIDs: [Int!], $sourceID: Int, $start: Float, $kind: EventDataType!) {
  reportData {
    report(code: $code) {
      events(fightIDs: $fightIDs, sourceID: $sourceID, startTime: $start,
             dataType: $kind, limit: 10000) {
        data
        nextPageTimestamp
      }
    }
  }
}
"""


def ranking_candidates():
    found, seen = [], set()
    for path in sorted(RANKING_DIR.glob("*.json")):
        root = json.loads(path.read_text(encoding="utf-8"))
        encounter = root.get("encounter") or {}
        block = ((root.get("rankings") or {}).get("Assassination") or {})
        for rank, item in enumerate(block.get("rankings") or [], 1):
            report = item.get("report") or {}
            code, fight_id = report.get("code"), report.get("fightID")
            key = (code, fight_id, item.get("name"))
            if code and fight_id and key not in seen:
                seen.add(key)
                found.append({
                    "ranking_file": str(path),
                    "encounter_id": encounter.get("id"),
                    "encounter_name": encounter.get("name"),
                    "rank": rank,
                    "player": item.get("name"),
                    "server": (item.get("server") or {}).get("name"),
                    "region": (item.get("server") or {}).get("region"),
                    "level": item.get("hardModeLevel"),
                    "duration": item.get("duration"),
                    "report_code": code,
                    "fight_id": fight_id,
                })
    found.sort(key=lambda x: (-(x.get("level") or 0), x["rank"], x["duration"] or 10**12))
    return found[:MAX_REPORTS]


def find_player(actors, name):
    exact = [a for a in actors if a.get("type") == "Player" and a.get("name") == name]
    rogue = [a for a in exact if a.get("subType") == "Rogue"]
    return (rogue or exact or [None])[0]


def paged_events(access_token, code, fight_id, source_id, kind, start):
    events, cursor = [], start
    for _ in range(30):
        data = gql(access_token, EVENT_QUERY, {
            "code": code, "fightIDs": [fight_id], "sourceID": source_id,
            "start": cursor, "kind": kind,
        })
        page = data["reportData"]["report"]["events"]
        events.extend(page.get("data") or [])
        nxt = page.get("nextPageTimestamp")
        if nxt is None or nxt == cursor:
            break
        cursor = nxt
        time.sleep(0.15)
    return events


def summarize(sample):
    casts = sample["events"]["Casts"]
    debuffs = sample["events"]["Debuffs"]
    deaths = sample["events"]["Deaths"]
    death_by_target = {}
    for event in deaths:
        target = event.get("targetID")
        if target is not None:
            death_by_target.setdefault(target, []).append(event.get("timestamp", 0))
    for values in death_by_target.values():
        values.sort()

    applications = []
    for event in casts:
        ability = event.get("abilityGameID")
        if ability not in DOT_IDS:
            continue
        timestamp, target = event.get("timestamp", 0), event.get("targetID")
        future = [value for value in death_by_target.get(target, []) if value >= timestamp]
        seconds_to_death = (future[0] - timestamp) / 1000 if future else None
        applications.append({
            "timestamp": timestamp,
            "spell_id": ability,
            "spell": DOT_IDS[ability],
            "target_id": target,
            "seconds_to_target_death": seconds_to_death,
            "within_3s_of_death": seconds_to_death is not None and seconds_to_death <= 3,
            "within_6s_of_death": seconds_to_death is not None and seconds_to_death <= 6,
            "within_10s_of_death": seconds_to_death is not None and seconds_to_death <= 10,
        })

    by_spell = {}
    for spell_id, name in DOT_IDS.items():
        rows = [x for x in applications if x["spell_id"] == spell_id]
        measured = [x["seconds_to_target_death"] for x in rows if x["seconds_to_target_death"] is not None]
        by_spell[name] = {
            "casts": len(rows),
            "casts_with_observed_target_death": len(measured),
            "within_3s": sum(x <= 3 for x in measured),
            "within_6s": sum(x <= 6 for x in measured),
            "within_10s": sum(x <= 10 for x in measured),
            "median_seconds_to_death": sorted(measured)[len(measured)//2] if measured else None,
        }
    return {
        "dot_casts": applications,
        "by_spell": by_spell,
        "debuff_event_count": len(debuffs),
        "limitations": [
            "Time-to-death is paired to the next observed death event for targetID.",
            "Target health percentage is only reported when WCL includes target resource snapshots.",
            "A cast near death can be intentional for Sudden Demise, mark routing, or incidental target selection.",
        ],
    }


def main():
    client_id = os.environ.get("WCL_CLIENT_ID", "").strip()
    secret = os.environ.get("WCL_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        raise SystemExit("Missing WCL_CLIENT_ID/WCL_CLIENT_SECRET")
    access_token = token(client_id, secret)
    status = {"ok": False, "collected_at_utc": utc_now(), "samples": [], "errors": []}

    for candidate in ranking_candidates():
        try:
            meta = gql(access_token, META_QUERY, {
                "code": candidate["report_code"], "fightIDs": [candidate["fight_id"]],
            })["reportData"]["report"]
            actors = (meta.get("masterData") or {}).get("actors") or []
            player = find_player(actors, candidate["player"])
            fights = meta.get("fights") or []
            if not player or not fights:
                raise RuntimeError("player actor or fight not found")
            fight = fights[0]
            source_id = player["id"]
            start = fight["startTime"]
            events = {
                "Casts": paged_events(access_token, candidate["report_code"], candidate["fight_id"], source_id, "Casts", None),
                "Debuffs": paged_events(access_token, candidate["report_code"], candidate["fight_id"], source_id, "Debuffs", None),
                "Deaths": paged_events(access_token, candidate["report_code"], candidate["fight_id"], None, "Deaths", None),
            }
            sample = {
                "ranking": candidate,
                "report": {"title": meta.get("title"), "fight": fight},
                "player_actor": player,
                "actors": actors,
                "events": events,
            }
            sample["analysis"] = summarize(sample)
            filename = f'{candidate["report_code"]}-{candidate["fight_id"]}-{source_id}.json'
            save(OUT / "samples" / filename, sample)
            status["samples"].append({
                "file": str(OUT / "samples" / filename),
                "player": candidate["player"],
                "report_code": candidate["report_code"],
                "fight_id": candidate["fight_id"],
                "source_id": source_id,
                "level": candidate.get("level"),
                "summary": sample["analysis"]["by_spell"],
            })
            time.sleep(0.25)
        except Exception as error:
            status["errors"].append({"candidate": candidate, "error": str(error)})

    status["ok"] = bool(status["samples"])
    status["message"] = "Event samples collected." if status["ok"] else "No event samples collected."
    save(OUT / "status.json", status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
