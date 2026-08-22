# NilName API Whitelist — Provisional Documentation Baseline

> 状态：**DOC-ONLY / NOT RUNTIME-CONFIRMED**  
> 日期：2026-08-17

本白名单只表示“当前官方正文已确认接口契约，适合进入第一轮 runtime probe”。它不表示我们已经在 12.1 客户端实机运行过 NilName。

## A. 第一阶段允许测试/依赖

### Bootstrap / protected calls

- `Unlock(function_or_name, ...)`
- `local nn = ...`（script bootstrap convention）

### Core Objects

- `Object(token)`
- `Objects()` / `GetObjects()`
- `ObjectExists(object)`
- `ObjectName(object)`
- `ObjectPosition(object)`
- `ObjectFacing(object)`
- `ObjectId(object)`
- `GameObjectType(object)`
- `ObjectAnimationFlag(object)`
- `ObjectSkinnable(object)`
- `ObjectInteract(object)`

### Unit metadata

- `CombatReach(object)`
- `UnitMovementFlag(object)`

### Geometry / ground AoE

- `ClickPosition(x,y,z)`
- `TraceLine(x1,y1,z1,x2,y2,z2,flags)`
- `ScreenToWorld(x,y,flags)` — 文档 heading 有错误，实机必须验证返回 shape
- `WorldToScreen(x,y,z)` — 当前文档像素语义，实机必须验证
- `GetCameraPosition()`

### Target bridge

- `GetFocus()`
- `GetMouseover()`
- `GetNPCObject()`
- `SetFocus(object)`

### Optional navigation

- `ClickToMove(x,y,z)`
- `GenerateLocalPath(...)`
- `GeneratePath(...)`
- `SetPlayerFacing(facing)`
- `SendMovementHeartbeat()`
- `SetNavHost(hosturl)`

### HTTP / identity / licensing

- `HTTP:Request(options)`
- `GetWowAccount()`
- `GetKeyState(virtKey)`

### FileSystem

- `FileExists(path)`
- `ReadFile(path)`
- `WriteFile(path,data[,append])`
- `DeleteFile(path)`
- `DirectoryExists(path)`
- `CreateDirectory(path)`
- `DeleteDirectory(path)`
- `ListFiles(path)`

### Crypto

- `NoName.Utils.AES`
- `aes.LoadScriptAES256CBC(...)`
- `aes.RunScriptAES256CBC(...)`
- `aes.encrypt(...)`
- `aes.decrypt(...)`
- `NoName.Utils.sha`
- `sha.sha256(...)`
- `sha.hmac_sha256(...)`
- `NoName.Utils.JSON`

## B. 当前存在，但禁止生产依赖，等待实机/正文补全

### Performance-important pending

- `ObjectPointer`
- `ObjectManager(type)`
- `ObjectType(object)` 独立页面契约

`ObjectType` 本身在当前官方 Getting Started 已经直接使用，因此“函数存在”可信；但因为 Guidelines 又明确建议用 `ObjectManager(type)` 避免逐对象类型检测，所以正式框架应优先把 `ObjectManager(type)` Probe 清楚。

### Object pending

- `ObjectBoundingRadius`
- `ObjectFlags`
- `ObjectHeight`
- `ObjectLootable`
- `ObjectRawPosition`
- `ObjectUnitId`（当前页面拼写不一致）

### Unit pending

- `DynamicFlags`
- `GetUnitBoundingRadius`
- `GetUnitCreatedBy`
- `UnitFlags`
- `UnitFlags2`
- `UnitFlags3`
- `GetUnitIsTapped`
- `GetUnitLootable`
- `GetUnitSummonedBy`
- `UnitTarget`
- `ObjectSkinType`
- `UnitCreatureTypeId`
- `UnitFacing`

### Target pending

- `SetMouseover`
- `SetNPCObject`（当前文档代码块疑似 typo）
- `UnitTarget`
- `CastTarget`
- `PlayerTarget`

### Movement pending

- `GetCorpsePosition`
- `GetPitch`
- `LastTerrainClick`
- `SetPitch`

### Session pending

- `GetSessionId`
- `GetSessionIndex`

### Legacy/warning HTTP

- `HTTPGet`
- `HTTPPost`

## C. 默认禁止

### `ObjectField(object, offset, type)`

虽然当前官方正文可读，但它属于 raw descriptor/memory read。普通循环**禁止使用硬编码 offset**。只有当官方高层 descriptor API 无法提供关键数据、并且我们有版本化 offset 管理和 fail-closed 防护时才允许进入特例审核。

## D. Legacy-only，不得自动调用

- `Distance(...)`
- `GetAnglesBetweenPositions(...)`
- `GetPositionFromPosition(...)`
- `UnitSpecializationID(...)`
- 旧二参数 `SetPlayerFacing(direction, forceUpdate)`

## E. 外部框架线索 — 分清 pre-12.1 与 post-refactor 12.1

### E1. BadRotations：`PRE_12_1_CODE_CONFIRMED`

