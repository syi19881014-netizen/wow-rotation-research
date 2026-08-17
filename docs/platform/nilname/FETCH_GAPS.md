# NilName API Fetch / Runtime Gaps

> Updated: 2026-08-17

本文件只记录当前尚未被官方正文、用户客户端静态审计或本地 runtime probe 完全确认的缺口。不要用函数名猜签名。

## 1. Current docs index-only / body unavailable

当前官方导航明确出现，但正文抓取受 403/站点限制或尚未完整获得的接口包括：

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

这属于 Sirus 性能关键路径，正式 Object Cache 前必须补齐。

## 3. 12.1 Aura / Secret Value — 新的最高优先级 runtime gap

BadRotations 当前公开 NN adapter 提供了非常强的外部证据：Midnight NN environment 中存在：

- `C_Timer.Nn`
- `issecretvalue`
- `secretunwrap`

并且成熟框架使用它们处理 AuraData、`C_Spell` 和 CombatLog secret-wrapped values。

但是 NilName 当前公开官方 docs 未检索到这些符号的正式说明，用户提供客户端静态 strings 也没有直接暴露这些名称。因此当前状态只能是：

**`EXTERNAL_FRAMEWORK_OBSERVED / LOCAL_RUNTIME_UNKNOWN`**

必须按 `AURA_SECRET_DIRECT_PROBE_SPEC.md` 实机验证。

### 必须回答的问题

1. 当前用户 NN build 是否真的暴露 `C_Timer.Nn`？
2. `issecretvalue` / `secretunwrap` 是否存在于该 environment？
3. normal value 输入行为是什么？
4. AuraData 的哪些 fields 是 secret？
5. unwrap 后是否得到普通 boolean/number/string？
6. player/target/non-target NN object 是否都可用？
7. nested `points[]` 等字段如何处理？
8. `C_Spell` 和 CombatLog 是否需要同一层？
9. zone/reload/combat/target swap 后是否稳定？

在这组问题得到答案前，不再假定“只能 Event/cache 重建”，也不把 direct unwrap 当生产事实。

## 4. Health / TTD runtime gap

BadRotations NN adapter 的 capability mapping 强烈暗示 `UnitHealth/UnitHealthMax` 可通过 NN object/unit bridge 使用，但用户环境仍需实测：

- target
- 非当前 enemy object
- combat 中
- 高频采样
- 是否 secret / 是否需要 unwrap

TTD Engine 开发应等这条数据源确认后再开始。

## 5. Navigation mesh gap

用户提供客户端包含 NilName navigation executable，但 `mmaps/` 只有下载说明，缺少 retail mesh bundle。

因此当前客户端包**不能视为导航 ready**。未来测试 `GeneratePath` 前先安装匹配当前 Retail 的 mesh bundle。

## 6. PrimeKit contamination risk

用户包内 `_PrimeKitCore.nn` 为自动加载的第三方 framework。所有 NilName native capability probe 必须在 PrimeKit 禁用/隔离状态下进行，否则无法判断函数来自 NN 还是 PrimeKit。

## 7. Protected `.nn` modules

`.nn` 文件为受保护/混淆的 Lua 5.1 bytecode。当前研究不尝试绕过其保护，也不把逆向 PrimeKit 当成 API 发现方法。

优先顺序：

```text
官方文档
→ 公开框架源码证据
→ NilName runtime namespace discovery
→ 黑盒 capability probe
→ 必要时向作者确认
```

而不是破解第三方 `.nn`。
