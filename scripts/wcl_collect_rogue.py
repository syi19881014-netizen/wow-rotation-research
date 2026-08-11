#!/usr/bin/env python3

import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
API_URL = "https://www.warcraftlogs.com/api/v2/client"

OUT = Path("data/wcl/rogue")

SPECS = (
    "Assassination",
    "Outlaw",
    "Subtlety",
)


def now():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def save(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_token(client_id, client_secret):
    auth = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
        }
    ).encode()

    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
            "User-Agent": (
                "wow-rotation-research/0.2"
            ),
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        data = json.loads(
            response.read().decode()
        )

    access_token = data.get(
        "access_token"
    )

    if not access_token:
        raise RuntimeError(
            "OAuth succeeded but no "
            "access_token was returned"
        )

    return access_token


def gql(
    access_token,
    query,
    variables=None,
):
    payload = json.dumps(
        {
            "query": query,
            "variables": (
                variables or {}
            ),
        }
    ).encode()

    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Content-Type": (
                "application/json"
            ),
            "User-Agent": (
                "wow-rotation-research/0.2"
            ),
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:
        data = json.loads(
            response.read().decode()
        )

    if data.get("errors"):
        raise RuntimeError(
            "GraphQL error: "
            + json.dumps(
                data["errors"],
                ensure_ascii=False,
            )
        )

    return data.get(
        "data",
        {},
    )


WORLD_QUERY = (
    "query { "
    "rateLimitData { "
    "limitPerHour "
    "pointsSpentThisHour "
    "pointsResetIn "
    "} "
    "worldData { "
    "expansions { "
    "id "
    "name "
    "zones { "
    "id "
    "name "
    "frozen "
    "encounters { "
    "id "
    "name "
    "} "
    "} "
    "} "
    "} "
    "}"
)


RANK_QUERY = (
    "query RogueRankings("
    "$encounterID: Int!"
    ") { "
    "worldData { "
    "encounter("
    "id: $encounterID"
    ") { "
    "id "
    "name "
    "zone { "
    "id "
    "name "
    "frozen "
    "} "

    "assassination: "
    "characterRankings("
    "className: \"Rogue\", "
    "specName: \"Assassination\", "
    "page: 1, "
    "includeCombatantInfo: true"
    ") "

    "outlaw: "
    "characterRankings("
    "className: \"Rogue\", "
    "specName: \"Outlaw\", "
    "page: 1, "
    "includeCombatantInfo: true"
    ") "

    "subtlety: "
    "characterRankings("
    "className: \"Rogue\", "
    "specName: \"Subtlety\", "
    "page: 1, "
    "includeCombatantInfo: true"
    ") "

    "} "
    "} "

    "rateLimitData { "
    "limitPerHour "
    "pointsSpentThisHour "
    "pointsResetIn "
    "} "
    "}"
)


def nonempty(value):
    if value is None:
        return False

    if isinstance(
        value,
        list,
    ):
        return bool(value)

    if isinstance(
        value,
        dict,
    ):
        if not value:
            return False

        for key, item in (
            value.items()
        ):
            lower = key.lower()

            if (
                lower
                in (
                    "rankings",
                    "entries",
                    "data",
                )
                and isinstance(
                    item,
                    list,
                )
                and item
            ):
                return True

            if (
                lower
                in (
                    "count",
                    "total",
                )
                and isinstance(
                    item,
                    (
                        int,
                        float,
                    ),
                )
                and item > 0
            ):
                return True

        return any(
            nonempty(item)
            for item
            in value.values()
        )

    return False


