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

Support response #4, after explicitly asking whether the NN object from `Objects()` can be passed directly through `Unlock` versus first mapping it with `SetNPCObject(object)` and then using the `npc` token:

> "both work"
>
> "object shouldnt taint"
>
> "but if it does"
>
> "use setnpc"
>
> "but it shouldnt"

## Interpretation

This is the strongest current direct support evidence for the multi-target Aura route needed by Sirus.

NilName support now explicitly confirms two valid access styles:

```text
A) Direct object path [preferred]
   NN object pointer from Objects()
   -> Unlock(<Aura function>, object, ...)
   -> query tracked Aura ID
   -> unwrap Secret values if returned

B) SetNPCObject fallback
   NN object pointer
   -> SetNPCObject(object)
   -> use the mapped `npc` unit token in the Aura query through Unlock
   -> unwrap Secret values if returned
```

Support says **both work**. They further state the direct NN object **should not taint**; if it does in a particular call/path, use `SetNPCObject` as the fallback, though they do not expect that to be necessary normally.

This resolves the earlier uncertainty over whether the direct object must first be converted to the `npc` token. At support-guidance level, it does not: direct object pass-through is expected to work, with `SetNPCObject` retained as a compatibility/taint fallback.

The enemy therefore does not need to be the player's current target merely to inspect Aura state that the framework is tracking.

## What is support-confirmed

- NilName can query Aura state on a non-current object returned by `Objects()`.
- A non-current NN object can be passed directly through the privileged `Unlock` path to the relevant Aura query.
- `SetNPCObject(object)` + `npc` token is also valid and is the recommended fallback if the direct object path taints/fails.
- Support expects the direct object itself not to taint.
- Tracked Aura IDs can be checked after establishing either privileged/object path.
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

- exact supported by-spellID/by-name Aura function in the user's current Retail 12.1 build;
- exact `Unlock` call signature and argument order for that Aura function;
- whether any particular Aura API unexpectedly taints/errors with a direct NN object;
- exact field names/shapes in the current 12.1 build;
- refresh/expiry behavior;
- multi-object iteration behavior under load;
- stale-state behavior when objects disappear/despawn;
- performance when scanning multiple enemies each pulse.

Current capability labels:

```text
NN_NON_TARGET_AURA_ACCESS       = SUPPORT_GUIDANCE_CONFIRMED
NN_DIRECT_OBJECT_AURA_PATH      = SUPPORT_GUIDANCE_CONFIRMED_PREFERRED
NN_SETNPC_AURA_FALLBACK         = SUPPORT_GUIDANCE_CONFIRMED
NN_UNLOCK_AURA_BRIDGE           = SUPPORT_GUIDANCE_CONFIRMED_SIGNATURE_PENDING
NN_NON_TARGET_NORMAL_AURA_DATA  = SUPPORT_GUIDANCE_CONFIRMED
NN_NON_TARGET_AURA_REMAINS      = SUPPORT_GUIDANCE_CONFIRMED_PENDING_RUNTIME_VALIDATION
NN_MULTI_TARGET_DOT_ENGINE      = SUPPORT_CONFIRMED_FEASIBLE_PENDING_RUNTIME_VALIDATION
```

## P0 runtime proof

Use two or three training dummies. Apply Rupture/Garrote manually, target a different dummy, then test the direct object path first and fall back to SetNPCObject only if required:

```text
Preferred path:
Unlock(<confirmed Aura function>, object, spellID / required args)
-> detect/unwrap Secret fields
-> record up/stacks/duration/expiration/source

Fallback path if direct object taints/errors:
SetNPCObject(object)
-> Unlock(<confirmed Aura function>, "npc", spellID / required args)
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
    -> direct privileged Aura query via Unlock(object, ...)
    -> Secret unwrap
    -> per-object Aura cache
    -> exact remains/stacks/source for APL decisions

If direct object access taints/errors for a particular API:
    -> SetNPCObject(object)
    -> query through `npc` token
```

This should be preferred over reconstructing non-current DoT duration purely from cast history whenever the direct path is stable and performant.
