# NilName client static audit — 2026-08-17

Scope: static inspection only. No uploaded executable was launched.

## Archive

- Uploaded archive: `NN.zip`
- SHA-256: `fdda48faac477fe2a7c2ad9d8a493f65863fcfab1cf443b00e57bf6eb284c645`
- 41 archive entries, ~10.3 MB uncompressed.

## High-level layout

The package contains:

- a likely renamed NilName launcher: `claude.exe`
- navigation helper binaries: `NnNavigation_RenameMe.exe` plus two `.upd...` PE files
- `license.txt` (empty in this copy)
- `/scripts/` for world-loaded Lua/NN scripts
- `/load_glue/` with a plaintext relogger and account config
- `/lua/core/` and `/lua/utils/` precompiled/protected `.nn` libraries
- `/mmaps/` containing only download instructions, not actual retail mesh files
- `WowErrors/` placeholders

Official setup docs say the launcher is normally `NoName.exe`, that it may be renamed/obscured, and that scripts under `/scripts/` beginning with `_` auto-load on world entry. This matches the package structure.

## Launcher / batch observations

`Command Line Examples.txt` explicitly documents renaming `NoName.exe` (example: `notepad.exe`) and passing the NilName token/session count/WoW path on the command line.

`start.bat` currently invokes `666.exe`, but no `666.exe` exists in the uploaded archive. Therefore this batch file is stale relative to the current renamed launcher (`claude.exe`) unless the user renames/copies the launcher or edits the batch file.

`license.txt` is empty, so this copy contains no NilName license token.

## Navigation

`NN/mmaps/MMAP download info.txt` points to official CDN bundles:

- Classic Era: `https://cdn.nilname.com/mmaps/classic_era.7z`
- Classic: `https://cdn.nilname.com/mmaps/classic.7z`
- Retail: `https://cdn.nilname.com/mmaps/retail-bundle.7z`

The uploaded package does **not** contain `.mmap` / `.mmtile` mesh data. Therefore full path-generation/navigation should not be considered ready until the retail bundle is installed in the expected folder.

## Plaintext runtime evidence from `load_glue/reloggerV9.lua`

This file is valuable because it is readable source and directly confirms several runtime conventions/functions in this client family.

Observed patterns/functions:

- `local NoName = ...`
- `NoName.GetSessionIndex()`
- `Unlock(...)`
- `ReadFile(...)`
- `WriteFile(...)`
- `FileExists(...)`
- `Utils.JSON.decode`
- normal WoW Lua globals / namespaces such as `C_Timer`, `C_Login`, `C_RealmList`, `GetTime`, etc.

The relogger uses `C_Timer.After` / `C_Timer.NewTicker`, reinforcing that NilName does not impose a Workout-style mandatory `Main()` host; framework code can build its own scheduler/tickers.

## `.nn` files

All sampled `.nn` files begin with the standard Lua 5.1 bytecode signature (`1B 4C 75 61 51 ...`) but the prototype/body data is strongly obfuscated/protected and does not expose useful printable symbol strings under ordinary static extraction.

Examples:

- `lua/core/storage.nn`
- `lua/core/slashcommands.nn`
- `lua/utils/AESECB.nn`
- `scripts/_PrimeKitCore.nn`

This is consistent with a protected/compiled distribution format. No attempt was made to bypass or reverse the protection.

## Bundled third-party framework: `_PrimeKitCore.nn`

`NN/scripts/_PrimeKitCore.nn` is ~102 KB and starts with `_`.

Because official NilName docs state that `/scripts/` files beginning with `_` auto-load on entering the world, this package will likely auto-load PrimeKitCore unless it is moved/renamed/disabled.

Important implication for Sirus development:

- treat PrimeKitCore as a **third-party framework bundled with this particular package**, not as proof of NilName-native behavior;
- initial NilName capability probes should be performed with PrimeKitCore isolated, otherwise we cannot distinguish NilName functions from framework-added helpers;
- preserve the file for later comparative study, but do not depend on it for Sirus.

Public web search performed on 2026-08-17 did not find useful indexed documentation for `PrimeKitCore` / `_PrimeKitCore.nn`.