来源：`CuteOne/BadRotations` 的 `Unlockers/nn.lua`。2026-03-27 `Initial Midnight NN support` 和 2026-04-20 `C_UnitAuras` proxy 均发生在 Blizzard 2026-06-18 的 12.1 Aura refactor 公告之前。

公开代码证明过的 NilName/Midnight runtime candidates：

- `C_Timer.Nn`
- `issecretvalue(value)`
- `secretunwrap(value)`

并证明过一种 pre-refactor 模式：AuraData、`C_Spell`、CombatLog 返回值在 NilName adapter 边界做 Secret-aware normalization。

**这仍是强外部证据，但不是 12.1 post-refactor runtime proof。**

### E2. 12.1 普通-addon 控制组：旧 Aura enumeration 不可直接沿用

公开的 12.1 addon 代码（例如 TellMeWhen / EllesmereUI）显示，在 Aura restrictions 生效时：

- index-based Aura access 可 hard-error；
- slot / auraInstanceID family 也可能被禁止；
- `UNIT_AURA` payload 不能再按旧的可读 delta 数据使用；
- by-spellID / by-name identifier reads 对部分 Aura 仍可调用，但覆盖范围有限。

所以以下 API 在 Sirus 中只能作为 **12.1 capability-probe targets**，不能作为生产白名单：

#### Enumeration / instance family

- `C_UnitAuras.GetAuraDataByIndex(...)`
- `C_UnitAuras.GetAuraDataBySlot(...)`（如果当前 build 存在）
- `C_UnitAuras.GetAuraDataByAuraInstanceID(...)`（如果当前 build 存在）
- Aura slot enumeration APIs（如果当前 build 存在）

#### Identifier family

- `C_UnitAuras.GetUnitAuraBySpellID(...)`（如果当前 build 存在）
- `C_UnitAuras.GetAuraDataBySpellName(...)`（如果当前 build 存在）

必须分别在：

```text
WOW_NORMAL
NN_ENV
NN_UNLOCK（仅签名/调用方式已确认时）
NN_NATIVE（若 runtime 发现明确 NN Aura provider）
```

下比较。

### E3. Ascended：`POST_12_1_RELEASE_CONFIRMED`

`medi8tor/AscendedRotation_Midnight` 在 2026-08-16/17 的公开 release history 明确发布多个 `Midnight 12.1` rotation 更新，包括 Outlaw、Affliction、Unholy 等。

这证明当前 NilName-oriented framework 在 12.1 Aura refactor 之后仍有生产可用路线，但 protected `.nn` distribution 没有公开 exact Aura implementation。

因此：

```text
12.1_NN_ROTATION_VIABILITY = HIGH_EXTERNAL_CONFIDENCE
12.1_NN_AURA_IMPLEMENTATION = UNKNOWN_PENDING_LOCAL_PROBE
```

### E4. 12.1 Aura probe fields

无论哪条 provider 返回 AuraData，都要单独测试：

- `spellId`
- `name`
- `applications`
- `duration`
- `expirationTime`
- `sourceUnit`
- `isHelpful/isHarmful`
- `dispelName`
- `auraInstanceID`
- `points[]` / nested values

若当前 NilName 仍暴露 Secret unwrap primitive，必须按字段检测后再 unwrap；**禁止盲目 `secretunwrap(auraTable)`**。

### E5. Other secret-sensitive candidates

同样只允许 Probe：

- `C_Spell.*` 返回值
- `CombatLogGetCurrentEventInfo()` 多返回值
- `UnitHealth / UnitHealthMax` 等 TTD 输入

## F. 12.1 Aura provider policy

正式 Sirus 不预设 provider 顺序，先按 `AURA_SECRET_DIRECT_PROBE_SPEC.md` 建 capability matrix。

候选：

```text
NN_NATIVE_PROVIDER
NN_PRIVILEGED_IDENTIFIER
NN_PRIVILEGED_INDEX
WOW_IDENTIFIER_FALLBACK
EVENT_CACHE
MECHANIC_RECONSTRUCTION
```

只有本地 runtime probe 证明的一项才能进入生产依赖。

## G. License boundary

BadRotations 为 GPL-3.0。允许作为研究证据、测试线索和架构参考；除非明确选择 GPL-3.0 兼容发行方式，否则不复制其 wrapper 实现进入 Sirus。Sirus 必须按自己的 contract clean-room 实现。

## H. Codex 规则

以后让 Codex 开发 NilName 框架或循环时：

1. 默认只能把 A 区官方正文接口视为文档级可用；涉及 WoW combat state 仍须单独 runtime whitelist。
2. B 区 API 必须先补文档或 runtime probe，再升级状态。
3. C/D 区不得为“方便”直接使用。
4. E/F 区全部是 Probe-only；任何 Aura/Secret 生产依赖必须取得**本用户当前 12.1 build**的 runtime 证据。
5. 不允许根据函数名自行发明参数。
6. 普通 WoW API 是否可直接调用、是否需要/允许 NN privileged execution，必须逐 API 建 capability matrix。
7. 不复制 GPL-3.0 BadRotations 源码；只按我们自己的接口契约 clean-room 重写。
8. 不得把 March/April 2026 的 pre-refactor evidence 写成 12.1 post-refactor confirmation。
