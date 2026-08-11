#!/usr/bin/env python3

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


WCL_TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
WCL_API_URL = "https://www.warcraftlogs.com/api/v2/client"

OUT_ROOT = Path("data/wcl/rogue")

SPECS = [
    "Assassination",
    "Outlaw",
    "Subtlety",
]

MAX_CANDIDATE_ZONES = 5


def utc_now():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_token(client_id: str, client_secret: str) -> str:
    auth = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
        }
    ).encode()

    request = urllib.request.Request(
        WCL_TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "wow-rotation-research/0.1",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        payload = json.loads(
            response.read().decode()
        )

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(
            "WCL OAuth returned no access_token"
        )

    return token


def graphql(
    token: str,
    query: str,
    variables=None,
):
    payload = json.dumps(
        {
            "query": query,
            "variables": variables or {},
        }
    ).encode()

    request = urllib.request.Request(
        WCL_API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "wow-rotation-research/0.1",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:
        result = json.loads(
            response.read().decode()
        )

    if result.get("errors"):
        raise RuntimeError(
            "GraphQL error: "
            + json.dumps(
                result["errors"],
                ensure_ascii=False,
            )
        )

    return result.get("data", {})


def discover_world(token: str):
    query = """
    query {
      rateLimitData {
        limitPerHour
        pointsSpentThisHour
        pointsResetIn
      }

      worldData {
        expansions {
          id
          name

          zones {
            id
            name
            frozen

            difficulties {
              id
              name
              sizes
            }

            encounters {
              id
              name
              journalID
            }
          }
        }
      }
    }
    """

    return graphql(
        token,
        query,
    )


def looks_nonempty(value):
    if value is None:
        return False

    if isinstance(value, list):
        return len(value) > 0

    if isinstance(value, dict):
        if not value:
            return False

        for key, item in value.items():
            lower_key = key.lower()

            if (
                lower_key
                in {
                    "rankings",
                    "entries",
                    "data",
                }
                and isinstance(item, list)
                and item
            ):
                return True

            if (
                lower_key
                in {
                    "total",
                    "count",
                }
                and isinstance(
                    item,
                    (int, float),
                )
                and item > 0
            ):
                return True

        return any(
            looks_nonempty(item)
            for item in value.values()
        )

    return False


def collect_encounter_rankings(
    token: str,
    encounter_id: int,
):
    query = """
    query RogueRankings($encounterID: Int!) {
      worldData {
        encounter(id: $encounterID) {
          id
          name

          zone {
            id
            name
            frozen
          }

          assassination: characterRankings(
            className: "Rogue"
            specName: "Assassination"
            page: 1
            includeCombatantInfo: true
          )

          outlaw: characterRankings(
            className: "Rogue"
            specName: "Outlaw"
            page: 1
            includeCombatantInfo: true
          )

          subtlety: characterRankings(
            classN
