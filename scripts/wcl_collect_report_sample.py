#!/usr/bin/env python3
"""Descend from a ranking pointer into a complete actor event sample."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from wcl_common import (
    API_URL,
    WCLClient,
    WCLRequestError,
    canonical_json_bytes,
    query_sha256,
    rate_limit_remaining,
    read_json,
    sha256_file,
    utc_now,
    write_gzip_json,
    write_gzip_jsonl,
    write_json,
)


COLLECTOR_NAME = "wcl_report_event_sample"
COLLECTOR_VERSION = "1.0.0"
MANIFEST_SCHEMA = "wcl.report-sample-manifest.v1"


REPORT_QUERY = """
query ReportSampleMetadata($code: String!, $fightIDs: [Int]!) {
  rateLimitData { limitPerHour pointsSpentThisHour pointsResetIn }
  reportData {
    report(code: $code) {
      code
      title
      visibility
      startTime
      endTime
      revision
      segments
      exportedSegments
      archiveStatus { isArchived isAccessible }
      masterData(translate: false) {
        logVersion
        gameVersion
        lang
        abilities { gameID icon name type }
        actors { id gameID icon name petOwner server subType type }
      }
      fights(fightIDs: $fightIDs, translate: false) {
        id
        encounterID
        originalEncounterID
        name
        startTime
        endTime
        kill
        inProgress
        difficulty
        size
        hardModeLevel
        keystoneLevel
        keystoneBonus
        keystoneTime
        rating
        bossPercentage
        fightPercentage
        lastPhase
        lastPhaseAsAbsoluteIndex
        lastPhaseIsIntermission
        averageItemLevel
        friendlyPlayers
        friendlySpecs
        friendlyItemLevels
        friendlyNPCs { id gameID instanceCount groupCount petOwner }
        friendlyPets { id gameID instanceCount groupCount petOwner }
        enemyPlayers
        enemyNPCs { id gameID instanceCount groupCount petOwner }
        enemyPets { id gameID instanceCount groupCount petOwner }
        gameZone { id name }
        maps { id }
        phaseTransitions { id startTime }
        dungeonPulls {
          id
          encounterID
          name
          startTime
          endTime
          kill
          x
          y
          maps { id }
          enemyNPCs {
            id
            gameID
            minimumInstanceID
            maximumInstanceID
            minimumInstanceGroupID
            maximumInstanceGroupID
          }
        }
      }
      playerDetails(
        fightIDs: $fightIDs
        includeCombatantInfo: true
        translate: false
      )
    }
  }
}
""".strip()


TALENT_QUERY = """
query ReportActorTalent($code: String!, $fightIDs: [Int]!, $sourceID: Int!) {
  rateLimitData { limitPerHour pointsSpentThisHour pointsResetIn }
  reportData {
    report(code: $code) {
      fights(fightIDs: $fightIDs, translate: false) {
        id
        talentImportCode(actorID: $sourceID)
      }
    }
  }
}
""".strip()


EVENT_QUERY = """
query ReportActorEvents(
  $code: String!
  $fightIDs: [Int]!
  $startTime: Float!
  $endTime: Float!
  $dataType: EventDataType!
  $sourceID: Int
  $targetID: Int
  $includeResources: Boolean!
  $limit: Int!
) {
  rateLimitData { limitPerHour pointsSpentThisHour pointsResetIn }
  reportData {
    report(code: $code) {
      revision
      events(
        dataType: $dataType
        fightIDs: $fightIDs
        startTime: $startTime
        endTime: $endTime
        sourceID: $sourceID
        targetID: $targetID
        includeResources: $includeResources
        limit: $limit
        translate: false
        useAbilityIDs: true
        useActorIDs: true
      ) {
        data
        nextPageTimestamp
      }
    }
  }
}
""".strip()


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != "wcl.sample-pointer.v1":
        raise ValueError("unsupported or missing sample pointer schema_version")
    if not isinstance(config.get("report_code"), str) or not config["report_code"]:
        raise ValueError("report_code is required")
    if not isinstance(config.get("fight_id"), int) or config["fight_id"] < 1:
        raise ValueError("fight_id must be a positive integer")
    ranking = config.get("ranking")
    collection = config.get("collection")
    if not isinstance(ranking, dict):
        raise ValueError("ranking must be an object")
    for field in ("class", "spec", "spec_key"):
        if not isinstance(ranking.get(field), str) or not ranking[field]:
            raise ValueError(f"ranking.{field} is required")
    if not isinstance(collection, dict):
        raise ValueError("collection must be an object")
    sample_window = config.get("sample_window") or {"kind": "fight"}
    if not isinstance(sample_window, dict) or sample_window.get("kind") not in {
        "fight",
        "dungeon_pull",
    }:
        raise ValueError("sample_window.kind must be fight or dungeon_pull")
    if sample_window.get("kind") == "dungeon_pull" and (
        not isinstance(sample_window.get("index"), int)
        or sample_window["index"] < 0
    ):
        raise ValueError("dungeon_pull sample_window requires a non-negative index")
    allowed_event_types = {
        "All",
        "Buffs",
        "Casts",
        "CombatantInfo",
        "DamageDone",
        "DamageTaken",
        "Deaths",
        "Debuffs",
        "Dispels",
        "Healing",
        "Interrupts",
        "Resources",
        "Summons",
        "Threat",
    }
    target_event_types = collection.get("target_event_types", [])
    if not isinstance(target_event_types, list) or any(
        value not in allowed_event_types for value in target_event_types
    ):
        raise ValueError("collection.target_event_types contains an invalid EventDataType")
    limit = collection.get("event_page_limit", 10000)
    max_pages = collection.get("max_pages_per_stream", 200)
    if not isinstance(limit, int) or not 100 <= limit <= 10000:
        raise ValueError("event_page_limit must be between 100 and 10000")
    if not isinstance(max_pages, int) or max_pages < 1:
        raise ValueError("max_pages_per_stream must be positive")


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _detail_records(player_details: Any, actor_id: int) -> list[dict[str, Any]]:
    output = []
    for item in _walk(player_details):
        if item.get("id") == actor_id and any(
            key in item
            for key in ("combatantInfo", "gear", "talents", "specs", "icon", "type")
        ):
            output.append(item)
    return output


def _fingerprint(value: Any) -> tuple[set[int], set[int]]:
    gear: set[int] = set()
    talents: set[int] = set()
    for item in _walk(value):
        gear_value = item.get("gear")
        if isinstance(gear_value, list):
            for entry in gear_value:
                if isinstance(entry, dict) and isinstance(entry.get("id"), int):
                    gear.add(entry["id"])
        talent_value = item.get("talents")
        if isinstance(talent_value, list):
            for entry in talent_value:
                if not isinstance(entry, dict):
                    continue
                candidate = entry.get("talentID", entry.get("id"))
                if isinstance(candidate, int):
                    talents.add(candidate)
    return gear, talents


def resolve_actor(
    *,
    actors: list[dict[str, Any]],
    fight: dict[str, Any],
    player_details: Any,
    ranking: dict[str, Any],
    explicit_source_id: int | None = None,
) -> dict[str, Any]:
    actors_by_id = {
        item["id"]: item
        for item in actors
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    friendly_players = [
        value for value in fight.get("friendlyPlayers") or [] if isinstance(value, int)
    ]
    friendly_specs = fight.get("friendlySpecs") or []
    spec_by_id = {
        actor_id: friendly_specs[index]
        for index, actor_id in enumerate(friendly_players)
        if index < len(friendly_specs)
    }
    expected_class = normalize(ranking.get("class"))
    expected_spec = normalize(ranking.get("spec"))

    def valid_class(actor_id: int) -> bool:
        actor = actors_by_id.get(actor_id) or {}
        return normalize(actor.get("subType")) == expected_class

    def valid_spec(actor_id: int) -> bool:
        actual = normalize(spec_by_id.get(actor_id))
        return actual == expected_spec or actual.endswith(expected_spec)

    if explicit_source_id is not None:
        if explicit_source_id not in friendly_players:
            raise ValueError(
                f"explicit source ID {explicit_source_id} is not a friendly player in fight"
            )
        if explicit_source_id not in actors_by_id:
            raise ValueError(f"explicit source ID {explicit_source_id} is absent from actors")
        if not valid_class(explicit_source_id) or not valid_spec(explicit_source_id):
            raise ValueError(
                f"explicit source ID {explicit_source_id} does not match "
                f"{ranking.get('class')} {ranking.get('spec')}"
            )
        return {
            "source_id": explicit_source_id,
            "method": "explicit_source_id",
            "actor": actors_by_id[explicit_source_id],
            "candidate_ids": [explicit_source_id],
            "scores": {},
        }

    candidates = [
        actor_id
        for actor_id in friendly_players
        if valid_class(actor_id) and valid_spec(actor_id)
    ]
    if len(candidates) == 1:
        actor_id = candidates[0]
        return {
            "source_id": actor_id,
            "method": "friendly_class_and_spec_unique",
            "actor": actors_by_id[actor_id],
            "candidate_ids": candidates,
            "scores": {},
        }
    if not candidates:
        candidates = [actor_id for actor_id in friendly_players if valid_class(actor_id)]
    if not candidates:
        raise ValueError(
            f"no friendly actor matched class={ranking.get('class')} "
            f"spec={ranking.get('spec')}"
        )

    expected_gear = {
        value for value in ranking.get("gear_ids") or [] if isinstance(value, int)
    }
    expected_talents = {
        value for value in ranking.get("talent_ids") or [] if isinstance(value, int)
    }
    scores: dict[int, dict[str, int]] = {}
    for actor_id in candidates:
        details = _detail_records(player_details, actor_id)
        observed_gear, observed_talents = _fingerprint(details)
        gear_overlap = len(expected_gear & observed_gear)
        talent_overlap = len(expected_talents & observed_talents)
        scores[actor_id] = {
            "gear_overlap": gear_overlap,
            "talent_overlap": talent_overlap,
            "total": gear_overlap * 4 + talent_overlap,
        }
    ranked = sorted(candidates, key=lambda value: scores[value]["total"], reverse=True)
    if not ranked or scores[ranked[0]]["total"] <= 0:
        raise ValueError(
            "actor resolution is ambiguous and playerDetails did not expose a matching "
            f"combatant fingerprint; candidates={candidates}"
        )
    if len(ranked) > 1 and scores[ranked[0]]["total"] == scores[ranked[1]]["total"]:
        raise ValueError(
            f"actor fingerprint tie between source IDs {ranked[0]} and {ranked[1]}"
        )
    actor_id = ranked[0]
    return {
        "source_id": actor_id,
        "method": "combatant_gear_talent_fingerprint",
        "actor": actors_by_id[actor_id],
        "candidate_ids": candidates,
        "scores": scores,
    }


def collect_event_stream(
    client: WCLClient,
    *,
    report_code: str,
    fight_id: int,
    fight_start: float,
    fight_end: float,
    stream_name: str,
    data_type: str,
    source_id: int | None,
    target_id: int | None,
    include_resources: bool,
    page_limit: int,
    max_pages: int,
    reserve_points: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    start = float(fight_start)
    seen_starts: set[float] = set()
    events: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    last_rate_limit: dict[str, Any] | None = None

    for page_number in range(1, max_pages + 1):
        if start in seen_starts:
            raise WCLRequestError(
                f"event pagination repeated start timestamp {start} for {stream_name}"
            )
        seen_starts.add(start)
        variables = {
            "code": report_code,
            "fightIDs": [fight_id],
            "startTime": start,
            "endTime": float(fight_end),
            "dataType": data_type,
            "sourceID": source_id,
            "targetID": target_id,
            "includeResources": include_resources,
            "limit": page_limit,
        }
        response = client.query(EVENT_QUERY, variables)
        last_rate_limit = response.get("rateLimitData")
        remaining = rate_limit_remaining(last_rate_limit)
        if remaining is not None and remaining < reserve_points:
            raise WCLRequestError(
                f"rate-limit reserve reached ({remaining:.2f} points remaining)"
            )
        report = ((response.get("reportData") or {}).get("report") or {})
        paginator = report.get("events") or {}
        page_events = paginator.get("data") or []
        if not isinstance(page_events, list) or any(
            not isinstance(event, dict) for event in page_events
        ):
            raise WCLRequestError(f"events.data was not an object array for {stream_name}")
        next_timestamp = paginator.get("nextPageTimestamp")
        pages.append(
            {
                "page": page_number,
                "start_time": start,
                "event_count": len(page_events),
                "next_page_timestamp": next_timestamp,
                "report_revision": report.get("revision"),
            }
        )
        events.extend(page_events)
        if next_timestamp is None:
            return events, {
                "name": stream_name,
                "source_id": source_id,
                "target_id": target_id,
                "data_type": data_type,
                "include_resources": include_resources,
                "complete": True,
                "page_count": len(pages),
                "raw_event_count": len(events),
                "pages": pages,
                "rate_limit_after": last_rate_limit,
            }
        if not isinstance(next_timestamp, (int, float)):
            raise WCLRequestError(
                f"invalid nextPageTimestamp for {stream_name}: {next_timestamp!r}"
            )
        if float(next_timestamp) < start:
            raise WCLRequestError(
                f"event pagination moved backwards for {stream_name}: "
                f"{next_timestamp} < {start}"
            )
        start = float(next_timestamp)
    raise WCLRequestError(
        f"event stream {stream_name} exceeded max_pages_per_stream={max_pages}"
    )


def select_sample_window(
    fight: dict[str, Any], selection: dict[str, Any] | None
) -> dict[str, Any]:
    selection = selection or {"kind": "fight"}
    kind = selection.get("kind", "fight")
    if kind == "fight":
        return {
            "kind": "fight",
            "id": fight.get("id"),
            "name": fight.get("name"),
            "start_time": float(fight["startTime"]),
            "end_time": float(fight["endTime"]),
            "full_fight_covered": True,
        }
    pulls = fight.get("dungeonPulls") or []
    index = selection.get("index")
    if not isinstance(index, int) or index < 0 or index >= len(pulls):
        raise ValueError(
            f"dungeon pull index {index!r} is outside available range 0..{len(pulls)-1}"
        )
    pull = pulls[index]
    return {
        "kind": "dungeon_pull",
        "index": index,
        "id": pull.get("id"),
        "encounter_id": pull.get("encounterID"),
        "name": pull.get("name"),
        "start_time": float(pull["startTime"]),
        "end_time": float(pull["endTime"]),
        "duration_ms": float(pull["endTime"]) - float(pull["startTime"]),
        "full_fight_covered": False,
    }


def _contains_resource_payload(event: dict[str, Any]) -> bool:
    for item in _walk(event):
        if any(
            key in item
            for key in (
                "sourceResources",
                "targetResources",
                "classResources",
                "resourceChange",
                "resourceChangeType",
                "waste",
            )
        ):
            return True
    return False


def merge_and_classify_events(
    streams: list[tuple[str, list[dict[str, Any]]]],
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, dict[str, Any]] = {}
    for stream_name, events in streams:
        for event in events:
            event_id = hashlib.sha256(canonical_json_bytes(event)).hexdigest()
            record = merged.setdefault(
                event_id,
                {"event_id": event_id, "streams": set(), "event": event},
            )
            record["streams"].add(stream_name)

    records = [
        {
            "event_id": event_id,
            "streams": sorted(record["streams"]),
            "event": record["event"],
        }
        for event_id, record in merged.items()
    ]
    records.sort(
        key=lambda record: (
            float(record["event"].get("timestamp", 0) or 0),
            str(record["event"].get("type", "")),
            record["event_id"],
        )
    )
    tables: dict[str, list[dict[str, Any]]] = {
        "all": records,
        "casts": [],
        "auras": [],
        "resources": [],
        "damage": [],
        "summons": [],
        "interrupts": [],
        "deaths": [],
        "other": [],
    }
    for record in records:
        event = record["event"]
        event_type = normalize(event.get("type"))
        classified = False
        if event_type in {"begincast", "cast", "castfailed"}:
            tables["casts"].append(record)
            classified = True
        if "buff" in event_type or "debuff" in event_type:
            tables["auras"].append(record)
            classified = True
        if (
            "resource" in event_type
            or "energize" in event_type
            or _contains_resource_payload(event)
        ):
            tables["resources"].append(record)
            classified = True
        if "damage" in event_type:
            tables["damage"].append(record)
            classified = True
        if event_type in {"summon", "create", "destroy"}:
            tables["summons"].append(record)
            classified = True
        if "interrupt" in event_type:
            tables["interrupts"].append(record)
            classified = True
        if event_type in {"death", "unitdied"}:
            tables["deaths"].append(record)
            classified = True
        if not classified:
            tables["other"].append(record)
    return tables


def build_target_summary(
    events: list[dict[str, Any]], actors: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    counts: Counter[tuple[Any, Any]] = Counter()
    for record in events:
        event = record["event"]
        target_id = event.get("targetID")
        target_instance = event.get("targetInstance") or event.get("targetInstanceID")
        if target_id is not None:
            counts[(target_id, target_instance)] += 1
    actors_by_id = {
        item.get("id"): item for item in actors if isinstance(item, dict)
    }
    output = []
    for (target_id, target_instance), count in counts.most_common():
        actor = actors_by_id.get(target_id) or {}
        output.append(
            {
                "target_id": target_id,
                "target_instance": target_instance,
                "event_count": count,
                "name": actor.get("name"),
                "type": actor.get("type"),
                "sub_type": actor.get("subType"),
                "game_id": actor.get("gameID"),
                "pet_owner": actor.get("petOwner"),
            }
        )
    return output


def sanitize_player_data(value: Any, player_ids: set[int]) -> Any:
    """Redact identities that WCL rankings intentionally exposed as anonymous."""

    def visit(item: Any, inherited_actor_id: int | None = None) -> Any:
        if isinstance(item, list):
            return [visit(child, inherited_actor_id) for child in item]
        if not isinstance(item, dict):
            return item
        actor_id = item.get("id") if item.get("id") in player_ids else inherited_actor_id
        output = {}
        for key, child in item.items():
            if actor_id in player_ids and key == "name":
                output[key] = f"Player {actor_id}"
            elif actor_id in player_ids and key in {"server", "gameID", "guid"}:
                output[key] = None
            else:
                output[key] = visit(child, actor_id)
        return output

    return visit(copy.deepcopy(value))


def artifact_entry(root: Path, path: Path, row_count: int | None = None) -> dict[str, Any]:
    entry = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }
    if row_count is not None:
        entry["row_count"] = row_count
    return entry


def _safe_replace_directory(staged: Path, destination: Path, output_root: Path) -> None:
    output_resolved = output_root.resolve()
    destination_resolved = destination.resolve()
    if output_resolved not in destination_resolved.parents:
        raise RuntimeError(f"refusing to replace path outside output root: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    os.replace(staged, destination)


def write_sample(
    *,
    output_root: Path,
    config: dict[str, Any],
    report: dict[str, Any],
    fight: dict[str, Any],
    sample_window: dict[str, Any],
    actor_resolution: dict[str, Any],
    talent_import_code: str | None,
    streams: list[tuple[str, list[dict[str, Any]]]],
    stream_manifests: list[dict[str, Any]],
) -> Path:
    ranking = config["ranking"]
    source_id = int(actor_resolution["source_id"])
    report_code = config["report_code"]
    fight_id = int(config["fight_id"])
    relative = (
        Path(ranking["spec_key"])
        / report_code
        / f"fight-{fight_id}"
        / f"source-{source_id}"
    )
    output_root.mkdir(parents=True, exist_ok=True)
    staging_parent = output_root / ".staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging_parent) as temporary:
        staged = Path(temporary) / "sample"
        staged.mkdir(parents=True)
        master_data = report.get("masterData") or {}
        raw_actors = master_data.get("actors") or []
        player_ids = {
            int(item["id"])
            for item in raw_actors
            if isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and normalize(item.get("type")) == "player"
        }
        actors = sanitize_player_data(raw_actors, player_ids)
        abilities = master_data.get("abilities") or []
        player_details = sanitize_player_data(report.get("playerDetails"), player_ids)
        public_resolution = sanitize_player_data(actor_resolution, player_ids)

        report_header = copy.deepcopy(report)
        report_header.pop("masterData", None)
        report_header.pop("playerDetails", None)
        report_header.pop("fights", None)
        report_header["fight_absolute_start_time"] = (
            float(report["startTime"]) + float(fight["startTime"])
        )
        report_header["fight_absolute_end_time"] = (
            float(report["startTime"]) + float(fight["endTime"])
        )
        report_header["source_id"] = source_id
        report_header["talent_import_code"] = talent_import_code
        report_header["sample_window"] = sample_window

        metadata_dir = staged / "metadata"
        write_json(metadata_dir / "report.json", report_header)
        write_json(metadata_dir / "fight.json", fight)
        write_gzip_json(metadata_dir / "actors.json.gz", actors)
        write_gzip_json(metadata_dir / "abilities.json.gz", abilities)
        write_gzip_json(metadata_dir / "player_details.json.gz", player_details)

        tables = merge_and_classify_events(streams)
        events_dir = staged / "events"
        artifacts: dict[str, dict[str, Any]] = {}
        for name, rows in tables.items():
            path = events_dir / f"{name}.jsonl.gz"
            write_gzip_jsonl(path, rows)
            artifacts[name] = artifact_entry(staged, path, len(rows))

        derived_dir = staged / "derived"
        targets = build_target_summary(tables["all"], actors)
        segments = {
            "fight": {
                "id": fight.get("id"),
                "start_time": fight.get("startTime"),
                "end_time": fight.get("endTime"),
                "phase_transitions": fight.get("phaseTransitions") or [],
            },
            "dungeon_pulls": fight.get("dungeonPulls") or [],
        }
        write_json(derived_dir / "targets.json", targets)
        write_json(derived_dir / "fight_segments.json", segments)

        actor_ids = {source_id}
        actor_ids.update(
            item.get("id")
            for item in raw_actors
            if isinstance(item, dict) and item.get("petOwner") == source_id
        )
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "collected_at_utc": utc_now(),
            "collector": {
                "name": COLLECTOR_NAME,
                "version": COLLECTOR_VERSION,
                "commit": os.environ.get("GITHUB_SHA") or None,
            },
            "source": {
                "api": API_URL,
                "report_code": report_code,
                "report_revision": report.get("revision"),
                "fight_id": fight_id,
                "ranking_pointer": ranking,
                "query_sha256": {
                    "metadata": query_sha256(REPORT_QUERY),
                    "talent": query_sha256(TALENT_QUERY),
                    "events": query_sha256(EVENT_QUERY),
                },
            },
            "identity": {
                "source_id": source_id,
                "owned_actor_ids": sorted(value for value in actor_ids if value is not None),
                "resolution": public_resolution,
                "talent_import_code": talent_import_code,
            },
            "report_versions": {
                "log_version": master_data.get("logVersion"),
                "game_version": master_data.get("gameVersion"),
                "language": master_data.get("lang"),
            },
            "fight": {
                "encounter_id": fight.get("encounterID"),
                "name": fight.get("name"),
                "start_time": fight.get("startTime"),
                "end_time": fight.get("endTime"),
                "kill": fight.get("kill"),
                "difficulty": fight.get("difficulty"),
                "keystone_level": fight.get("keystoneLevel"),
                "game_zone": fight.get("gameZone"),
                "dungeon_pull_count": len(fight.get("dungeonPulls") or []),
            },
            "sample_window": sample_window,
            "completeness": {
                "complete": all(item["complete"] for item in stream_manifests),
                "scope": "selected_window",
                "full_fight_covered": sample_window["full_fight_covered"],
                "stream_count": len(stream_manifests),
                "raw_stream_event_count": sum(
                    item["raw_event_count"] for item in stream_manifests
                ),
                "unique_event_count": len(tables["all"]),
                "streams": stream_manifests,
            },
            "tables": artifacts,
            "metadata": {
                "report": artifact_entry(staged, metadata_dir / "report.json"),
                "fight": artifact_entry(staged, metadata_dir / "fight.json"),
                "actors": artifact_entry(staged, metadata_dir / "actors.json.gz", len(actors)),
                "abilities": artifact_entry(
                    staged, metadata_dir / "abilities.json.gz", len(abilities)
                ),
                "player_details": artifact_entry(
                    staged, metadata_dir / "player_details.json.gz"
                ),
                "targets": artifact_entry(staged, derived_dir / "targets.json", len(targets)),
                "fight_segments": artifact_entry(
                    staged, derived_dir / "fight_segments.json"
                ),
            },
            "limitations": [
                "This is an L5 event sample, not an L6 per-GCD decision-state reconstruction.",
                "Cooldown and charge state must be derived from spell data and the event sequence.",
                "Cast cancellation and channel clipping must be inferred from begin/cast/interrupt timing.",
                "Event completeness applies to the selected window, not necessarily the full fight.",
                "Warcraft Logs documents report events as mutable data; report revision is pinned here.",
            ],
            "privacy": {
                "player_names_redacted": True,
                "player_servers_redacted": True,
                "player_game_ids_redacted": True,
                "report_actor_ids_preserved": True,
            },
            "secrets_exposed": False,
        }
        write_json(staged / "manifest.json", manifest)
        destination = output_root / relative
        _safe_replace_directory(staged, destination, output_root)
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/samples/rogue_assassination_murder_row.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("data/samples"))
    parser.add_argument("--source-id", type=int)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = read_json(args.config)
        validate_config(config)
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "config": str(args.config),
                        "query_sha256": {
                            "metadata": query_sha256(REPORT_QUERY),
                            "talent": query_sha256(TALENT_QUERY),
                            "events": query_sha256(EVENT_QUERY),
                        },
                    },
                    indent=2,
                )
            )
            return 0

        client = WCLClient(
            os.environ.get("WCL_CLIENT_ID", "").strip(),
            os.environ.get("WCL_CLIENT_SECRET", "").strip(),
        )
        report_code = config["report_code"]
        fight_id = int(config["fight_id"])
        metadata_response = client.query(
            REPORT_QUERY, {"code": report_code, "fightIDs": [fight_id]}
        )
        report = ((metadata_response.get("reportData") or {}).get("report") or {})
        if report.get("code") != report_code:
            raise WCLRequestError(f"report {report_code} was not returned")
        fights = report.get("fights") or []
        if len(fights) != 1 or int(fights[0].get("id", -1)) != fight_id:
            raise WCLRequestError(
                f"fight lookup expected exactly fight {fight_id}, received {len(fights)} rows"
            )
        fight = fights[0]
        if fight.get("inProgress"):
            raise WCLRequestError("refusing to sample a fight that is still in progress")
        master_data = report.get("masterData") or {}
        actors = master_data.get("actors") or []
        resolution = resolve_actor(
            actors=actors,
            fight=fight,
            player_details=report.get("playerDetails"),
            ranking=config["ranking"],
            explicit_source_id=args.source_id,
        )
        source_id = int(resolution["source_id"])
        sample_window = select_sample_window(fight, config.get("sample_window"))

        talent_response = client.query(
            TALENT_QUERY,
            {"code": report_code, "fightIDs": [fight_id], "sourceID": source_id},
        )
        talent_fights = (
            (((talent_response.get("reportData") or {}).get("report") or {}).get("fights"))
            or []
        )
        talent_import_code = (
            talent_fights[0].get("talentImportCode") if talent_fights else None
        )

        collection = config["collection"]
        owned_pets = [
            int(item["id"])
            for item in actors
            if isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and item.get("petOwner") == source_id
            and normalize(item.get("type")) == "pet"
        ]
        stream_specs: list[
            tuple[str, int | None, int | None, str, bool]
        ] = [
            (
                f"source:{source_id}:All",
                source_id,
                None,
                "All",
                bool(collection.get("include_resources", True)),
            )
        ]
        stream_specs.extend(
            (f"target:{source_id}:{data_type}", None, source_id, data_type, False)
            for data_type in collection.get("target_event_types", [])
        )
        if collection.get("include_owned_pet_source_events", True):
            stream_specs.extend(
                (
                    f"source:{pet_id}:All",
                    pet_id,
                    None,
                    "All",
                    bool(collection.get("include_resources", True)),
                )
                for pet_id in owned_pets
            )

        streams: list[tuple[str, list[dict[str, Any]]]] = []
        stream_manifests: list[dict[str, Any]] = []
        for (
            stream_name,
            stream_source,
            stream_target,
            data_type,
            include_resources,
        ) in stream_specs:
            print(f"collecting {stream_name}", flush=True)
            events, stream_manifest = collect_event_stream(
                client,
                report_code=report_code,
                fight_id=fight_id,
                fight_start=sample_window["start_time"],
                fight_end=sample_window["end_time"],
                stream_name=stream_name,
                source_id=stream_source,
                target_id=stream_target,
                data_type=data_type,
                include_resources=include_resources,
                page_limit=int(collection.get("event_page_limit", 10000)),
                max_pages=int(collection.get("max_pages_per_stream", 200)),
                reserve_points=float(collection.get("rate_limit_reserve_points", 100)),
            )
            streams.append((stream_name, events))
            stream_manifests.append(stream_manifest)

        destination = write_sample(
            output_root=args.output,
            config=config,
            report=report,
            fight=fight,
            sample_window=sample_window,
            actor_resolution=resolution,
            talent_import_code=talent_import_code,
            streams=streams,
            stream_manifests=stream_manifests,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "output": str(destination),
                    "source_id": source_id,
                    "owned_pet_ids": owned_pets,
                    "stream_count": len(streams),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ValueError, WCLRequestError, OSError, json.JSONDecodeError) as exc:
        print(f"report sample collector failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
