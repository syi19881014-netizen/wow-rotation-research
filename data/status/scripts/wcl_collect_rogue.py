
        discovery = {
            "checked_at_utc": utc_now(),
            "latest_expansion": {
                "id": latest_expansion.get("id"),
                "name": latest_expansion.get("name"),
            },
            "candidate_zones": candidate_zones,
            "rate_limit_before": world.get("rateLimitData"),
        }
        write_json(OUT_ROOT / "discovery" / "latest.json", discovery)

        attempts = []
        any_nonempty = False
        selected_zone = None
        last_rate = world.get("rateLimitData")

        for zone in candidate_zones:
            zone_any = False
            zone_id = zone["id"]

            for enc in zone.get("encounters") or []:
                encounter_id = enc["id"]
                data = collect_encounter_rankings(token, encounter_id)
                encounter = ((data.get("worldData") or {}).get("encounter") or {})
                last_rate = data.get("rateLimitData") or last_rate

                out = {
                    "collected_at_utc": utc_now(),
                    "expansion": {
                        "id": latest_expansion.get("id"),
                        "name": latest_expansion.get("name"),
                    },
                    "zone": {
                        "id": zone_id,
                        "name": zone.get("name"),
                        "frozen": zone.get("frozen"),
                    },
                    "encounter": {
                        "id": encounter.get("id", encounter_id),
                        "name": encounter.get("name", enc.get("name")),
                    },
                    "rankings": {
                        "Assassination": encounter.get("assassination"),
                        "Outlaw": encounter.get("outlaw"),
                        "Subtlety": encounter.get("subtlety"),
                    },
                    "rate_limit_after_query": last_rate,
                }

                path = OUT_ROOT / "rankings" / str(zone_id) / f"{encounter_id}.json"
                write_json(path, out)

                nonempty_specs = [
                    spec for spec, value in out["rankings"].items()
                    if looks_nonempty(value)
                ]
                if nonempty_specs:
                    zone_any = True
                    any_nonempty = True

                attempts.append({
                    "zone_id": zone_id,
                    "zone_name": zone.get("name"),
                    "encounter_id": encounter_id,
                    "encounter_name": out["encounter"]["name"],
                    "nonempty_specs": nonempty_specs,
                    "file": str(path),
                })
                time.sleep(0.15)

            if zone_any:
                selected_zone = {"id": zone_id, "name": zone.get("name")}
                break

        status.update({
            "ok": True,
            "stage": "complete",
            "latest_expansion": {
                "id": latest_expansion.get("id"),
                "name": latest_expansion.get("name"),
            },
            "selected_zone_with_data": selected_zone,
            "found_nonempty_rankings": any_nonempty,
            "attempts": attempts,
            "rate_limit_after": last_rate,
            "secrets_exposed": False,
        })

        if not any_nonempty:
            status["message"] = (
                "API worked, but no non-empty Rogue rankings were found in the newest "
                "candidate zones yet. This can be normal before the new season/raid has populated logs."
            )
        else:
            status["message"] = (
                "Rogue ranking data collected successfully. Next step: inspect report/fight "
                "references and descend into casts/resources/buffs."
            )

        write_json(OUT_ROOT / "collector_status.json", status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0

    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if hasattr(e, "read") else ""
        status.update({"stage": "http", "message": f"HTTP {e.code}", "details": body[:2000]})
    except Exception as e:
        status.update({"stage": "exception", "message": str(e)})

    write_json(OUT_ROOT / "collector_status.json", status)
    print(json.dumps(status, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
