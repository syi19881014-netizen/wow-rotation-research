# NilName API Catalog

抓取基线：2026-08-17。  
本表以当前 `docs.nilname.com` 侧栏为目录基线；正文能读取的接口记录签名，403/正文缺失的只记录存在性，**不猜参数**。

## 1. Bootstrap / Scripts / Unlock

| API/能力 | 已知签名/行为 | 状态 | 框架用途 |
|---|---|---|---|
| Script loading | `.lua` 放入 `/scripts/`；进入游戏世界或 `/reload` 后执行 | `CURRENT_BODY_CAPTURED` | bootstrap |
| NilName object | `local nn = ...` | `CURRENT_BODY_CAPTURED` | 获取 NilName 对象/方法 |
| `Unlock` | `Unlock(function_or_name, ...)`；当前入门示例 `Unlock(CastSpellByName, "Fishing")`，旧镜像还展示函数名字符串/函数引用两种形式 | `CURRENT_BODY_CAPTURED` + legacy detail | 调用受保护 WoW API |
| Scheduler | 官方示例自行使用 `C_Timer.After(...)` 重复调用 | `CURRENT_BODY_CAPTURED` | 证明 NilName 不替开发者提供 Workout 式 Main tick |

## 2. Targeting

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `GetFocus` | `GetFocus() -> object` | `CURRENT_BODY_CAPTURED` | 使用 `Object('focus')` 的优化桥接 |
| `GetMouseover` | `GetMouseover() -> object` | `CURRENT_BODY_CAPTURED` | 当前正文已见到 |
| `GetNPCObject` | `GetNPCObject() -> object` | `CURRENT_BODY_CAPTURED` | 优化桥接 |
| `SetFocus` | `SetFocus(object)` | `CURRENT_BODY_CAPTURED` | 将 Nn object 暴露为 WoW `focus` token |
| `SetMouseover` | 当前侧栏确认；旧镜像：`SetMouseover(object)` | `LEGACY_MIRROR_CAPTURED` | 当前正文待补 |
| `SetNPCObject` | 预期 `SetNPCObject(object)` | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 当前页面代码块误写成 `SetFocus(object)` |
| `UnitTarget` | 存在 | `CURRENT_INDEX_ONLY` | 签名待补 |
| `CastTarget` | 存在 | `CURRENT_INDEX_ONLY` | 签名待补 |
| `PlayerTarget` | 存在 | `CURRENT_INDEX_ONLY` | 签名待补 |

## 3. Objects / Object Manager

| API | 当前已知签名/返回 | 状态 | 备注/风险 |
|---|---|---|---|
| `Object` | `Object(token) -> object` | `CURRENT_BODY_CAPTURED` | token 如 `player`,`target`,`focus`；可组合 token |
| `ObjectPointer` | Guidelines 提及为高性能接口 | `CURRENT_INDEX_ONLY` | 当前侧栏无独立页；签名未知 |
| `ObjectManager` | Guidelines 明确建议 `ObjectManager(type)` 获得指定类型对象表 | `CURRENT_INDEX_ONLY` | 性能关键；独立页面暂未抓到 |
| `Objects` / `GetObjects` | `Objects() -> table<object>` | `CURRENT_BODY_CAPTURED` | 开放世界通常约玩家周围 100 码，小副本可能覆盖全部 |
| `ObjectAnimationFlag` | `ObjectAnimationFlag(object) -> number` | `CURRENT_BODY_CAPTURED` | animation flag |
| `ObjectBoundingRadius` | 存在 | `CURRENT_INDEX_ONLY` | 正文 403 |
| `ObjectExists` | `ObjectExists(object) -> bool` | `CURRENT_BODY_CAPTURED` | 缓存 object ID 时重要 |
| `ObjectFacing` | `ObjectFacing(object) -> radians` | `CURRENT_BODY_CAPTURED` | 0..2π |
| `ObjectField` | `ObjectField(object, offset, type) -> data` | `CURRENT_BODY_CAPTURED` | **ADVANCED_UNSAFE**；直接 descriptor/memory offset，硬编码 offset 易版本崩溃 |
| `ObjectFlags` | 存在 | `CURRENT_INDEX_ONLY` | 正文 403 |
| `ObjectHeight` | 存在 | `CURRENT_INDEX_ONLY` | 正文 403 |
| `ObjectId` | `ObjectId(object) -> number` | `CURRENT_BODY_CAPTURED` | GameObject ID |
| `ObjectInteract` | `ObjectInteract(object) -> bool/status` | `CURRENT_BODY_CAPTURED` | CTM 开启且距离不足时可能向对象移动 |
| `ObjectLootable` | 存在 | `CURRENT_INDEX_ONLY` | 正文未取到 |
| `ObjectName` | `ObjectName(object) -> string` | `CURRENT_BODY_CAPTURED` | 可能返回 `Unknown` |
| `ObjectPosition` | `ObjectPosition(object) -> x,y,z` | `CURRENT_BODY_CAPTURED` | 世界 XYZ；mover/transport 场景看 RawPosition 注释 |
| `ObjectRawPosition` | 存在 | `CURRENT_INDEX_ONLY` | 当前正文 403；用于相对/原始位置的语义需补证 |
| `ObjectSkinnable` | `ObjectSkinnable(object) -> bool` | `CURRENT_BODY_CAPTURED` | skin 状态 |
| `ObjectType` | `ObjectType(object) -> typeId`（入门示例确认） | `CURRENT_INDEX_ONLY` + current example | 类型枚举在开发入门页给出；官方警告跨版本/产品可能变化 |
| `GameObjectType` | `GameObjectType(object) -> number` | `CURRENT_BODY_CAPTURED` | 与通用 `ObjectType` 不同 |
| `ObjectUnitId` | `ObjectUnitId(object) -> NPC id`（侧栏名） | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 页面正文拼成 `ObjetUnitId` |

