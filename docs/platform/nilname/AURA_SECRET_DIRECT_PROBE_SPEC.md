# NilName 12.1 Aura Capability Probe Spec

> Status: SPEC ONLY — not runtime confirmed  
> Updated: 2026-08-17 after the Curse of Ula'tek Aura-refactor audit

## Goal

Determine which Aura access paths actually work in the user's **current WoW 12.1 + NilName build**.

This spec no longer assumes that the pre-12.1 BadRotations path (`GetAuraDataByIndex -> secretunwrap`) survives the 12.1 Aura refactor. Blizzard changed the Aura interface model, and current ordinary-addon implementations show that index/slot/auraInstanceID reads may hard-error while Auras are secret.

The probe must establish a capability matrix for:

```text
ordinary WoW execution
vs
NilName privileged execution
vs
any NN-native Aura provider discovered at runtime
```

First version is read-only: **no automatic casting, no profession rotation, no Sirus Core, no PrimeKit dependency, no raw ObjectField offsets**.

## Environment

1. Temporarily move/disable `_PrimeKitCore.nn` so it cannot auto-load.
2. Load only the probe.
3. Record WoW build, locale, specialization and any safely available NilName build/version identifier.
4. Run out-of-combat and in-combat/restricted phases.
5. Use `pcall/xpcall` around every call that may hard-error.
6. Never concatenate, compare or perform arithmetic on a value until Secret behavior is known.

## Phase A — Runtime namespace discovery

Check only existence/type first:

- script vararg `nn = ...`
- `C_Timer`
- `C_Timer.Nn`
- `C_Timer.Nn.issecretvalue`
- `C_Timer.Nn.secretunwrap`
- `_G.issecretvalue` / other already-present official Secret detector locations if exposed by the current client

Also enumerate the **names** of safe NilName runtime namespaces/tables looking for explicit Aura-related providers/helpers. Do not guess signatures or invoke unknown functions simply because their name contains `Aura`.

Output example:

```text
[NN12_AURA] phase=A symbol=C_Timer.Nn type=table
[NN12_AURA] phase=A symbol=secretunwrap type=function
[NN12_AURA] phase=A discovered_namespace=<name> type=<type>
```

## Phase B — Restriction-state baseline

If available, record the current Aura restriction state using the game-provided restriction/Secret API (for example a current `C_Secrets` capability), protected by `pcall`.

Run each meaningful Aura test twice:

```text
state=OUT_OF_COMBAT_OR_UNRESTRICTED
state=IN_COMBAT_OR_RESTRICTED
```

Do not assume `InCombatLockdown()` and Aura secrecy are identical; record both if available.

## Phase C — Ordinary WoW Aura API control group

The control group establishes what ordinary addon execution can do in this exact build.

### C1. Index/enumeration family

Probe existence and call behavior for currently present APIs such as:

- `C_UnitAuras.GetAuraDataByIndex`
- `C_UnitAuras.GetAuraDataBySlot`
- `C_UnitAuras.GetAuraDataByAuraInstanceID`
- Aura-slot enumeration APIs if present

Expected from public 12.1 addon evidence: some/all of these may hard-error while Auras are secret. Record the error; that is a useful result, not a probe failure.

### C2. Identifier family

Probe currently present APIs such as:

- `C_UnitAuras.GetUnitAuraBySpellID`
- `C_UnitAuras.GetAuraDataBySpellName`

Do not assume these return all Auras. Record whether a known Aura is:

- returned as a table;
- absent/nil;
- returned with Secret fields;
- usable only when Blizzard marks that Aura non-secret.

### C3. Field matrix

For every returned AuraData table, inspect these fields safely if present:

- `spellId`
- `name`
- `applications`
- `duration`
- `expirationTime`
- `sourceUnit`
- `isHelpful`
- `isHarmful`
- `dispelName`
- `isStealable`
- `auraInstanceID`
- `points` / nested value fields

For each field record `type`, Secret status, and whether it can be consumed by ordinary Lua logic.

## Phase D — NilName privileged execution of the same calls

Repeat Phase C through the actual NilName privileged environment/calling convention confirmed by runtime discovery.

Important: do not assume `Unlock(C_UnitAuras...)` is equivalent to executing inside `C_Timer.Nn`, and do not assume either changes Secret restrictions. Test each confirmed mechanism separately.

For each API compare:

```text
ordinary_call_result
NN_privileged_call_result
```

Possible outcomes:

- ordinary hard-error, NN returns AuraData;
- both return AuraData but NN can normalize Secret fields;
- both are identifier-only;
- both blocked;
- NN exposes a different Aura API entirely.

## Phase E — Secret detector/unwrap behavior

Only if the current NN runtime actually exposes a Secret detector/unwrap primitive.

### E1. Normal-value sanity

Protected-call the helper with controlled ordinary values:

- nil
- boolean
- integer
- float
- string

Record no-op/error behavior.

### E2. Returned Secret scalar

For an Aura field already proven Secret:

1. detect Secret state;
2. call unwrap only when appropriate;
3. record unwrapped type;
4. test whether the result can safely participate in:
   - equality;
   - numeric comparison;
   - arithmetic for `expirationTime - now` when numeric;
   - table-key/index use when string/token-like.

Never blindly call `secretunwrap(auraTable)`. Tables and fields are separate capabilities.

## Phase F — `UNIT_AURA` event behavior

Register `UNIT_AURA` and record:

- whether the unit argument remains ordinary/usable;
- payload type/shape;
- which payload fields are Secret/unreadable;
- whether the event can be used only as an invalidation signal in restricted mode.

Do not depend on old delta payload semantics until this probe proves them.

If the payload is unusable but unit identity remains usable, record:

```text
EVENT_INVALIDATION_ONLY
```

because Sirus may re-read only its tracked Aura identifiers on that unit.

## Phase G — Representative Aura classes

Use manually triggered/observed effects; the probe does not cast them.

Test at least:

1. `SELF_BUFF` — ordinary deterministic player buff
2. `SELF_PROC` — proc/stacking player buff important to an APL
3. `TARGET_DEBUFF` — player's debuff on current target
4. `TARGET_BUFF` — buff on current hostile target if reproducible
5. `NON_TARGET_DEBUFF` — player's debuff on a second nearby enemy without making it the current target

For Outlaw a later run may use representative proc/buff spell IDs from the project rotation module, but the generic probe must not hard-code profession logic as its foundation.

## Phase H — NilName Object coverage

After Object Manager / UnitRef bridging is separately confirmed:

1. obtain at least two nearby attackable NN objects;
2. identify the current target and a non-current enemy;
3. test the successful Aura API/provider against both references;
4. verify that the non-current object's Aura state can return ordinary framework-consumable values.

Minimum multi-target success fields:

```text
exists/up
applications/stacks
expirationTime/remains
source/source-is-player
```

This phase determines whether Sirus can support genuine per-object multidot logic.

## Phase I — NN-native Aura provider discovery

If Phase A exposes an explicit NN-specific Aura API/namespace, make a **separate** capability branch for it.

Rules:

- first log function/table names and types;
- do not infer parameters from names;
- use official docs or safe runtime introspection/sample usage before calling;
- compare results against manually known Aura state and the WoW API control group.

A successful NN-native provider can become the primary 12.1 source even if Blizzard index APIs remain blocked.

## Phase J — Other Secret-sensitive combat inputs

Aura is not the only possible compatibility surface. Separately probe:

### `C_Spell`

- spell info
- cooldown
- charges
- usable/range where current APIs exist

### Combat Log

- `CombatLogGetCurrentEventInfo()` return positions needed by Sirus
- source/dest GUID
- spell ID
- damage/event identifiers

### Health / TTD

- `UnitHealth(target)`
- `UnitHealthMax(target)`
- same reads for a confirmed non-current NN object

For each, record ordinary vs NN-privileged result and Secret normalization requirements.

## Logging schema

One structured record per API/field test:

```text
[NN12_AURA]
phase=<A-J>
restriction=<UNRESTRICTED|RESTRICTED|UNKNOWN>
execution=<WOW_NORMAL|NN_ENV|NN_UNLOCK|NN_NATIVE>
api=<name>
unit=<token/object-kind>
aura_class=<SELF_BUFF|SELF_PROC|TARGET_DEBUFF|TARGET_BUFF|NON_TARGET_DEBUFF|NA>
field=<field-or-return-index>
call_ok=<true|false>
raw_type=<type|na>
is_secret=<true|false|unknown>
unwrap_ok=<true|false|na>
unwrapped_type=<type|na>
operation_test=<pass|fail|na>
classification=<result-class>
error=<sanitized-error|none>
```

Do not log account IDs, session tokens, license tokens or HTTP credentials.

## Result classifications

Use per-capability classifications, not one global PASS/FAIL:

- `NORMAL_AVAILABLE`
- `EXPECTED_BLOCKED_NORMAL`
- `NN_PRIVILEGED_INDEX`
- `NN_PRIVILEGED_IDENTIFIER`
- `NN_NATIVE_PROVIDER`
- `SECRET_RETURNED_UNWRAPPED`
- `SECRET_RETURNED_NOT_CONSUMABLE`
- `IDENTIFIER_ONLY`
- `EVENT_INVALIDATION_ONLY`
- `NO_DIRECT_PATH`
- `UNKNOWN`

## Sirus decision rule

Only after the matrix exists should Sirus choose provider precedence. Example:

```text
if NN_NATIVE_PROVIDER covers required fields:
    use NN native provider
elseif NN_PRIVILEGED_IDENTIFIER covers tracked Aura set:
    use identifier provider + tracked cache
elseif NN_PRIVILEGED_INDEX is proven safe/current:
    use privileged enumeration provider
elseif ordinary identifier path covers the specific non-secret Aura:
    use limited ordinary provider
else:
    use event/mechanic reconstruction only for explicitly supported effects
```

Do not promote March/April 2026 BadRotations index wrappers to current production dependencies without this probe.

## Minimal “12.1 Aura solved” gate

The current NilName build must provide stable combat/restricted-mode framework state for:

```text
player proc:      Up + Stacks + Remains
current target:   Debuff Up + Remains + Source
non-current mob:  Debuff Up + Remains + Source
```

and survive refresh/removal/target swap/reload without PrimeKit dependency.

Until then:

```text
12.1_NN_AURA_SOLUTION = IMPLEMENTATION_UNKNOWN
```

## Codex implementation constraints

- implement this spec clean-room;
- do not copy BadRotations GPL code;
- do not load/depend on PrimeKit;
- do not auto-cast;
- do not implement Sirus Core yet;
- do not use raw `ObjectField` offsets;
- do not invent undocumented function signatures;
- all risky calls use `pcall/xpcall` and fail closed;
- preserve ordinary-vs-NN comparison in the logs.