def main():
    client_id = (
        os.environ.get(
            "WCL_CLIENT_ID",
            "",
        ).strip()
    )

    client_secret = (
        os.environ.get(
            "WCL_CLIENT_SECRET",
            "",
        ).strip()
    )

    status = {
        "ok": False,
        "checked_at_utc": now(),
        "collector": (
            "rogue_rankings_v0.2"
        ),
        "specs": list(SPECS),
        "secrets_exposed": False,
    }

    if (
        not client_id
        or not client_secret
    ):
        status.update(
            stage="secrets",
            message=(
                "Missing WCL_CLIENT_ID "
                "or WCL_CLIENT_SECRET"
            ),
        )

        save(
            OUT
            / "collector_status.json",
            status,
        )

        return 2

    try:
        access_token = get_token(
            client_id,
            client_secret,
        )

        world = gql(
            access_token,
            WORLD_QUERY,
        )

        expansions = (
            (
                world.get(
                    "worldData"
                )
                or {}
            ).get(
                "expansions"
            )
            or []
        )

        if not expansions:
            raise RuntimeError(
                "WCL returned "
                "no expansions"
            )

        expansion = max(
            expansions,
            key=lambda item: (
                item.get(
                    "id",
                    -1,
                )
            ),
        )

        zones = [
            zone
            for zone
            in (
                expansion.get(
                    "zones"
                )
                or []
            )
            if (
                zone.get(
                    "encounters"
                )
                or []
            )
        ]

        zones.sort(
            key=lambda item: (
                item.get(
                    "id",
                    -1,
                )
            ),
            reverse=True,
        )

        active_zones = [
            zone
            for zone in zones
            if not zone.get(
                "frozen"
            )
        ]

        candidates = (
            active_zones
            or zones
        )[:3]

        save(
            OUT
            / "discovery"
            / "latest.json",
            {
                "collected_at_utc": now(),

                "expansion": {
                    "id": (
                        expansion.get(
                            "id"
                        )
                    ),
                    "name": (
                        expansion.get(
                            "name"
                        )
                    ),
                },

                "candidate_zones": (
                    candidates
                ),

                "rate_limit_before": (
                    world.get(
                        "rateLimitData"
                    )
                ),
            },
        )

        attempts = []

        found = False

        selected_zone = None

        last_rate = (
            world.get(
                "rateLimitData"
            )
        )

        for zone in candidates:
            zone_found = False

            encounters = (
                zone.get(
                    "encounters"
                )
                or []
            )

            for encounter in encounters:
                data = gql(
                    access_token,
                    RANK_QUERY,
                    {
                        "encounterID": (
                            encounter[
                                "id"
                            ]
                        ),
                    },
                )

                item = (
                    (
                        data.get(
                            "worldData"
                        )
                        or {}
                    ).get(
                        "encounter"
                    )
                    or {}
                )

                last_rate = (
                    data.get(
                        "rateLimitData"
                    )
                    or last_rate
                )

                rankings = {
                    "Assassination": (
                        item.get(
                            "assassination"
                        )
                    ),
                    "Outlaw": (
                        item.get(
                            "outlaw"
                        )
                    ),
                    "Subtlety": (
                        item.get(
                            "subtlety"
                        )
                    ),
                }

                nonempty_specs = [
                    spec
                    for spec, value
                    in rankings.items()
                    if nonempty(
                        value
                    )
                ]

                path = (
                    OUT
                    / "rankings"
                    / str(
                        zone[
                            "id"
                        ]
                    )
                    / (
                        f"{encounter['id']}.json"
                    )
                )

                save(
                    path,
                    {
                        "collected_at_utc": (
                            now()
                        ),

                        "expansion": {
                            "id": (
                                expansion.get(
                                    "id"
                                )
                            ),
                            "name": (
                                expansion.get(
                                    "name"
                                )
                            ),
                        },

                        "zone": {
                            "id": (
                                zone.get(
                                    "id"
                                )
                            ),
                            "name": (
                                zone.get(
                                    "name"
                                )
                            ),
                            "frozen": (
                                zone.get(
                                    "frozen"
                                )
                            ),
                        },

                        "encounter": {
                            "id": (
                                item.get(
                                    "id",
                                    encounter[
                                        "id"
                                    ],
                                )
                            ),
                            "name": (
                                item.get(
                                    "name",
                                    encounter.get(
                                        "name"
                                    ),
                                )
                            ),
                        },

                        "rankings": (
                            rankings
                        ),

                        "rate_limit_after_query": (
                            last_rate
                        ),
                    },
                )

                attempts.append(
                    {
                        "zone_id": (
                            zone.get(
                                "id"
                            )
                        ),

                        "zone_name": (
                            zone.get(
                                "name"
                            )
                        ),

                        "encounter_id": (
                            encounter.get(
                                "id"
                            )
                        ),

                        "encounter_name": (
                            item.get(
                                "name",
                                encounter.get(
                                    "name"
                                ),
                            )
                        ),

                        "nonempty_specs": (
                            nonempty_specs
                        ),

                        "file": str(
                            path
                        ),
                    }
                )

                if nonempty_specs:
                    found = True
                    zone_found = True

                time.sleep(
                    0.15
                )

            if zone_found:
                selected_zone = {
                    "id": (
                        zone.get(
                            "id"
                        )
                    ),
                    "name": (
                        zone.get(
                            "name"
                        )
                    ),
                }

                break

        status.update(
            ok=True,
            stage="complete",

            latest_expansion={
                "id": (
                    expansion.get(
                        "id"
                    )
                ),
                "name": (
                    expansion.get(
                        "name"
                    )
                ),
            },

            selected_zone_with_data=(
                selected_zone
            ),

            found_nonempty_rankings=(
                found
            ),

            attempts=attempts,

            rate_limit_after=(
                last_rate
            ),

            message=(
                "Rogue ranking data "
                "collected successfully."
                if found
                else (
                    "WCL API worked, "
                    "but no non-empty Rogue "
                    "rankings were found in "
                    "the newest candidate zones."
                )
            ),
        )

        save(
            OUT
            / "collector_status.json",
            status,
        )

        print(
            json.dumps(
                status,
                ensure_ascii=False,
                indent=2,
            )
        )

        return 0

    except urllib.error.HTTPError as error:
        body = (
            error.read().decode(
                errors="replace"
            )
            if hasattr(
                error,
                "read",
            )
            else ""
        )

        status.update(
            stage="http",
            message=(
                f"HTTP {error.code}"
            ),
            details=(
                body[:2000]
            ),
        )

    except Exception as error:
        status.update(
            stage="exception",
            message=str(error),
        )

    save(
        OUT
        / "collector_status.json",
        status,
    )

    print(
        json.dumps(
            status,
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