### ObjectType 当前入门页枚举

`Object=0, Item=1, Container=2, AzeriteEmpoweredItem=3, AzeriteItem=4, Unit=5, Player=6, ActivePlayer=7, GameObject=8, DynamicObject=9, Corpse=10, AreaTrigger=11, SceneObject=12, Conversation=13`。

**不要固化为永久 ABI。** 官方明确提示 expansion/product 变化可能改变类型定义。

## 4. Units

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `CombatReach` | `CombatReach(object) -> number` | `CURRENT_BODY_CAPTURED` | 近战/命中距离建模 |
| `DynamicFlags` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `GetUnitBoundingRadius` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `GetUnitCreatedBy` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `UnitFlags` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `UnitFlags2` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `UnitFlags3` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `GetUnitIsTapped` | 存在，页面带 ⚠️ | `CURRENT_INDEX_ONLY` | 谨慎使用 |
| `GetUnitLootable` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `GetUnitSummonedBy` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `UnitTarget` | 存在 | `CURRENT_INDEX_ONLY` | Units/Targeting 均出现 |
| `ObjectSkinType` | 存在，页面带 ⚠️ | `CURRENT_INDEX_ONLY` | 谨慎使用 |
| `ObjectSkinnable` | 存在 | `CURRENT_BODY_CAPTURED`（Objects 路径） | 重复分类 |
| `UnitCreatureTypeId` | `UnitCreatureTypeId(object) -> number` | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 页面 return prose 有明显复制粘贴错误；类型列表仍可用 |
| `UnitFacing` | 存在 | `CURRENT_INDEX_ONLY` | 正文 403 |
| `UnitMovementFlag` | `UnitMovementFlag(object) -> number` | `CURRENT_BODY_CAPTURED` | bit flags：前后移动/跳跃/坠落/飞行等 |

## 5. Movement / Navigation / Geometry

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `GenerateLocalPath` | `GenerateLocalPath(map,x1,y1,z1,x2,y2,z2,errorCallback,smooth) -> points` | `CURRENT_BODY_CAPTURED` | 本地同步；需要 `NnNav.exe` + mmaps；长距离建议分段 |
| `GeneratePath` | `GeneratePath(map,x1,y1,z1,x2,y2,z2,callback,smooth,errorCallback)` | `CURRENT_BODY_CAPTURED` | 远程/异步 pathing；callback 接收 path |
| `ClickPosition` | `ClickPosition(x,y,z)` | `CURRENT_BODY_CAPTURED` | 3D 左键点击；官方明确指出常用于 **AoE spellcasting**，不是 CTM |
| `ClickToMove` | `ClickToMove(x,y,z)` | `CURRENT_BODY_CAPTURED` | 直接向 XYZ 移动 |
| `GetCameraPosition` | `GetCameraPosition() -> x,y,z` | `CURRENT_BODY_CAPTURED` | camera XYZ |
| `GetCorpsePosition` | 当前存在；旧镜像 `GetCorpsePosition()`，标 Experimental | `LEGACY_MIRROR_CAPTURED` | 当前正文待补 |
| `GetPitch` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `LastTerrainClick` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `SendMovementHeartbeat` | `SendMovementHeartbeat()` | `CURRENT_BODY_CAPTURED` | 同步 facing/movement 到服务器 |
| `SetPitch` | 存在 | `CURRENT_INDEX_ONLY` | 正文缺失 |
| `SetPlayerFacing` | `SetPlayerFacing(facing)` | `CURRENT_BODY_CAPTURED` | 当前文档建议配合 heartbeat；旧版曾有第二个 forceUpdate 参数 |
| `TraceLine` | `TraceLine(x1,y1,z1,x2,y2,z2,flags) -> false OR collision x,y,z` | `CURRENT_BODY_CAPTURED` | 见下方 flags；高频使用需注意空间范围和性能 |
| `ScreenToWorld` | `ScreenToWorld(x,y,flags) -> x,y,z` | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 像素屏幕坐标转 3D，内部用 TraceLine；页面标题误写 GetFocus |
| `WorldToScreen` | `WorldToScreen(x,y,z) -> x,y` | `CURRENT_BODY_CAPTURED` | **当前文档称返回像素**；旧镜像曾称比例坐标，见版本漂移 |

