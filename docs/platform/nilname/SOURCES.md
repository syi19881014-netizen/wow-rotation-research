# NilName Research Sources

> Updated: 2026-08-17

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

Official docs are treated as the primary contract source. When current pages are unavailable, legacy mirrors are tagged separately and never silently promoted to current.

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

## Public mature framework reference — BadRotations

Repository:

- `CuteOne/BadRotations`
- default branch: `master`
- license: GPL-3.0

Primary audited files:

- `Unlockers/nn.lua`
- `Expansions/Retail/Functions.lua`

Important history:

- commit `740e678e981b77727b1aef4eabe52bf918643c6d` — 2026-03-27, message includes `Initial Midnight NN support`
- its parent `97cc89582d9e7656a8e687f9e34dafa791fd17b1` — used to verify the pre-Midnight NN adapter did not yet contain the secret unwrap compatibility layer
- commit `885beb3f4ef048f557918dbdcfc8d7cd0ffb7642` — 2026-04-20; adds/extends the `C_UnitAuras` proxy path used by the Retail compatibility layer

Key external-framework observations:

- execution environment switch through `C_Timer.Nn`
- runtime symbols `issecretvalue` and `secretunwrap`
- secret-value conversion applied to AuraData
- same conversion concept applied to `C_Spell`
- same conversion concept applied to `CombatLogGetCurrentEventInfo()`
- object/unit normalization before aura calls
- one-`Objects()`-snapshot-per-scan pattern
- `UnitHealth/UnitHealthMax` mapped through the NN-facing compatibility layer

These facts are stored as `EXTERNAL_FRAMEWORK_OBSERVED`, not `RUNTIME_CONFIRMED` for the user's NilName build.

### License boundary

BadRotations is GPL-3.0. Its implementation is used only as research evidence and architectural/reference material. Sirus code should be independently implemented from our own interface contracts unless a future licensing decision explicitly permits GPL-3.0 code reuse.

See:

- `BADROTATIONS_NN_ADAPTER_AUDIT.md`
- `AURA_SECRET_DIRECT_PROBE_SPEC.md`

## Evidence levels used by this research

### OFFICIAL_CURRENT_BODY

Current NilName official docs body retrieved and contract recorded.

### OFFICIAL_CURRENT_INDEX_ONLY

Current NilName official navigation confirms the API exists, but body/signature is not available.

### OFFICIAL_LEGACY_BODY

Older official-doc mirror/body is available; current status must be verified.

### CLIENT_STATIC_OBSERVED

Observed directly in the user-supplied client package without running executables.

### EXTERNAL_FRAMEWORK_OBSERVED

Observed in a public third-party framework that explicitly supports NilName. Strong runtime-development clue, but not a contract for the user's build.

### RUNTIME_CONFIRMED

Reserved for functions/semantics confirmed by our own controlled NilName + WoW runtime probe.

No API should be promoted to this level from documentation or third-party source alone.