## Internal Lua libraries

The package includes protected/compiled versions of:

- Ace3
- AceAddon-3.0
- AceComm-3.0
- AceDB-3.0
- CallbackHandler-1.0
- LibSharedMedia-3.0
- LibStub
- AES/ECB helper
- anti-AFK helper
- core storage and slash-command modules

This is consistent with NilName providing a substantial Lua support environment even though it does not provide a full rotation host.

## PE static observations

Executables were inspected statically only.

### `claude.exe`

- SHA-256: `5f813ae145bdb54d09099df055b4b45103d138f31c711cdbab94894c7ae3cb49`
- PE32+, x86-64, Windows console subsystem
- imports include networking/crypto/system libraries such as `WS2_32`, `bcrypt`, `CRYPT32`, `ncrypt`, `IPHLPAPI`, `KERNEL32`
- section names/metadata are intentionally irregular and the main raw section has high entropy (~7.95 bits/byte), consistent with packing/obfuscation
- PE security directory is empty in static headers (no embedded Authenticode signature observed)

### Navigation binaries

All three navigation-related files are x86-64 PE executables and similarly appear packed/obfuscated under static inspection.

No conclusion about trustworthiness or maliciousness should be drawn solely from packing or lack of an Authenticode signature; these observations only mean ordinary static inspection reveals little about their implementation.

## Client/documentation cross-check

The uploaded package strongly matches current official setup/developer documentation in several areas:

1. launcher can be renamed;
2. license key is stored in `license.txt`;
3. `/scripts/` contains `.lua` / `.nn` scripts;
4. underscore-prefixed scripts auto-load;
5. `local nn = ...` / `local NoName = ...` convention is used;
6. `Unlock(...)` is present in real bundled Lua source;
7. filesystem and JSON helpers are present in real bundled Lua source;
8. an optional external navigation helper and separate MMaps are used.

## What this client DOES confirm for Sirus feasibility

The package is sufficient to justify proceeding with a NilName-native Sirus framework design around:

- custom scheduler/ticker
- object manager
- target/state cache
- spell/unlock layer
- GCD/action queue
- TTD engine
- position/ground-AoE engine
- navigation adapter
- HTTP/license module
- logging/storage/UI
- APL/rotation modules

However, the static client package does **not** by itself settle several WoW 12.1 runtime questions.

## What remains runtime-only

The following must be tested in the actual current WoW/NilName runtime, preferably with PrimeKitCore disabled:

1. **12.1 Aura/Secret behavior**
   - whether ordinary `C_UnitAuras` remains secret in combat;
   - whether `Unlock` changes anything (do not assume it does);
   - whether NilName exposes any lower-level aura source not visible in public docs;
   - which buffs/procs can be reconstructed reliably through events.

2. **Health / TTD inputs**
   - whether `UnitHealth(object)` / `UnitHealthMax(object)` accept Nn object handles reliably for all nearby enemies in combat;
   - sampling stability and object identity persistence.

3. **Spell execution semantics**
   - protected cast behavior;
   - GCD timing;
   - queue/retry behavior;
   - confirmation events and failures.

4. **Account/session APIs**
   - actual runtime return values/types of `GetWowAccount`, `GetSessionId`, `GetSessionIndex`.

5. **HTTP/Crypto**
   - callback behavior and TLS/certificate handling in the current client.

6. **Object/position API**
   - current 12.1 object type values;
   - `ObjectPosition`, facing, range, visibility/LOS, object lifetime.

## Recommended clean-room probe order

Before any rotation is migrated, use a native-only capability probe set with `_PrimeKitCore.nn` temporarily removed from auto-load:

1. script load + `local nn = ...`
2. `Object('player')`, `Objects()`, `ObjectType`, `ObjectPosition`
3. current target / nearby enemies
4. `UnitHealth(object)` / `UnitHealthMax(object)`
5. 12.1 Aura matrix
6. protected cast + GCD timing
7. account/session identity
8. HTTP request
9. ground-target spell + `ClickPosition`
10. navigation after installing retail MMaps

Once these pass, freeze a `RUNTIME_CONFIRMED` NilName whitelist and build Sirus only on top of that whitelist.