### TraceLine flags（当前正文）

- `M2Collision = 0x1`
- `M2Render = 0x2`
- `WMOCollision = 0x10`
- `WMORender = 0x20`
- `Terrain = 0x100`
- `WaterWalkableLiquid = 0x10000`
- `Liquid = 0x20000`
- `EntityCollision = 0x100000`
- `Unknown = 0x200000`

性能注意：官方说明 TraceLine 会先对向量覆盖范围内对象做包围盒类检查，因此超长向量高频调用可能增加开销。

## 6. Utils

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `LibDraw` | 页面存在但正文 TODO | `CURRENT_TODO` | 不能据此设计生产绘制层 |
| `json.encode` | `json.encode(table) -> JSON string` | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 页面 return type 标 number，与 prose/语义矛盾 |
| `json.decode` | `json.decode(jsonstr) -> table/value` | `CURRENT_BODY_CAPTURED` + `DOC_INCONSISTENCY` | 页面把 jsonstr 类型写成 number，明显不一致 |

Guidelines 另列内置库：

- `NoName.Utils.JSON`
- `NoName.Utils.Draw:New()`
- `NoName.Utils.LibStub`
- `NoName.Utils.sha`
- `NoName.Utils.AES`
- `NoName.Utils.AceGUI`
- `NoName.Utils.Storage.read` / `NoName.Utils.Storage.write`

## 7. HTTP

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `HTTP:Request` | `HTTP:Request(options)` | `CURRENT_BODY_CAPTURED` | **推荐 HTTP 入口** |
| `HTTPGet` | 存在，页面带 ⚠️ | `CURRENT_INDEX_ONLY` | 可能为旧/不推荐入口；不纳入首选白名单 |
| `HTTPPost` | 存在，页面带 ⚠️ | `CURRENT_INDEX_ONLY` | 同上 |

`HTTP:Request` 当前 options：

- `url`：required
- `method`：required，文档示例/说明允许 GET/PUT/POST/OPTIONS 等字符串
- `callback`：optional；示例回调形如 `(status, result)`
- `headers`：optional
- request body：文档 prose 与示例分别出现 `params` / `body` 命名，**需实机确认或以后补正文版本**
- `pin`：optional certificate pinning

## 8. Misc / Identity

| API | 当前已知签名/返回 | 状态 | 备注 |
|---|---|---|---|
| `GetKeyState` | `GetKeyState(virtKey) -> flags` | `CURRENT_BODY_CAPTURED` | Windows virtual key；高 bit 表示 down，低 bit 表示 toggled |
| `SetNavHost` | `SetNavHost(hosturl)` | `CURRENT_BODY_CAPTURED` | 默认 localhost；影响 GenerateLocalPath / GeneratePath |
| `GetSessionId` | 存在 | `CURRENT_INDEX_ONLY` | 身份/会话用途值得重点补抓 |
| `GetWowAccount` | `GetWowAccount() -> string` | `CURRENT_BODY_CAPTURED` | 文档称对 Battle.net + game-account 组合唯一；适合授权绑定候选 |
| `GetSessionIndex` | 存在 | `CURRENT_INDEX_ONLY` | 正文 403 |

## 9. FileSystem

| API | 已知签名/返回 | 状态 |
|---|---|---|
| `FileExists` | `FileExists(path) -> bool` | `CURRENT_BODY_CAPTURED` |
| `ReadFile` | `ReadFile(path) -> contents` | `CURRENT_BODY_CAPTURED` |
| `WriteFile` | `WriteFile(path, data [, append])` | `CURRENT_BODY_CAPTURED` |
| `DeleteFile` | `DeleteFile(path)` | `CURRENT_BODY_CAPTURED` |
| `DirectoryExists` | `DirectoryExists(path) -> bool` | `CURRENT_BODY_CAPTURED` |
| `CreateDirectory` | `CreateDirectory(path)` | `CURRENT_BODY_CAPTURED` |
| `DeleteDirectory` | `DeleteDirectory(path)` | `CURRENT_BODY_CAPTURED` |
| `ListFiles` | `ListFiles(path) -> list/table` | `CURRENT_BODY_CAPTURED` |

