# NilName 12.1 Post-Refactor Aura Audit

> Date: 2026-08-17  
> Scope boundary: evidence after Blizzard's 2026-06-18 Curse of Ula'tek Aura refactor announcement  
> Status: external research; no local NilName runtime confirmation yet

## Executive conclusion

The earlier Midnight evidence and the 12.1 Curse of Ula'tek Aura refactor must be treated as two different compatibility problems.

- Pre-12.1 public NilName framework code proves that NilName could expose/use Secret-value detection and unwrapping for AuraData and other combat-critical values.
- Blizzard's 12.1 Aura work explicitly changes the Aura access model to stop addon-visible Aura data from leaking information usable for combat automation.
- Ordinary addon implementations updated for the real 12.1 API demonstrate that index-, slot-, and auraInstanceID-based Aura reads can hard-error while Auras are secret, and that `UNIT_AURA` payload data is not available as a normal iterable state source.
- A current NilName-oriented framework, Ascended Rotation Midnight, is shipping explicit 12.1 profession-rotation updates after the refactor. This is strong evidence that 12.1 rotation use on NilName is practically solvable, but its protected distribution does not reveal the exact Aura transport/normalization path.

Therefore the old statement

```text
C_UnitAuras index scan -> secretunwrap -> Aura cache
```

must **not** be treated as the confirmed 12.1 solution.

The correct current stance is:

```text
12.0/Midnight Secret-value solution: PRE_12_1_CODE_CONFIRMED
12.1 ordinary-addon Aura restrictions: POST_12_1_CODE_CONFIRMED
12.1 NilName production viability: POST_12_1_RELEASE_CONFIRMED
12.1 NilName exact Aura implementation: UNKNOWN_PENDING_RUNTIME_PROBE
```

## Evidence classes

- `PRE_12_1_CODE_CONFIRMED` — public implementation exists, but predates the June 18 Aura refactor.
- `POST_12_1_CODE_CONFIRMED` — public implementation/source after the Aura refactor directly demonstrates current API behavior.
- `POST_12_1_RELEASE_CONFIRMED` — current protected NilName product/framework is shipping explicit 12.1 rotations, but implementation is hidden.
- `ECOSYSTEM_ONLY` — product/framework is confirmed in the NilName ecosystem; no primary Aura implementation evidence is public.
- `LOCAL_RUNTIME_CONFIRMED` — reserved for our own current NilName + WoW 12.1 probe. None yet.

## 1. Blizzard 12.1 changes are not just another Secret-value field pass

Primary Blizzard sources:

- `https://us.forums.blizzard.com/en/wow/t/addons-and-auras-in-curse-of-ula%E2%80%99tek/2317456/`
- `https://us.forums.blizzard.com/en/wow/t/midnight-curse-of-ulatek-ptr-development-notes/2317811/1`

On 2026-06-18 Blizzard stated that 12.1 is the next major step of the Midnight addon-security work, specifically focused on Auras. The stated goal is to prevent player/enemy/party/raid Auras from exposing combat information usable for automation, while introducing filtered display APIs that do not expose the underlying Aura information.

This is an interface-model change, not merely evidence that some existing fields became Secret.

## 2. Ordinary-addon baseline after the refactor

The ordinary addon baseline is valuable because it tells us what **must fail or be restricted without NilName privilege**. This gives the local NN probe a control group.

### TellMeWhen — 2026-08-16

Repository: `ascott18/TellMeWhen`  
Commit: `852c25fd309879d09a51d3720f139541e3f72984`

Its post-12.1 implementation records that while Aura restrictions are active:

- Aura reads by index, slot, or auraInstanceID hard-error;
- `UNIT_AURA` payload is entirely secret/unusable as the old delta source;
- tracked identifiers are re-read through `GetUnitAuraBySpellID` and `GetAuraDataBySpellName`;
- identifier lookups have reduced expressiveness: they cannot replace full enumeration, second/later copies, generic Aura filters, or “track every Aura” behavior.

This is strong `POST_12_1_CODE_CONFIRMED` evidence that the old index-enumeration model cannot be assumed to survive 12.1 for ordinary addon execution.

