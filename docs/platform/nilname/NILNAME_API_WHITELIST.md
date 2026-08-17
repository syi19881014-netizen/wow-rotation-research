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

## E. 外部成熟框架已观察，但必须本地 Probe 后才能使用

来源：`CuteOne/BadRotations` 当前 `master` 的 `Unlockers/nn.lua`。2026-03-27 提交说明为 `Initial Midnight NN support`，该提交相较前一版本新增了 NilName/Midnight secret-value 处理；2026-04-20 又补充了 `C_UnitAuras` proxy。

### Runtime environment candidates

- `C_Timer.Nn`
- `issecretvalue(value)`
- `secretunwrap(value)`

BadRotations 的结构显示：进入 `C_Timer.Nn` 环境后，可以检测 secret-wrapped scalar，并对 AuraData、`C_Spell` 返回值、`CombatLogGetCurrentEventInfo()` 返回值做 unwrap。

**状态：`EXTERNAL_FRAMEWORK_OBSERVED`，不是 `RUNTIME_CONFIRMED`。**

### 12.1 / Midnight Aura direct-path candidates

第一轮实机 Probe 应优先验证：

- `C_UnitAuras.GetAuraDataByIndex(unit,index,filter)`
- `C_UnitAuras.GetBuffDataByIndex(unit,index,filter)`
- `C_UnitAuras.GetDebuffDataByIndex(unit,index,filter)`
- AuraData 的 `spellId / applications / duration / expirationTime / sourceUnit / points[]` 等字段
- `issecretvalue(field)`
- `secretunwrap(field)` 后是否变为普通 Lua 类型、可比较、可做算术

BadRotations 的当前实现提供了强证据：**Midnight Aura 很可能存在直接可消费路线，而不必默认依赖 CombatLog/cache 重建。** 但在本用户 NilName build 上完成验证前，Sirus 不得把这条路线写成生产依赖。

### Other secret-sensitive candidates

- `C_Spell.*` 返回值
- `CombatLogGetCurrentEventInfo()` 多返回值
- `UnitHealth / UnitHealthMax` 等 TTD 输入是否 secret 或是否需要同一 unwrap 层

### License boundary

BadRotations 为 GPL-3.0。允许把其公开实现作为**研究证据、测试线索、架构参考**；除非未来明确选择 GPL-3.0 兼容发行方式，否则不要复制其 wrapper 源码进入 Sirus。Sirus 应独立实现自己的 Platform/SecretValueAdapter。

## F. Codex 规则

以后让 Codex 开发 NilName 框架或循环时：

1. 默认只能调用 A 区接口。
2. B 区 API 必须先补文档或 runtime probe，再升级状态。
3. C/D 区不得为“方便”直接使用。
4. E 区只允许进入 probe；任何 `C_Timer.Nn` / `secretunwrap` 生产依赖必须先取得本地 12.1 runtime 证据。
5. 不允许根据函数名自行发明参数。
6. 普通 WoW API 是否可直接调用/是否需要 `Unlock`，必须单独建立 WoW-API capability whitelist。
7. 不复制 GPL-3.0 BadRotations 源码；只按我们自己的接口契约 clean-room 重写。
