# NilName 12.1 Aura Ecosystem Cross-Validation

Date: 2026-08-17
Status: Research baseline; external evidence only until local runtime probe

## Scope

This audit searches the publicly discoverable NilName ecosystem for frameworks/rotation products that run on NilName and asks one narrow question: how do they make WoW 12.1/Midnight Aura data usable by rotation logic?

Important limitation: most commercial frameworks are closed/protected. “All frameworks” here means all publicly discoverable candidates plus every implementation for which code or sufficiently specific release history could be audited. Closed-source products are listed but their Aura internals are not guessed.

## Evidence classes

- `CODE_CONFIRMED`: public source shows the Aura implementation.
- `RELEASE_HISTORY_CONFIRMED`: protected build, but public release history records specific Aura/Secret implementation behavior.
- `SUPPORT_CONFIRMED`: NilName support is confirmed, Aura implementation is not public.
- `LOCAL_RUNTIME_CONFIRMED`: reserved for our own NilName client probe; none yet.

## Framework matrix

| Framework / product | NilName use | Aura evidence | Observed 12.1 strategy | Confidence |
|---|---|---|---|---|
| BadRotations | Yes | Public source | Direct `C_UnitAuras` read in NN environment -> guarded Secret-value normalization -> normalized Aura table; proxy/wrapper layer hides Secret handling from framework | `CODE_CONFIRMED` |
| Ascended Rotation Midnight | Yes / NilName-oriented distribution | Protected `.nn`, detailed public release history | Direct Aura table remains framework truth; individual Secret-tainted fields are unwrapped/normalized; later adds unit/aura caches for performance | `RELEASE_HISTORY_CONFIRMED` |
| PrimeKitCore (user-supplied NN package) | Yes | Protected `.nn` only | Unknown | `SUPPORT_CONFIRMED`, implementation unknown |
| Lunar | NilName partner/support | Closed | Unknown | `SUPPORT_CONFIRMED` |
| Clipper | NilName partner/support | Closed | Unknown | `SUPPORT_CONFIRMED` |
| Go Hands Free | NilName partner/support | Closed | Unknown | `SUPPORT_CONFIRMED` |
| NilName in-house rotations | Native | Closed | Unknown | `SUPPORT_CONFIRMED` |
| Baneto / GMR / WD and related partners | NilName partner ecosystem | Closed / bot-oriented | No public 12.1 Aura implementation found | `SUPPORT_CONFIRMED` only |
| Phoenix / Wings and other community-listed products | Community reports of NilName use | No primary implementation found | Unknown | Secondary evidence only; do not use as implementation proof |

## 1. BadRotations: direct code evidence

BadRotations' NilName adapter is the strongest public source because both pre-Midnight and post-Midnight versions are visible.

### Before Midnight support

The older NN adapter simply bridged object references and called:

- `C_UnitAuras.GetAuraDataByIndex(...)`
- `C_UnitAuras.GetBuffDataByIndex(...)`
- `C_UnitAuras.GetDebuffDataByIndex(...)`

There was no Secret-value normalization layer.

### Midnight transition

The 2026-03-27 commit explicitly states `Initial Midnight NN support` and introduces a Secret compatibility layer in the NilName environment. The current adapter enters `C_Timer.Nn` and resolves runtime symbols named:

- `issecretvalue`
- `secretunwrap`

It then defines three levels of normalization:

1. scalar return normalization;
2. generic table field normalization;
3. Aura-specific table normalization, including nested `points` values.

Aura access still uses `C_UnitAuras` directly; the wrapper normalizes Secret-tainted fields before upper framework code consumes the AuraData.

The same adapter also normalizes returns from `C_Spell`, `CombatLogGetCurrentEventInfo()` and selected unit/global APIs. This strongly suggests Secret handling belongs in a platform boundary adapter, not inside every combat subsystem.

### Architecture implication

BadRotations is not reconstructing the ordinary Aura state from spell history as its first-line solution. It treats the direct Aura table as the truth source and normalizes Secret values at the NN adapter boundary.

## 2. Ascended Rotation Midnight: independent corroboration

Ascended is particularly useful because its current distribution is protected, but release notes expose many highly specific Aura bug fixes.

Observed release-history evidence includes:

- v0.1.95: explicitly fixes a failure by unwrapping Secret `sourceUnit` from Aura data before using it as a table key.
- v0.1.246: records that a HasAura fast path broke on “secret-tainted auras” and explicitly removes an incorrect `secretunwrap` call on `GetUnitAuraBySpellID` because that helper returns a table rather than an atomic Secret value.
- v0.1.572: debug mode can display “private auras (decrypted)” and unit data is cached once per pulse.
- later releases add source-filtered Aura cache checks, per-pulse Aura-query caches, and avoidance of unnecessary 40-slot scans.