### TellMeWhen Aura Containers — 2026-07-24

Commit: `e838fb903624ebb7b27989596db7628bbc46b550`

The current 12.1 container path had to adapt to multiple PTR API changes, secret-aware access restrictions, and engine-controlled Aura button behavior. This independently confirms that 12.1's supported addon display model is materially different from the old Aura enumeration model.

### EllesmereUI — 2026-08-05

Repository: `EllesmereGaming/EllesmereUI`  
Commit: `80e8678a066ce1ec1196a05f2ee28ad0aad03c87`

Its source notes that `C_UnitAuras.GetAuraDataByIndex` can hard-error in combat for a tainted caller before any `issecretvalue()` check on a returned value can run.

This detail matters for Sirus: **a Secret-value normalizer alone is not sufficient if the Aura API call itself is blocked before a value is returned.**

## 3. BadRotations must be downgraded from “12.1 proof” to pre-refactor evidence

Repository: `CuteOne/BadRotations`

Useful public history:

- 2026-03-27 `Initial Midnight NN support`
- 2026-04-20 `C_UnitAuras` proxy/compatibility work
- latest relevant public repository activity predates the June 18 Aura refactor

The public NN adapter is still extremely useful because it proves a NilName execution environment in which framework code used:

- `C_Timer.Nn`
- `issecretvalue`
- `secretunwrap`
- per-field Aura normalization
- Secret-aware `C_Spell` / CombatLog normalization

However, this must now be classified as:

```text
PRE_12_1_CODE_CONFIRMED
```

It does **not** prove that 12.1 allows the same index-based Aura call to return a value that can then be unwrapped.

## 4. Ascended gives the strongest post-refactor NilName viability evidence

Repository: `medi8tor/AscendedRotation_Midnight`

Older public release notes before the refactor showed sophisticated Secret-Aura handling, including Secret `sourceUnit`, secret-tainted Aura fixes, decrypted private-Aura diagnostics, and per-pulse Aura caches. Those remain useful as pre-12.1 architectural evidence.

More important for the current question, the protected NilName-oriented distribution continues shipping after the June 18 refactor and is now publishing explicit 12.1 rotation updates. Examples include:

- v0.1.861, 2026-08-16: Affliction Warlock and Outlaw Rogue “Midnight 12.1” updates;
- v0.1.866, 2026-08-17: Unholy Death Knight 12.1 rotation update;
- adjacent releases also update additional specs for 12.1.

This is:

```text
POST_12_1_RELEASE_CONFIRMED
```

It strongly supports the conclusion that a NilName framework can run current 12.1 rotations after the Aura refactor.

What it **does not** reveal is whether Ascended now uses:

- identifier-based Blizzard Aura APIs inside a privileged NN environment;
- an NN-native/internal Aura provider;
- a modified Secret unwrap path that bypasses ordinary-addon call restrictions;
- object/internal data;
- a mixed provider/cache strategy.

Because the shipped framework is protected `.nn`, the exact post-refactor Aura source remains unknown.

## 5. Closed NilName frameworks/products

Current ecosystem candidates include Lunar, Clipper, Go Hands Free, NilName's own rotations, PrimeKitCore, and other community-listed frameworks/products.

Their continued existence is useful as ecosystem evidence, but no primary public 12.1 Aura implementation was found in this audit. Do not infer their internal route from marketing/support status.

Classification:

```text
Lunar            ECOSYSTEM_ONLY
Clipper          ECOSYSTEM_ONLY
Go Hands Free    ECOSYSTEM_ONLY
NilName Rotations ECOSYSTEM_ONLY
PrimeKitCore     ECOSYSTEM_ONLY / CLIENT_STATIC_OBSERVED
```

## 6. Cross-validation matrix

