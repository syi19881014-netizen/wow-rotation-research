# NilName support guidance — non-current object Aura access

> Date: 2026-08-18
> Evidence class: SUPPORT_GUIDANCE_CONFIRMED / NOT LOCAL_RUNTIME_CONFIRMED

The user asked NilName support whether a non-current target/object can be checked for Aura state under WoW 12.1 restrictions.

Support response:

> "Yes, you can use setnpcobject and subsequently check for your aura ids on that object pointer, and if they return secrets which they most probably will, unwrap the secret values."

## Interpretation

This is the strongest current direct support evidence for the multi-target Aura route needed by Sirus:

```text
NN object pointer
    -> SetNPCObject(object)
    -> query the tracked Aura IDs on the exposed NPC/object bridge
    -> if returned scalars are Secret, unwrap them
    -> normalize into Aura state for rotation logic
```

The important new point is that the enemy does not need to be the player's current target merely to inspect the Aura IDs that the framework is tracking.

## What is support-confirmed

- `SetNPCObject` is the recommended bridge for a non-current NN object.
- After binding the object, tracked Aura IDs can be checked.
- Returned values may be Secret under 12.1.
- Secret values should be unwrapped before the framework consumes them.

## What remains runtime-only

The support reply does not name the exact Aura query function or guarantee every field. Local probe must still determine:

- whether the query uses the `npc` unit token or accepts the object pointer directly;
- exact supported by-spellID/by-name API path;
- existence/up state;
- applications/stacks;
- duration;
- expirationTime/remains;
- sourceUnit / ownership;
- behavior across refresh, expiry and rapid `SetNPCObject` rebinding;
- performance when scanning multiple enemies each pulse.

Current capability labels:

```text
NN_NON_TARGET_AURA_ACCESS  = SUPPORT_GUIDANCE_CONFIRMED
NN_NON_TARGET_AURA_REMAINS = HIGH_CONFIDENCE_PENDING_LOCAL_PROBE
NN_MULTI_TARGET_DOT_ENGINE = FEASIBLE_PENDING_LOCAL_PROBE
```

## P0 runtime proof

Use two or three training dummies. Apply Rupture/Garrote manually, target a different dummy, then for each stored NN object pointer:

```text
SetNPCObject(object)
-> query tracked Aura spellID
-> detect/unwrap Secret fields
-> record up/stacks/duration/expiration/source
```

Success requires independent non-current-object state such as:

```text
A Rupture: up=true  remains=17.2
B Rupture: up=true  remains=8.7
C Rupture: up=false remains=0
```

without retargeting A/B/C for the read itself.
