# NilName Aura Ecosystem Cross-Validation

Date: 2026-08-17  
Status: external research only; **post-12.1 claims are superseded/qualified by `NN_12_1_POST_REFACTOR_AURA_AUDIT.md`**

## Scope and correction

This file records what public NilName frameworks teach us about Aura handling. It must distinguish two eras:

1. **Midnight / pre-12.1 Aura-refactor Secret-value handling** — public NilName framework code exists.
2. **12.1 Curse of Ula'tek Aura refactor (announced 2026-06-18)** — Blizzard changed the Aura access model again; pre-June code cannot be promoted to 12.1 proof.

The earlier conclusion that “direct `C_UnitAuras` + `secretunwrap` is the best-supported 12.1 model” was too broad. That model is strongly supported for the **pre-refactor Midnight Secret-value layer**, not yet for the post-refactor 12.1 API contract.

For current conclusions, read `NN_12_1_POST_REFACTOR_AURA_AUDIT.md` first.

## Evidence classes

- `PRE_12_1_CODE_CONFIRMED`: public source shows the pre-refactor implementation.
- `POST_12_1_RELEASE_CONFIRMED`: current protected NilName distribution ships explicit 12.1 rotations; implementation hidden.
- `ECOSYSTEM_ONLY`: NilName support/product existence confirmed; Aura implementation not public.
- `LOCAL_RUNTIME_CONFIRMED`: reserved for our current client probe; none yet.

## Framework matrix

| Framework / product | NilName use | Aura evidence | Correct classification |
|---|---|---|---|
| BadRotations | Yes | Public NN adapter with `C_Timer.Nn`, Secret detection/unwrap, Aura/C_Spell/CLEU normalization; relevant commits Mar-Apr 2026 | `PRE_12_1_CODE_CONFIRMED` |
| Ascended Rotation Midnight | NilName-oriented | Pre-refactor release history shows Secret-Aura handling; Aug 2026 releases explicitly update multiple rotations for 12.1 | `POST_12_1_RELEASE_CONFIRMED`, exact 12.1 Aura path unknown |
| PrimeKitCore | Bundled in user NN package | Protected `.nn` only | `ECOSYSTEM_ONLY` / client-static observed |
| Lunar | NilName partner/support | Closed | `ECOSYSTEM_ONLY` |
| Clipper | NilName partner/support | Closed | `ECOSYSTEM_ONLY` |
| Go Hands Free | NilName partner/support | Closed | `ECOSYSTEM_ONLY` |
| NilName in-house rotations | Native | Closed | `ECOSYSTEM_ONLY` |
| Phoenix / Wings / other community-listed products | Secondary reports | No primary implementation found | discovery only |

## 1. BadRotations — what it actually proves

BadRotations' public NN adapter is valuable because both the older adapter and the Midnight transition are visible.

The 2026-03-27 `Initial Midnight NN support` work introduces a Secret compatibility layer in the NilName environment and uses runtime symbols such as:

- `issecretvalue`
- `secretunwrap`

The adapter normalizes Secret-tainted scalar/table fields and has Aura-specific handling, including nested values. The same platform-boundary idea is used for `C_Spell` and `CombatLogGetCurrentEventInfo()`.

Its Aura path in this era is effectively:

```text
C_UnitAuras
  -> AuraData
  -> guarded per-field Secret normalization
  -> ordinary framework state
```

This is excellent evidence for **how Sirus should isolate Secret handling at the platform boundary**, and excellent evidence that NilName had a privileged Secret-value path in the earlier Midnight environment.

It is **not** post-12.1 Aura-refactor proof because the relevant public implementation predates Blizzard's June 18 announcement/refactor work.

## 2. Ascended — what the older and newer history prove

Pre-refactor public release history records highly specific behavior:

- Secret `sourceUnit` needed normalization before table-key use;
- a HasAura fast path broke on secret-tainted Auras;
- blindly applying `secretunwrap` to an Aura table was wrong because a table is not an atomic Secret scalar;
- private Aura debug/display paths and later per-pulse/source-aware Aura caches existed.

Those observations independently corroborate BadRotations' **pre-refactor** field-level Secret-normalization model.

After the June 18 refactor, Ascended continues shipping protected NilName builds and, on 2026-08-16/17, publishes explicit `Midnight 12.1` rotation updates for multiple specs including Affliction, Outlaw and Unholy.

That establishes current production viability but not implementation details:

```text
12.1 NN rotation viability = strong external evidence
12.1 Aura transport/source = still unknown
```

## 3. Closed frameworks

Lunar, Clipper, Go Hands Free, NilName's own rotations, and the bundled PrimeKitCore are useful as ecosystem evidence only. No public primary implementation was found that allows us to say whether they use:

- Blizzard identifier Aura APIs;
- NN-native/internal Aura data;
- a privileged post-refactor unwrap route;
- object/descriptor state;
- event reconstruction;
- a mixed design.

Do not guess.

## 4. Architecture facts still safe to retain

The following ideas survive the 12.1 correction because they are framework-level rather than dependent on one Aura API:

1. Put NilName-specific Secret handling under `Platform/NilName`.
2. Normalize UnitRef/ObjectRef before combat modules consume state.
3. Cache normalized results per pulse; do not make every APL branch rescan Auras.
4. Treat `sourceUnit` and nested fields as separately capability-tested values.
5. Keep direct provider, event support, and reconstruction decoupled so 12.1 can choose the working provider at runtime.
6. Do not copy BadRotations GPL-3.0 implementation into a proprietary Sirus distribution; clean-room implement against our own interface contract.

## 5. Current provider decision

Do **not** freeze this old ordering yet:

```text
Direct index Aura -> Secret unwrap -> Event fallback
```

Use capability routing instead:

```text
NN-native provider?             -> probe
NN-privileged identifier read?  -> probe
NN-privileged index read?       -> probe
ordinary identifier fallback?   -> probe/limited
Event cache/invalidation         -> support
mechanic reconstruction          -> exception
```

The working combination is selected only after the current client passes `AURA_SECRET_DIRECT_PROBE_SPEC.md` (now upgraded to a 12.1 interface capability matrix).

## 6. Supersession rule

Any project note that uses March/April 2026 BadRotations or early Ascended Secret-Aura behavior as direct proof of the **post-refactor 12.1** Aura solution is superseded.

Those sources remain valid for:

- the pre-12.1 Midnight Secret model;
- SecretValueAdapter architecture;
- probe targets;
- clean separation between platform/backend and rotation modules.

For the current 12.1 conclusion, use `NN_12_1_POST_REFACTOR_AURA_AUDIT.md` plus local runtime results.
