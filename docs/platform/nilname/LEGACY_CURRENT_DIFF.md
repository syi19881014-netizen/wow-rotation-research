# NilName Current vs Legacy Documentation Drift

本文件记录 2026-08-17 当前 `docs.nilname.com` 与旧官方文档 IPFS 镜像之间可观察到的差异。目的不是恢复旧 API，而是防止未来把旧示例误当作当前契约。

## 证据等级

- **Current**：当前 docs.nilname.com 正文或当前开发入门页。
- **Legacy**：旧 NilName/NoName 文档镜像。
- **Decision**：框架代码应该遵循的规则。

## 1. `WorldToScreen`

### Current

当前页面描述 `WorldToScreen(x,y,z) -> x,y`，并把返回结果描述为屏幕**像素坐标**。

### Legacy

旧镜像曾把返回值描述成比例/归一化坐标（约 -1..1 语义）。

### Decision

**不得根据旧镜像写屏幕换算。** 当前实现以像素语义为候选基线，并在首次 NilName 实机 Probe 用已知屏幕中心点验证。

---

## 2. `SetPlayerFacing`

### Current

`SetPlayerFacing(facing)`；当前文档另有 `SendMovementHeartbeat()`，并说明仅改变客户端 facing 后应通过 heartbeat 同步服务器。

### Legacy

旧文档出现 `SetPlayerFacing(direction, forceUpdate)` 二参数形式。

### Decision

生产代码只接受当前单参数版本；heartbeat 显式调用。旧 `forceUpdate` 参数标为 `UNVERIFIED_LEGACY`。

---

## 3. `Unlock`

### Current

当前开发入门示例证明 `Unlock(CastSpellByName, "Fishing")` 可调用受保护 WoW API。

### Legacy

旧镜像提供更完整说明：第一个参数可为 `_G` 中的函数名字符串或函数引用，并展示 `JumpOrAscendStart`、`CastSpellByName`、`CastSpellByID` 等例子。

### Decision

`Unlock` 本身为当前可用核心接口；但“函数名字符串形式”只视为旧文档增强信息，首次框架 Probe 需要验证。

---

## 4. `SetMouseover`

### Current

当前侧栏确认 `SetMouseover` 页面存在，但正文未成功抓取。

### Legacy

旧镜像明确给出 `SetMouseover(object)`。

### Decision

标 `LEGACY_MIRROR_CAPTURED`，在当前客户端验证前不进入生产白名单。

---

## 5. `GetCorpsePosition`

### Current

当前侧栏有该 API，但正文无法读取。

### Legacy

旧文档给出 `GetCorpsePosition()`，并标 Experimental。

### Decision

仅用于导航/尸体找回实验模块；普通 rotation 不需要。

---

## 6. 旧镜像额外 Utility API

旧镜像出现、当前侧栏未见独立页：

- `Distance(obj1,obj2)` / `Distance(x,y,z,x2,y2,z2)`
- `GetAnglesBetweenPositions(...)`
- `GetPositionFromPosition(...)`
- `UnitSpecializationID(object_or_unit)`

### Decision

全部标 `UNVERIFIED_LEGACY`。

其中 `Distance` 即便当前消失也不构成阻塞：框架可以直接用两个 `ObjectPosition()` 结果做欧氏距离，避免依赖未知 legacy helper。

---

## 7. `ObjectManager(type)` / `ObjectPointer`

这两个接口反而是**当前 Guidelines 提到，但当前侧栏没有清晰独立正文页**的情况。

Current Guidelines 明确：

- `Object / ObjectPointer` 属于优化 API。
- 应避免对每个 object 反复 `ObjectType`，优先 `ObjectManager(type)`。

### Decision

它们不是 legacy；而是 `CURRENT_INDEX_ONLY / GUIDELINES_CONFIRMED_NAME`。

这两个 API 对框架性能非常重要，NilName 实机到手后应作为第一优先级 Probe。

---

## 8. 文档自身错误，不是版本差异

当前文档发现至少以下明显问题：

- `SetNPCObject` 页面代码块疑似误写 `SetFocus(object)`。
- `ObjectUnitId` 页面函数名出现 `ObjetUnitId` 拼写错误。
- `UnitCreatureTypeId` return prose 出现与 loot 有关的复制粘贴文本。
- `ScreenToWorld` 页面 heading 误写成 `GetFocus`。
- `json.encode` return type 写成 number，但语义/正文为 JSON string。
- `json.decode` 输入类型字段写成 number，但参数显然是 JSON string。
- HTTP request body 在正文中出现 `params`，示例中出现 `body`，命名不一致。

### Decision

这些条目统一标 `DOC_INCONSISTENCY`。实现不得仅依赖自动生成的参数表；必须结合语义、当前示例和实机 Probe。

---

## 总体原则

1. Current 正文 > Current Guidelines/入门示例 > Current 侧栏索引 > Legacy mirror。
2. 任何旧签名与当前签名冲突时，一律以当前为候选并实机验证。
3. 不因为旧 API 很方便就把它加入框架依赖。
4. 为版本升级预留 capability detection，避免一个 API 改名导致整个框架无法加载。
