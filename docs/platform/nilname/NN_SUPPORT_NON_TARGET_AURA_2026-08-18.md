# NilName support guidance — non-current object Aura access

> Date: 2026-08-18
> Evidence class: SUPPORT_GUIDANCE_CONFIRMED / NOT LOCAL_RUNTIME_CONFIRMED

The user asked NilName support whether a non-current target/object can be checked for Aura state under WoW 12.1 restrictions.

Support response #1:

> "Yes, you can use setnpcobject and subsequently check for your aura ids on that object pointer, and if they return secrets which they most probably will, unwrap the secret values."

Follow-up response #2, after asking whether normal Aura fields such as stacks/duration/expiration/source remain usable through that path:

> "Yes, all normal aura data should be in presentable form after that path."

Support response #3 to the broader 12.1 question, including non-current Objects(), spellID lookup, applications/duration/expirationTime/sourceUnit, and the supported path:

> "yes it can, should be able to use Unlock and pass down"

## Interpretation

This is the strongest current direct support evidence for the multi-target Aura route needed by Sirus.

There are now two support-described access styles that may be related rather than mutually exclusive:

```text
A) NN object pointer
   -> SetNPCObject(object)
   -> query tracked Aura IDs
   -> unwrap Secret values

B) call the relevant Aura function through Unlock(...)
   -> pass the non-current object / required unit argument down to that function
   -> unwrap Secret values if returned
```

The third response strongly suggests that `Unlock` itself can be used as the privileged call bridge, with the target object/unit arguments passed through to the underlying Aura query. It does **not** yet specify the exact function signature, so we must not hard-code a guessed call such as `Unlock(C_UnitAuras.GetUnitAuraBySpellID, object, spellID)` until runtime or support confirms the concrete argument form.

The important capability conclusion is unchanged and strengthened: the enemy does not need to be the player's current target merely to inspect Aura state that the framework is tracking.

## What is support-confirmed

- NilName can query Aura state on a non-current object returned by `Objects()`.
- `SetNPCObject` is one explicitly recommended bridge for a non-current NN object.
- `Unlock` is also explicitly described by support as a path that can be used while passing the required object/unit arguments down to the Aura query.
- Tracked Aura IDs can be checked after establishing the privileged/object path.
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

This does not mean every Blizzard/internal/private Aura field is guaranteed, only that the normal Aura data used by ordinary Aura logic is expected to be presentable after the privileged query + Secret unwrap path.

## What remains runtime-only

Local probe still needs to determine implementation details and stability:

- whether `Unlock` can directly pass an NN object pointer to the chosen Aura function or first requires `SetNPCObject`;
- whether the query uses the `npc` unit token after `SetNPCObject`;
- exact supported by-spellID/by-name Aura function;
- exact `Unlock` call signature and argument order;
- exact field names/shapes in the current 12.1 build;
- refresh/expiry behavior;
- rapid object rebinding / multi-object iteration behavior;
- stale-state behavior when objects disappear/despawn;
- performance when scanning multiple enemies each pulse.

Current capability labels:

```text
NN_NON_TARGET_AURA_ACCESS       = SUPPORT_GUIDANCE_CONFIRMED
NN_UNLOCK_AURA_BRIDGE           = SUPPORT_GUIDANCE_CONFIRMED_SIGNATURE_PENDING
NN_NON_TARGET_NORMAL_AURA_DATA  = SUPPORT_GUIDANCE_CONFIRMED
NN_NON_TARGET_AURA_REMAINS      = SUPPORT_GUIDANCE_CONFIRMED_PENDING_RUNTIME_VALIDATION
NN_MULTI_TARGET_DOT_ENGINE      = SUPPORT_CONFIRMED_FEASIBLE_PENDING_RUNTIME_VALIDATION
```

## P0 runtime proof

Use two or three training dummies. Apply Rupture/Garrote manually, target a different dummy, then test both support-described paths where applicable:

```text
Path A:
SetNPCObject(object)
-> query tracked Aura spellID
-> detect/unwrap Secret fields

Path B:
Unlock(<confirmed Aura function>, <confirmed object/unit args>, spellID)
-> detect/unwrap Secret fields
```

Record:

```text
up / applications / duration / expirationTime / sourceUnit
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
    -> privileged Aura query via confirmed Unlock/Object bridge
    -> Secret unwrap
    -> per-object Aura cache
    -> exact remains/stacks/source for APL decisions
```

This should be preferred over reconstructing non-current DoT duration purely from cast history whenever the direct path is stable and performant.