| Question | Ordinary addon post-12.1 | BadRotations public NN code | Ascended current NN distribution | Current conclusion |
|---|---|---|---|---|
| Can index/slot/instance Aura enumeration be assumed in combat? | No; public 12.1 addon code reports hard errors | Yes in pre-refactor code | Hidden | **Do not assume** |
| Does `UNIT_AURA` expose the old usable payload? | No in restricted mode | Pre-refactor assumptions only | Hidden | **Do not assume** |
| Are by-spellID/name reads useful? | Yes for some non-secret/identifier-resolvable Auras | Not the old primary route | Hidden | **Must probe** |
| Does NilName expose Secret detector/unwrap? | N/A ordinary addon | Yes, pre-refactor external code | Older release history is consistent | **Runtime-discover current build** |
| Can a current NN framework run 12.1 rotations? | N/A | Public repo not current enough | Yes; explicit 12.1 releases | **High-confidence yes** |
| Exact current NN Aura truth source known? | N/A | Only pre-refactor path known | No | **UNKNOWN** |

## 7. Revised Sirus Aura architecture

Do not hard-code one source as “the 12.1 solution” before the local probe.

Use capability-routed providers:

```text
Platform/NilName/AuraCapability
    |
    +-- NN_NATIVE_PROVIDER           [if runtime discovered]
    +-- NN_PRIVILEGED_IDENTIFIER     [spellID/name]
    +-- NN_PRIVILEGED_INDEX          [only if current build proves it]
    +-- WOW_IDENTIFIER_FALLBACK      [limited ordinary path]
    +-- EVENT_CACHE                  [invalidation/support]
    +-- MECHANIC_RECONSTRUCTION      [explicit exceptions only]
            |
       normalized AuraState
            |
        Sirus.Aura
```

The framework should select a provider per capability/field/unit type rather than assuming one global route.

## 8. Updated runtime probe requirements

The first current-12.1 probe must compare **ordinary WoW behavior vs NilName-privileged behavior** for the same Aura and unit.

### Environment

- isolate/disable `_PrimeKitCore.nn`;
- load only the probe;
- record WoW build and NilName build;
- test out of combat and in combat/restricted state.

### API families

Test existence and protected-call behavior without guessing missing signatures:

1. Index/enumeration family
   - `GetAuraDataByIndex`
   - slot APIs if present
   - auraInstanceID APIs if present
2. Identifier family
   - `GetUnitAuraBySpellID` if present
   - `GetAuraDataBySpellName` if present
3. Event
   - `UNIT_AURA` payload shape and Secret behavior
4. NilName environment
   - `C_Timer.Nn`
   - Secret detector/unwrap symbols if exposed
   - runtime namespace discovery for an NN-native Aura provider
5. Unit coverage
   - player buff
   - player proc/stacking buff
   - target debuff
   - target buff
   - non-current NilName object debuff
6. Fields
   - existence
   - spellId/name
   - applications/stacks
   - duration
   - expirationTime
   - sourceUnit
   - nested points/value fields if present

### Required result granularity

Do not return one global PASS/FAIL. Classify each combination as one of:

```text
NORMAL_AVAILABLE
EXPECTED_BLOCKED_NORMAL
NN_PRIVILEGED_INDEX
NN_PRIVILEGED_IDENTIFIER
NN_NATIVE_PROVIDER
SECRET_RETURNED_UNWRAPPED
SECRET_RETURNED_NOT_CONSUMABLE
IDENTIFIER_ONLY
EVENT_INVALIDATION_ONLY
NO_DIRECT_PATH
UNKNOWN
```

## 9. What would settle the question

The 12.1 Aura problem is considered solved for Sirus only when the user's current runtime demonstrates that rotation-critical fields can be turned into ordinary framework state for all required unit classes, especially non-current enemy objects.

A minimal success proof is:

```text
player proc:      Up + Stacks + Remains
current target:   Debuff Up + Remains + Source
non-current mob:  Debuff Up + Remains + Source
```

with stable results in combat/restricted mode and no PrimeKit dependency.

Until then, the correct label is:

```text
12.1_NN_AURA_SOLUTION = POST_12_1_VIABILITY_CONFIRMED / IMPLEMENTATION_UNKNOWN
```

## 10. Research-policy correction

Any previous project note that described BadRotations' March/April direct `C_UnitAuras -> secretunwrap` implementation as confirmed **12.1** behavior is superseded by this audit.

It remains valid evidence for the earlier Midnight Secret-value model and for Sirus adapter design, but current 12.1 Aura behavior must be established from post-refactor evidence and our own runtime capability matrix.
