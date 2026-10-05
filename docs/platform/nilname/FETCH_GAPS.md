# NilName API Fetch / Runtime Gaps

> Updated: 2026-08-17 after WoW 12.1 Aura-refactor audit

本文件只记录当前尚未被官方正文、用户客户端静态审计或本地 runtime probe 完全确认的缺口。不要用函数名猜签名。

## 1. Current docs index-only / body unavailable

当前官方导航明确出现，但正文抓取受限或尚未完整获得的接口包括：

### Objects
- ObjectBoundingRadius
- ObjectFlags
- ObjectHeight
- ObjectLootable
- ObjectRawPosition
- ObjectUnitId

### Units
- DynamicFlags
- GetUnitBoundingRadius
- GetUnitCreatedBy
- UnitFlags
- UnitFlags2
- UnitFlags3
- GetUnitIsTapped
- GetUnitLootable
- GetUnitSummonedBy
- UnitTarget
- ObjectSkinType
- UnitCreatureTypeId
- UnitFacing

### Targeting
- SetMouseover
- SetNPCObject
- UnitTarget
- CastTarget
- PlayerTarget

### Movement
- GetCorpsePosition
- GetPitch
- LastTerrainClick
- SetPitch

### Misc
- GetSessionId
- GetSessionIndex

## 2. ObjectManager performance path

Guidelines 明确建议优先 `ObjectManager(type)`，避免每帧对全部对象执行 `ObjectType`，但当前需要进一步取得/验证它的当前签名和返回 shape。

这是 Sirus 性能关键路径，正式 Object Cache 前必须补齐。

## 3. 12.1 Aura — 当前最高优先级 runtime gap

必须严格区分：

```text
pre-12.1 Midnight Secret-value handling
!=
12.1 Curse of Ula'tek Aura-refactor behavior
```

### 已确认的 pre-12.1 external evidence

BadRotations 的公开 NN adapter 在 2026-03/04 显示过：

- `C_Timer.Nn`
- `issecretvalue`
- `secretunwrap`
- AuraData / `C_Spell` / CombatLog Secret normalization

这些只能标：

```text
PRE_12_1_EXTERNAL_FRAMEWORK_OBSERVED
```

### 已确认的 post-12.1 ordinary-addon baseline

公开 12.1 addon 实现显示：

- index / slot / auraInstanceID family 在 Aura restricted combat 中可能 hard-error；
- `UNIT_AURA` payload 不再能按旧的普通 delta 数据消费；
- by-spellID / by-name identifier reads 可以为部分 Aura 提供有限查询路径。

### 已确认的 post-12.1 NilName viability

Ascended Rotation Midnight 在 2026-08-16/17 发布多个 explicit `Midnight 12.1` rotation updates，包括 Outlaw、Affliction、Unholy。

因此：

```text
12.1_NN_ROTATION_VIABILITY = HIGH_EXTERNAL_CONFIDENCE
12.1_NN_AURA_IMPLEMENTATION = UNKNOWN
```

### 必须回答的问题

1. 当前用户 NN build 是否仍暴露 `C_Timer.Nn`？
2. Secret detector / unwrap primitive 是否仍存在？
3. ordinary `GetAuraDataByIndex` 在 unrestricted/restricted 状态分别如何？
4. 相同 index call 在 NN privileged execution 下是否仍 hard-error？
5. slot / auraInstanceID family 行为如何？
6. `GetUnitAuraBySpellID` / `GetAuraDataBySpellName` 当前存在且可覆盖哪些 Aura？
7. NN privileged identifier reads 是否能返回普通/可 unwrap 的 AuraData？
8. runtime 是否暴露一个明确 NN-native Aura provider？
9. player/self-proc/target/non-target object 覆盖率分别如何？
10. `spellId/applications/duration/expirationTime/sourceUnit/points` 哪些可转成 ordinary Lua state？
11. `UNIT_AURA` 是完整数据源、Secret payload，还是只能当 invalidation signal？
12. zone/reload/combat/target swap 后是否稳定？

在这组问题得到本地答案前，不得把任何一个 Aura provider 写成生产 truth source。

详见：

- `NN_12_1_POST_REFACTOR_AURA_AUDIT.md`
- `AURA_SECRET_DIRECT_PROBE_SPEC.md`

## 4. Health / TTD runtime gap

Pre-12.1 mature NN adapter evidence暗示 `UnitHealth/UnitHealthMax` 可通过 NN object/unit bridge 使用，但用户当前 12.1 环境仍需实测：

- target
- 非当前 enemy object
- combat 中
- 高频采样
- 是否 Secret / 是否需要当前 runtime normalization

TTD Engine 开发应等这条数据源确认后再开始。

## 5. Navigation mesh gap

用户提供客户端包含 NilName navigation executable，但 `mmaps/` 只有下载说明，缺少 retail mesh bundle。

因此当前客户端包不能视为 navigation-ready。未来测试 `GeneratePath` 前先安装匹配当前 Retail 的 mesh bundle。

## 6. PrimeKit contamination risk

用户包内 `_PrimeKitCore.nn` 为自动加载的第三方 framework。所有 NilName native capability probe 必须在 PrimeKit 禁用/隔离状态下进行，否则无法判断函数来自 NN 还是 PrimeKit。

## 7. Protected `.nn` modules

`.nn` 文件为受保护/混淆的 Lua 5.1 bytecode。当前研究不尝试绕过其保护，也不把逆向 PrimeKit/Ascended 当成 API 发现方法。

优先顺序：

```text
官方文档 / Blizzard current API evidence
→ 公开框架源码/commit evidence
→ NilName runtime namespace discovery
→ 黑盒 capability probe
→ 必要时向作者确认
```

而不是破解第三方 `.nn`。
