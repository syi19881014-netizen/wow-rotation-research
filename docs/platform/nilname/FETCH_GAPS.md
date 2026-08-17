# NilName Documentation Fetch Gaps

抓取日期：2026-08-17。

当前 NilName 文档站存在一种明显现象：侧栏/索引完整可见，但部分具体 API 页面通过抓取环境会返回 `403 Forbidden`。因此本档案把“知道 API 名称存在”和“知道准确签名/返回值”严格分离。

## 当前正文无法取得（403 / index-only）

### Objects

- `ObjectBoundingRadius`
- `ObjectFlags`
- `ObjectHeight`
- `ObjectLootable`
- `ObjectRawPosition`
- `ObjectType` 独立页面（但当前 Getting Started 已确认调用 `ObjectType(object)`）

### Units

- `DynamicFlags`
- `GetUnitBoundingRadius`
- `GetUnitCreatedBy`
- `UnitFlags`
- `UnitFlags2`
- `UnitFlags3`
- `GetUnitIsTapped` ⚠️
- `GetUnitLootable`
- `GetUnitSummonedBy`
- `UnitTarget`
- `ObjectSkinType` ⚠️
- `UnitFacing`

### Movement

- `GetCorpsePosition` 当前正文（旧镜像有）
- `GetPitch`
- `LastTerrainClick`
- `SetPitch`

### Targeting

- `SetMouseover` 当前正文（旧镜像有）
- `UnitTarget`
- `CastTarget`
- `PlayerTarget`

### HTTP

- `HTTPGet` ⚠️
- `HTTPPost` ⚠️

### Misc

- `GetSessionId`
- `GetSessionIndex`

### General

- 当前 `API Summary` 页面抓取受限。
- 当前 `Scripts` 页面抓取受限。
- `ObjectManager(type)` 与 `ObjectPointer` 在当前 Guidelines 中被点名，但没有从当前侧栏抓到单独可读正文。

## 当前页面存在但内容不完整

- `LibDraw`：官方正文仍是 TODO。

## 当前文档明显不一致

- `SetNPCObject` 页面代码块疑似写错函数名。
- `ObjectUnitId` 正文拼写为 `ObjetUnitId`。
- `UnitCreatureTypeId` return prose 出现不相关 loot 文案。
- `ScreenToWorld` 页面 heading 误写 `GetFocus`。
- `json.encode` 返回类型字段与正文语义矛盾。
- `json.decode` 参数类型字段与正文语义矛盾。
- `HTTP:Request` body 字段出现 `params` / `body` 两种写法。

## 补全优先级

### P0：决定循环框架性能/结构

1. `ObjectManager(type)`
2. `ObjectPointer`
3. `ObjectType`
4. `UnitFacing`
5. `ObjectRawPosition`

### P1：账号/多开/授权

1. `GetSessionId`
2. `GetSessionIndex`
3. 继续确认 `GetWowAccount` 在多 Wow1/Wow2、不同角色、重启客户端下的稳定性

### P1：目标管理

1. `UnitTarget`
2. `CastTarget`
3. `PlayerTarget`
4. `SetMouseover`

### P2：高级 Unit metadata

- `UnitFlags*`
- `DynamicFlags`
- creator/summoner APIs
- bounding radius/height
- loot/tap/skin APIs

这些并不是第一版纯 DPS rotation 的阻塞项。

## 不能做的推断

以下规则是硬约束：

- 页面 403 ≠ API 不存在。
- 侧栏存在 ≠ 我们知道参数。
- 旧镜像签名 ≠ 当前签名。
- 函数名很直观 ≠ 返回类型可猜。
- 普通 WoW Lua 的同名/相似 API ≠ NilName API 契约。

## 后续补全方法

1. 继续利用当前官方页面内部链接和搜索引擎缓存。
2. 对比旧 IPFS 文档镜像，但只做历史提示。
3. NilName 客户端到手后，对 P0/P1 API 运行 capability probe，输出 `type(fn)`、最小合法调用和返回 shape。
4. Probe 通过后把条目从 `CURRENT_INDEX_ONLY` 提升为 `RUNTIME_CONFIRMED`，并记录产品版本/Build。