These details independently reinforce the same design seen in BadRotations:

1. Direct AuraData is available to the framework.
2. Secret taint exists at field/value granularity.
3. Unwrap must be type/Secret aware; blindly unwrapping a table or a non-Secret value is incorrect.
4. `sourceUnit` can itself be Secret and must be normalized before identity/source comparisons.
5. Cache layers are then added for CPU/performance, not because the framework has to infer all Aura state from casts/events.

## 3. Closed frameworks

NilName's official partner ecosystem publicly identifies Lunar, Clipper and Go Hands Free as rotation products/partners. NilName also ships its own in-house rotations. The user-supplied client contains `_PrimeKitCore.nn`, a protected third-party framework.

No public primary source was found that reveals how these products implement Midnight Aura handling. Therefore we intentionally do **not** infer that they use `secretunwrap`, ObjectField offsets, combat-log reconstruction, or any other specific method.

Their practical existence on the current NilName ecosystem is useful only as weak corroboration that 12.1 Aura is solvable in production. It is not implementation evidence.

## 4. Cross-validated model

The strongest evidence from two independent public NilName framework lines converges on this model:

```text
NilName privileged Lua environment
    |
    +-- Secret-value detector
    +-- Secret-value unwrap/normalizer
    |
Direct game-state API
    +-- C_UnitAuras
    +-- C_Spell
    +-- CombatLog / selected Unit APIs
    |
Guarded per-field normalization
    |
Plain framework state
    |
Tracked Aura cache / per-pulse cache
    |
Rotation API
    +-- Up
    +-- Remains
    +-- Stacks
    +-- Source / FromPlayer
```

### Most likely conclusion

For NilName on 12.1, the best-supported public explanation is **direct read + guarded Secret normalization + cache**, not pure combat-event reconstruction.

Event/cache reconstruction remains a fallback for unusual effects that cannot be represented reliably through the direct path; it should not be the default Sirus design assumption.

## 5. Critical safety/correctness details for Sirus

1. Never call an unwrap primitive blindly. Check whether the value is actually Secret first.
2. Do not assume an AuraData table itself is an atomic Secret value. Normalize fields individually.
3. Include `sourceUnit` in normalization; it is used for “my debuff” / source-filtered checks and has been observed Secret-tainted in another NN framework.
4. Include nested fields such as Aura `points` in the probe.
5. Keep Secret handling below `Sirus.Aura`; profession modules should only receive ordinary Lua values.
6. Cache normalized data. Do not scan 40 Aura slots for every unit on every rotation tick.
7. Preserve a direct provider plus fallback providers; do not couple the entire framework to one implementation detail.

## 6. Revised Sirus plan

Recommended boundary:

```text
Platform/NilName
  SecretValueAdapter
  UnitRef/ObjectRef bridge
  AuraDirectProvider
        |
Sirus/Aura
  tracked-spell cache
  source-aware lookup
  per-pulse memoization
  optional UNIT_AURA invalidation/update
        |
Rotation modules
```

Fallback order:

1. normalized direct Aura data;
2. event/cache support where direct access is incomplete;
3. mechanic reconstruction only for explicitly proven exceptions;
4. UNKNOWN/fail-closed rather than inventing state.

## 7. Local runtime gate

External evidence is now strong enough to justify a focused direct-path probe, but it is **not** equivalent to confirmation on the user's current NN build.

First local probe should isolate PrimeKitCore and test:

- whether `C_Timer.Nn` exists;
- whether the NN environment exposes a Secret-value detector and unwrap primitive;
- player, target and non-current-target/object Auras;
- Aura fields: `spellId`, `applications`, `duration`, `expirationTime`, `sourceUnit`, `points`, name/icon if relevant;
- guarded unwrap on Secret and non-Secret values;
- `C_Spell` and `CombatLogGetCurrentEventInfo()` Secret behavior;
- direct UnitHealth/UnitHealthMax separately for TTD.

Only after this probe succeeds should `NILNAME_API_WHITELIST.md` promote the Secret/Aura path to `LOCAL_RUNTIME_CONFIRMED`.

## 8. Licensing boundary

BadRotations is GPL-3.0. Sirus should use this research as behavioral/architectural evidence and implement its own adapter clean-room. Do not copy GPL implementation code into a proprietary distribution unless a deliberate licensing decision is made.