路径语义：当前文档说明，以 `/` 或 `\` 开头的路径从 unlocker base directory 解析；不带前导分隔符时可以相对 WoW 目录解析。正式框架必须统一自己的 path policy，避免把授权缓存和开发文件写错位置。

## 10. Cryptography

当前文档暴露的是内置 Lua crypto 库，不是单一全局 API。

| API | 已知签名/用途 | 状态 |
|---|---|---|
| AES namespace | `local aes = NoName.Utils.AES` | `CURRENT_BODY_CAPTURED` |
| `LoadScriptAES256CBC` | `aes.LoadScriptAES256CBC(filepath, password, iv)` | `CURRENT_BODY_CAPTURED` |
| `RunScriptAES256CBC` | `aes.RunScriptAES256CBC(data, password, iv)` | `CURRENT_BODY_CAPTURED` |
| AES encrypt | `aes.encrypt(...)`，支持 AES128/192/256 + ECB/CBC/OFB/CFB/CTR | `CURRENT_BODY_CAPTURED` |
| AES decrypt | `aes.decrypt(...)` | `CURRENT_BODY_CAPTURED` |
| SHA namespace | `NoName.Utils.sha` | `CURRENT_BODY_CAPTURED` |
| SHA256 | `sha.sha256(data/rawfile)` | `CURRENT_BODY_CAPTURED` |
| HMAC-SHA256 | `sha.hmac_sha256(key, text)` | `CURRENT_BODY_CAPTURED` |

文档中 AES namespace 大小写/示例存在轻微不一致，因此实现时不要直接复制未验证示例；先做最小 crypto compatibility test。

## 11. Guidelines / Performance 规则

当前 Guidelines 明确建议优先使用以下优化路径：

- `Object` / `ObjectPointer`
- `GetFocus`（内部使用 `Object('focus')`）
- `GetNPCObject`（内部使用 `Object('npc')`）
- `SetFocus`
- `SetNPCObject`
- `ObjectType`
- `ObjectExists`
- `ObjectField`

尤其重要：**不要在每个 object 上反复调用 `ObjectType`；优先 `ObjectManager(type)` 直接取得已按类型筛选的 table。**

这意味着未来我们的 Object Cache 应该是“按类型一次抓取 + 帧内缓存”，而不是每 tick 全对象 O(N) 类型探测再 O(N²) 重算。

## 12. 旧镜像额外出现、当前未正式确认的 API

以下仅作为迁移研究线索，不进入正式白名单：

| API | 旧镜像已知行为 | 状态 |
|---|---|---|
| `Distance` | `Distance(obj1,obj2)` 或 `Distance(x,y,z,x2,y2,z2)`；不能 object/xyz 混用 | `UNVERIFIED_LEGACY` |
| `GetAnglesBetweenPositions` | 两点坐标求角度 | `UNVERIFIED_LEGACY` |
| `GetPositionFromPosition` | 从起点 + 距离 + XY/XYZ angle 求新位置 | `UNVERIFIED_LEGACY` |
| `UnitSpecializationID` | 对 object/unit 取得 specialization ID（旧文档标 retail only） | `UNVERIFIED_LEGACY` |
| `SetPlayerFacing(direction, forceUpdate)` | 旧签名带 forceUpdate；当前签名改为单参 + heartbeat | `UNVERIFIED_LEGACY` |

## 13. 生产白名单候选（第一阶段）

如果现在就开始写 NilName Rotation Framework，建议只把以下作为第一阶段高可信底层：

### Core object/state
`Object`, `Objects`, `ObjectExists`, `ObjectPosition`, `ObjectFacing`, `ObjectName`, `ObjectId`, `GameObjectType`, `CombatReach`, `UnitMovementFlag`

### Protected actions
`Unlock`

### Geometry / ground AoE
`ClickPosition`, `TraceLine`, `WorldToScreen`, `ScreenToWorld`

### Optional movement
`ClickToMove`, `GenerateLocalPath`, `GeneratePath`, `SetPlayerFacing`, `SendMovementHeartbeat`

### Identity / licensing
`GetWowAccount`, `HTTP:Request`, FileSystem, SHA/HMAC, AES

### Do not use by default
`ObjectField` hardcoded offsets, ⚠️ APIs, current-index-only APIs, legacy-only APIs。
