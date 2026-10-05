# NilName Research Sources

> Updated: 2026-08-17

## Official Blizzard 12.1 Aura sources

These are the primary sources for the post-refactor boundary and take precedence over pre-June framework behavior when describing WoW 12.1 Aura restrictions.

- `https://us.forums.blizzard.com/en/wow/t/addons-and-auras-in-curse-of-ula%E2%80%99tek/2317456/`
  - 2026-06-18 developer post: 12.1 focuses on preventing player/enemy/party/raid Aura information from leaking combat-automation inputs while adding filtered display APIs that do not expose the underlying Aura information.
- `https://us.forums.blizzard.com/en/wow/t/midnight-curse-of-ulatek-ptr-development-notes/2317811/1`
  - PTR notes: new addon Aura APIs display filtered Aura sets without exposing underlying information usable for automation.

See `NN_12_1_POST_REFACTOR_AURA_AUDIT.md`.

## Public post-12.1 addon control-group evidence

These are not NilName frameworks. They are used as a control group to establish what the current ordinary-addon execution model does under 12.1 restrictions.

### TellMeWhen

Repository: `ascott18/TellMeWhen`

- commit `852c25fd309879d09a51d3720f139541e3f72984` — 2026-08-16; documents index/slot/auraInstanceID Aura reads hard-erroring under restrictions, `UNIT_AURA` payload being unusable as the old delta source, and by-spellID/by-name identifier lookups as the surviving limited read path.
- commit `e838fb903624ebb7b27989596db7628bbc46b550` — 2026-07-24; adapts to 12.1 Aura Container API changes and secret-aware access restrictions.

### EllesmereUI

Repository: `EllesmereGaming/EllesmereUI`

- commit `80e8678a066ce1ec1196a05f2ee28ad0aad03c87` — 2026-08-05; records that `GetAuraDataByIndex` can hard-error in combat for a tainted caller before `issecretvalue()` can inspect a return value.

These sources are important because they prove why “just unwrap the returned Secret” is not a complete 12.1 model if the API call itself is blocked.

## Official NilName / NoName documentation

Primary documentation domain:

- `https://docs.nilname.com/`

Important confirmed sections used in this research baseline:

- `/API/Guidelines/`
- `/Home/LuaAPISummary/`
- `/Home/Getting_started_as_a_developer/`
- `/Scripts/`
- `/Crypto/`
- `/FileSystem/`
- `/LuaAPI/Targeting/*`
- `/LuaAPI/Objects/*`
- `/LuaAPI/Units/*`
- `/LuaAPI/Movement/*`
- `/LuaAPI/HTTP/*`
- `/LuaAPI/Miscellaneous/*`

Official docs are treated as the primary NilName contract source. When current pages are unavailable, legacy mirrors are tagged separately and never silently promoted to current.

## User-supplied client package

Artifact supplied in conversation:

- `NN.zip`

Static audit only. No executable was run.

Observed package elements include:

- renamed NilName launcher executable
- NilName navigation executable/update files
- `/scripts/_PrimeKitCore.nn`
- `/load_glue/reloggerV9.lua`
- protected `.nn` Lua 5.1 bytecode modules
- `mmaps` download instructions without installed retail mesh files

See `CLIENT_AUDIT_2026-08-17.md`.

## Public mature framework reference — BadRotations (pre-12.1 Aura refactor)

Repository:

- `CuteOne/BadRotations`
- default branch: `master`
- license: GPL-3.0

Primary audited files:

- `Unlockers/nn.lua`
- `Expansions/Retail/Functions.lua`

Important history:

- commit `740e678e981b77727b1aef4eabe52bf918643c6d` — 2026-03-27, message includes `Initial Midnight NN support`
- parent `97cc89582d9e7656a8e687f9e34dafa791fd17b1` — verifies the older NN adapter lacked the later Secret unwrap compatibility layer
- commit `885beb3f4ef048f557918dbdcfc8d7cd0ffb7642` — 2026-04-20; adds/extends the `C_UnitAuras` proxy path

Key observations:

- `C_Timer.Nn`
- `issecretvalue` and `secretunwrap`
- Secret normalization applied to AuraData
- same concept applied to `C_Spell`
- same concept applied to `CombatLogGetCurrentEventInfo()`
- object/unit normalization before Aura calls
- one-`Objects()`-snapshot-per-scan pattern
- `UnitHealth/UnitHealthMax` mapped through the NN-facing compatibility layer

**Temporal classification:** these are `PRE_12_1_CODE_CONFIRMED` facts because the relevant code predates Blizzard's 2026-06-18 Aura refactor. They must not be described as direct proof of the current 12.1 Aura API path.

### License boundary

BadRotations is GPL-3.0. Its implementation is used only as research evidence and architecture/reference material. Sirus should be independently implemented from our own interface contracts unless a future licensing decision explicitly permits GPL-compatible code reuse.

See:

- `BADROTATIONS_NN_ADAPTER_AUDIT.md`
- `NN_AURA_ECOSYSTEM_CROSSVALIDATION.md`

## Post-refactor NilName viability evidence — Ascended Rotation Midnight

Repository: `medi8tor/AscendedRotation_Midnight`

Pre-refactor release history is useful for Secret-Aura architecture, while current releases establish 12.1 viability.

Examples:

- commit `3c513d0d2712f7704a13d4c3d38fc24362f9e365` — v0.1.861, 2026-08-16; explicitly updates Affliction Warlock and Outlaw Rogue rotations for Midnight 12.1 and references merge from `AscendedRotationsNilName`.
- commit `7f36282e5ffde85dec632c00b0402da6930a0cbc` — v0.1.866, 2026-08-17; Unholy Death Knight 12.1 rotation update.

Classification:

```text
POST_12_1_RELEASE_CONFIRMED
```

The distribution is protected `.nn`, so these releases prove current NilName-oriented 12.1 rotation viability but do not reveal the exact Aura implementation.

## Evidence levels used by this research

### OFFICIAL_CURRENT_BODY

Current official documentation body retrieved and contract recorded.

### PRE_12_1_CODE_CONFIRMED

Public NilName framework code proves an implementation, but it predates the June 18 12.1 Aura refactor.

### POST_12_1_CODE_CONFIRMED

Current public code after the refactor proves specific 12.1 API behavior. Ordinary-addon projects currently provide this control-group evidence.

### POST_12_1_RELEASE_CONFIRMED

A current protected NilName-oriented distribution explicitly ships 12.1 rotations, but implementation internals are hidden.

### CLIENT_STATIC_OBSERVED

Observed directly in the user-supplied client package without running executables.

### ECOSYSTEM_ONLY

NilName support/product existence confirmed; no primary Aura implementation proof.

### RUNTIME_CONFIRMED

Reserved for functions/semantics confirmed by our own controlled current NilName + WoW 12.1 runtime probe.

No Aura provider should be promoted to this level from documentation, old framework code or current release existence alone.
