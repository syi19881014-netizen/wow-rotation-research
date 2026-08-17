# NilName support guidance — non-current object Aura access

> Date: 2026-08-18
> Evidence class: SUPPORT_GUIDANCE_CONFIRMED / NOT LOCAL_RUNTIME_CONFIRMED

The user asked NilName support whether a non-current target/object can be checked for Aura state under WoW 12.1 restrictions.

Support response #1:

> "Yes, you can use setnpcobject and subsequently check for your aura ids on that object pointer, and if they return secrets which they most probably will, unwrap the secret values."

Follow-up response #2, after asking whether normal Aura fields such as stacks/duration/expiration/source remain usable through that path:

> "Yes, all normal aura data should be in presentable form after that path."

## Interpretation

This is the strongest current direct support evidence for the multi-target Aura route needed by Sirus:

```text
NN object pointer
    -> SetNPCObject(object)
    -> query the tracked Aura IDs on the exposed NPC/object bridge
    -> if returned values are Secret, unwrap them
    -> normal Aura data becomes presentable/consumable
    -> normalize into Aura state for rotation logic
```

The important new point is that the enemy does not need to be the player's current target merely to inspect Aura state that the framework is tracking.

## What is support-confirmed

- `SetNPCObject` is the recommended bridge for a non-current NN object.
- After binding the object, tracked Aura IDs can be checked.
- Returned values may be Secret under 12.1.
- Secret values should be unwrapped before the framework consumes them.
- NilName support explicitly states that **all normal Aura data should be presentable after this path**.

For Sirus, this is sufficient support-level evidence to expect ordinary Aura fields such as:

- existence/up state;
- applications/stacks;
- duration;
- expirationTime/remains;
- source/ownership;
- normal spell/name/id metadata where exposed by the chosen Aura query.

This does not mean every Blizzard/internal/private Aura field is guaranteed, only that the normal Aura data used by ordinary Aura logic is expected to be presentable after the `SetNPCObject -> Aura query -> Secret unwrap` path.

## What remains runtime-only

Local probe still needs to determine implementation details and stability:

- whether the query uses the `npc` unit token or accepts the object pointer directly;
- exact supported by-spellID/by-name API path;
- exact field names/shapes in the current 12.1 build;
- refresh/expiry behavior;
- rapid `SetNPCObject` rebinding behavior across multiple enemies;
- stale-state behavior when objects disappear/despawn;
- performance when scanning multiple enemies each pulse.

Current capability labels:

```text
NN_NON_TARGET_AURA_ACCESS       = SUPPORT_GUIDANCE_CONFIRMED
NN_NON_TARGET_NORMAL_AURA_DATA  = SUPPORT_GUIDANCE_CONFIRMED
NN_NON_TARGET_AURA_REMAINS      = SUPPORT_GUIDANCE_CONFIRMED_PENDING_RUNTIME_VALIDATION
NN_MULTI_TARGET_DOT_ENGINE      = SUPPORT_CONFIRMED_FEASIBLE_PENDING_RUNTIME_VALIDATION
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
A Rupture: up=true  stacks=1  remains=17.2  source=player
B Rupture: up=true  stacks=1  remains=8.7   source=player
C Rupture: up=false stacks=0  remains=0
```

without retargeting A/B/C for the read itself.

## Design consequence

Assuming the local runtime matches support guidance, the preferred Sirus multi-target DoT route becomes:

```text
Objects()/ObjectManager
    -> tracked enemy object set
    -> SetNPCObject(object)
    -> query only tracked Aura spellIDs
    -> Secret unwrap
    -> per-object Aura cache
    -> exact remains/stacks/source for APL decisions
```

This should be preferred over reconstructing non-current DoT duration purely from cast history whenever the direct path is stable and performant.
