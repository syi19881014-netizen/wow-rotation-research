# BadRotations NilName Adapter Audit

> Date: 2026-08-17  
> Temporal scope: **pre-12.1 Curse of Ula'tek Aura refactor**  
> Purpose: architecture/runtime-probe reference, not current 12.1 Aura proof

## Critical correction

The public BadRotations NilName adapter remains a valuable source, but its relevant Midnight Secret-value commits are from March/April 2026, before Blizzard's 2026-06-18 12.1 Aura refactor announcement.

Therefore every Aura conclusion in this file must be read as:

```text
PRE_12_1_CODE_CONFIRMED
```

not:

```text
POST_12_1_RUNTIME_CONFIRMED
```

For current 12.1 Aura conclusions see:

- `NN_12_1_POST_REFACTOR_AURA_AUDIT.md`
- `AURA_SECRET_DIRECT_PROBE_SPEC.md`

## 1. Source and license

Repository: `CuteOne/BadRotations`, default branch `master`, key files `Unlockers/nn.lua` and Retail compatibility code.

Relevant history:

- 2026-03-27 commit `740e678e981b77727b1aef4eabe52bf918643c6d` — message includes `Initial Midnight NN support`;
- its parent verifies the older NN adapter lacked the Secret unwrap compatibility layer;
- 2026-04-20 commit `885beb3f4ef048f557918dbdcfc8d7cd0ffb7642` extends the `C_UnitAuras` proxy path.

BadRotations is GPL-3.0. Sirus may use behavioral facts and architecture/probe clues, but should clean-room implement its own code unless a deliberate GPL-compatible distribution decision is made.

## 2. Strong pre-refactor discovery: NilName Secret compatibility layer

The public NN adapter enters a NilName-specific environment and uses runtime symbols including:

- `issecretvalue`
- `secretunwrap`

Its compatibility pattern separates:

1. scalar Secret normalization;
2. generic table-field normalization;
3. Aura-specific normalization, including nested values such as `points`.

This is powerful evidence that the earlier Midnight NilName runtime could turn certain Secret-wrapped combat values into ordinary framework-consumable values.

## 3. Pre-refactor Aura path

The public implementation's conceptual path is:

```text
C_UnitAuras lookup/enumeration
        ↓
Object/Unit normalization
        ↓
AuraData
        ↓
Secret detection
        ↓
field-level NilName Secret normalization
        ↓
framework Aura state
```

The public adapter did not need pure CombatLog reconstruction as its ordinary first-line Aura truth source in this era.

### Why this no longer proves the 12.1 path

Post-refactor 12.1 ordinary addon code demonstrates that some Aura calls can hard-error **before an AuraData value is returned**. In that case a field-level `secretunwrap` layer is never reached.

So the current 12.1 question is not merely:

```text
Can NN unwrap the returned field?
```

It is first:

```text
Can NN privileged execution make this Aura API return at all?
```

and, if not:

```text
Does NN expose a different Aura provider or identifier path?
```

## 4. Still-useful implementation lessons

### Field-level normalization

Do not assume an Aura table itself is an atomic Secret scalar. If the current runtime exposes Secret unwrapping, test/normalize required fields separately.

Probe at least:

- spellId
- applications
- duration
- expirationTime
- sourceUnit
- helpful/harmful state
- points/nested values

### Unit/Object bridge

BadRotations shows a mature framework pattern where unit tokens and NilName object references are normalized below the combat modules.

Sirus should preserve this idea:

```text
Sirus UnitRef
├─ player/target/focus/nameplate token
└─ NilName object reference
```

### Secret handling belongs in the platform backend

The same pre-refactor compatibility concept is applied beyond Aura, including `C_Spell` and CombatLog returns. This supports a general:

```text
Platform/NilName/SecretValueAdapter
```

rather than profession modules doing their own Secret checks.

## 5. Object Manager / Snapshot lesson

The public NN integration uses the useful principle that one object-enumeration snapshot should be shared by consumers within a pulse.

Sirus should independently implement:

```text
Tick N
  Objects() once
      ↓
  ObjectSnapshot[N]
      ├─ Targeting
      ├─ Aura
      ├─ TTD
      ├─ AoE
      └─ Movement
```

This reduces API calls and keeps same-pulse state coherent.

## 6. C_Spell and CombatLog

Pre-refactor code also suggests Secret-sensitive handling for `C_Spell` and `CombatLogGetCurrentEventInfo()`.

This remains a valid probe clue but current 12.1 behavior must be tested independently. Aura success cannot be generalized to Spell, Health or CLEU values.

## 7. Health / TTD clue

The NN-facing compatibility layer includes `UnitHealth` / `UnitHealthMax`, which supports the planned TTD research direction.

Current production requirements remain runtime-only:

- target health;
- non-current NN object health;
- restricted-combat behavior;
- Secret status/normalization;
- high-frequency sampling stability.

## 8. What Sirus can safely borrow at idea level

1. Platform Adapter separated from rotations.
2. UnitRef/ObjectRef normalization.
3. One Object snapshot per pulse.
4. SecretValueAdapter as a backend concern.
5. Per-field/schema-aware normalization rather than blind table unwrap.
6. C_Spell/CLEU/Health probed independently.
7. Clean-room implementation due GPL boundary.

## 9. What Sirus must NOT infer from this repo

Do not infer that current WoW 12.1 supports:

- `GetAuraDataByIndex` in restricted combat under NN;
- slot/instanceID enumeration under NN;
- readable `UNIT_AURA` payload;
- the same `secretunwrap` symbols/signature in the user's current build;
- complete non-target Aura access.

Those are now explicit runtime-probe questions.

## 10. Updated probe order

```text
A. current 12.1 ordinary Aura control group
   ├─ index
   ├─ slot/instance
   ├─ identifier reads
   └─ UNIT_AURA

B. current NilName environment discovery
   ├─ C_Timer.Nn
   ├─ Secret detector/unwrap
   └─ NN-native Aura namespaces

C. repeat identical Aura calls under NN privilege

D. player / proc / target / non-target object matrix

E. C_Spell / CLEU / Health
```

## 11. Evidence status

```text
BadRotations Midnight SecretValue architecture = HIGH / PRE_12_1_CODE_CONFIRMED
BadRotations current 12.1 Aura solution          = NOT PROVEN
```

The repo remains highly useful, but only within the correct temporal boundary.
