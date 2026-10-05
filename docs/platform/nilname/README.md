# NilName / NoName Platform Research

> Updated: 2026-08-17

本目录维护“魔兽循环”项目对 NilName/NoName 的平台能力研究。当前定位不是把 NilName 当成 Workout 风格的现成 Rotation Host，而是把它视为：

```text
Unlocker / Lua Runtime
+ Object Manager
+ Position / Geometry
+ Navigation
+ HTTP / Crypto / FileSystem
        ↓
我们自己的 Sirus Rotation Framework
```

## 当前资料

- `API_CATALOG.md` — 当前官方文档 + legacy mirror 的人工可读 API 目录
- `api_catalog.json` — 机器可读 API catalog，供 Codex/工具链消费
- `NILNAME_API_WHITELIST.md` — 当前允许 Probe 的接口与禁止项
- `FRAMEWORK_REQUIREMENTS.md` — 在 NilName 上自行搭建 Rotation Framework 的需求拆解
- `LEGACY_CURRENT_DIFF.md` — legacy/current 文档差异
- `FETCH_GAPS.md` — 当前 403 / index-only / TODO 缺口
- `SOURCES.md` — 来源记录
- `CLIENT_AUDIT_2026-08-17.md` — 用户提供 NilName 客户端静态审计
- `BADROTATIONS_NN_ADAPTER_AUDIT.md` — BadRotations NN adapter / pre-12.1 Midnight Secret-value 兼容层审计
- `NN_AURA_ECOSYSTEM_CROSSVALIDATION.md` — NilName Aura 生态交叉验证；已区分 pre-12.1 与 post-refactor 证据
- `NN_12_1_POST_REFACTOR_AURA_AUDIT.md` — **当前 12.1 Aura 结论的主审计文件**
- `AURA_SECRET_DIRECT_PROBE_SPEC.md` — 已升级为 12.1 interface capability matrix 的实机 Probe 规格

## 关键研究结论

### 1. NilName 不是 Workout 风格的高层循环框架

NilName 官方开发资料与用户提供客户端都支持这一判断：脚本运行在 NilName/WoW Lua 环境上，由开发者自己组织 ticker、状态、对象扫描、施法、导航和业务逻辑。

所以 Sirus 应把 NilName 作为第一个 platform backend，而不是把职业循环写死在 NilName API 上。

### 2. 必须严格区分 12.0/Midnight Secret 与 12.1 Aura Refactor

BadRotations 2026-03/04 的公开 NN adapter 证明了一个重要的 **pre-12.1** 能力模型：NilName 环境存在 Secret-value compatibility 路径，公开框架会对 AuraData、`C_Spell`、CombatLog 等做 Secret-aware normalization。

但 Blizzard 在 2026-06-18 公布 12.1 Aura refactor，目标是阻止 Aura 数据泄露可用于 combat automation 的底层信息，并新增面向显示的 Aura APIs。

12.1 后的公开普通-addon代码进一步证明：index / slot / auraInstanceID Aura reads 在 restricted combat 中可能直接 hard-error，`UNIT_AURA` payload 也不能再按旧的可读 delta 模型消费。

因此：

```text
BadRotations pre-refactor direct Aura + secretunwrap
!=
12.1 post-refactor confirmed solution
```

旧的“12.1 已由 direct index + unwrap 交叉确认”结论已废止。

### 3. 12.1 在 NilName 上仍有很强的生产可行性证据

`medi8tor/AscendedRotation_Midnight` 在 2026-08-16/17 的公开 release history 明确发布多个 `Midnight 12.1` rotation 更新，包括 Outlaw、Affliction、Unholy 等。

这意味着：

```text
12.1_NN_ROTATION_VIABILITY = HIGH_EXTERNAL_CONFIDENCE
```

但是它的发行主体为 protected `.nn`，无法从公开 release 包确认它现在的 Aura truth source，所以：

```text
12.1_NN_AURA_IMPLEMENTATION = UNKNOWN_PENDING_LOCAL_PROBE
```

Lunar、Clipper、Go Hands Free、NilName 自带 rotations、PrimeKitCore 等当前只能作为 ecosystem/support evidence，不能猜它们使用什么 Aura 方案。

### 4. Sirus Aura Engine 改为 capability-routed provider

在实机结果出来前，不预设“direct provider 一定第一”。候选 provider：

```text
NN_NATIVE_PROVIDER
NN_PRIVILEGED_IDENTIFIER
NN_PRIVILEGED_INDEX
WOW_IDENTIFIER_FALLBACK
EVENT_CACHE
MECHANIC_RECONSTRUCTION
```

当前 Probe 要同时比较 ordinary WoW 与 NilName privileged execution，并覆盖 index/slot/instance、by-spellID/by-name、`UNIT_AURA`、Secret unwrap、player/target/non-target object。

### 5. Object snapshot 仍应统一

成熟框架参考仍支持：同一 Tick 只获取一次 object snapshot，让 Targeting / Aura / TTD / AoE 共享一致状态切片。这个架构原则不依赖 12.1 Aura 具体 provider，继续保留。

### 6. GPL 边界不变

BadRotations 使用 GPL-3.0。Sirus 不复制其实现代码，只吸收公开事实、API 线索、测试方法和架构经验，并按自己的接口契约 clean-room 实现。

## 下一阶段 Gate

在开始 Sirus Core 或职业循环前，优先完成：

1. Pure NilName 环境，禁用 `_PrimeKitCore.nn`
2. 当前 12.1 Aura restriction baseline
3. ordinary index/slot/instance API control group
4. by-spellID / by-name identifier API control group
5. `C_Timer.Nn / issecretvalue / secretunwrap` 当前 runtime discovery
6. 相同 Aura API 在 NN privileged environment 下复测
7. runtime discovery 是否存在明确 NN-native Aura provider
8. player / self-proc / target / non-target-object Aura capability matrix
9. `C_Spell` / CombatLog / UnitHealth / UnitHealthMax capability matrix
10. 冻结第一版 `NILNAME_WOW_12_1_COMPAT_MATRIX` 和 runtime-confirmed whitelist
