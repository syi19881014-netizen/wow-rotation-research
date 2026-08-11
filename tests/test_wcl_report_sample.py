from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wcl_collect_report_sample import (  # noqa: E402
    collect_event_stream,
    merge_and_classify_events,
    resolve_actor,
    sanitize_player_data,
    validate_config,
)


class FakeEventClient:
    def __init__(self):
        self.calls = []

    def query(self, _query, variables):
        self.calls.append(variables)
        page = len(self.calls)
        events = (
            [{"timestamp": 10, "type": "begincast", "sourceID": 7}]
            if page == 1
            else [{"timestamp": 20, "type": "cast", "sourceID": 7}]
        )
        return {
            "rateLimitData": {
                "limitPerHour": 3600,
                "pointsSpentThisHour": 10,
                "pointsResetIn": 100,
            },
            "reportData": {
                "report": {
                    "revision": 3,
                    "events": {
                        "data": events,
                        "nextPageTimestamp": 15 if page == 1 else None,
                    },
                }
            },
        }


class ReportSampleTests(unittest.TestCase):
    def test_sample_config(self):
        config = json.loads(
            (ROOT / "config/samples/rogue_assassination_murder_row.json").read_text()
        )
        validate_config(config)

    def test_unique_class_spec_resolves_actor(self):
        resolution = resolve_actor(
            actors=[
                {"id": 1, "type": "Player", "subType": "Mage", "name": "A"},
                {"id": 7, "type": "Player", "subType": "Rogue", "name": "B"},
            ],
            fight={
                "friendlyPlayers": [1, 7],
                "friendlySpecs": ["Frost", "Assassination"],
            },
            player_details={},
            ranking={"class": "Rogue", "spec": "Assassination"},
        )
        self.assertEqual(resolution["source_id"], 7)
        self.assertEqual(resolution["method"], "friendly_class_and_spec_unique")

    def test_fingerprint_breaks_same_spec_tie(self):
        resolution = resolve_actor(
            actors=[
                {"id": 7, "type": "Player", "subType": "Rogue", "name": "A"},
                {"id": 8, "type": "Player", "subType": "Rogue", "name": "B"},
            ],
            fight={
                "friendlyPlayers": [7, 8],
                "friendlySpecs": ["Outlaw", "Outlaw"],
            },
            player_details={
                "data": {
                    "dps": [
                        {"id": 7, "combatantInfo": {"gear": [{"id": 100}]}},
                        {
                            "id": 8,
                            "combatantInfo": {
                                "gear": [{"id": 200}, {"id": 201}],
                                "talents": [{"talentID": 300}],
                            },
                        },
                    ]
                }
            },
            ranking={
                "class": "Rogue",
                "spec": "Outlaw",
                "gear_ids": [200, 201],
                "talent_ids": [300],
            },
        )
        self.assertEqual(resolution["source_id"], 8)
        self.assertEqual(resolution["method"], "combatant_gear_talent_fingerprint")

    def test_event_timestamp_pagination(self):
        client = FakeEventClient()
        events, manifest = collect_event_stream(
            client,
            report_code="ABC",
            fight_id=2,
            fight_start=0,
            fight_end=100,
            stream_name="source:7",
            source_id=7,
            target_id=None,
            include_resources=True,
            page_limit=10000,
            max_pages=4,
            reserve_points=100,
        )
        self.assertEqual(len(events), 2)
        self.assertTrue(manifest["complete"])
        self.assertEqual(manifest["page_count"], 2)
        self.assertEqual([call["startTime"] for call in client.calls], [0.0, 15.0])

    def test_deduplicates_streams_and_builds_overlapping_tables(self):
        event = {
            "timestamp": 10,
            "type": "cast",
            "sourceID": 7,
            "targetID": 9,
            "sourceResources": {"energy": 80},
        }
        tables = merge_and_classify_events(
            [("source:7", [event]), ("target:9", [dict(event)])]
        )
        self.assertEqual(len(tables["all"]), 1)
        self.assertEqual(tables["all"][0]["streams"], ["source:7", "target:9"])
        self.assertEqual(len(tables["casts"]), 1)
        self.assertEqual(len(tables["resources"]), 1)

    def test_player_identity_is_redacted_but_actor_id_is_stable(self):
        value = [
            {
                "id": 7,
                "name": "Realname",
                "server": "Realm",
                "gameID": 123,
                "combatantInfo": {"gear": [{"id": 999}]},
            }
        ]
        sanitized = sanitize_player_data(value, {7})
        self.assertEqual(sanitized[0]["id"], 7)
        self.assertEqual(sanitized[0]["name"], "Player 7")
        self.assertIsNone(sanitized[0]["server"])
        self.assertIsNone(sanitized[0]["gameID"])
        self.assertEqual(sanitized[0]["combatantInfo"]["gear"][0]["id"], 999)


if __name__ == "__main__":
    unittest.main()
