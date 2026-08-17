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
- `BADROTATIONS_NN_ADAPTER_AUDIT.md` — BadRotations 当前 NN adapter / Midnight secret-value 兼容层审计
- `AURA_SECRET_DIRECT_PROBE_SPEC.md` — 12.1 Aura Secret direct-path 实机 Probe 规格

## 关键研究结论

### 1. NilName 不是 Workout 风格的高层循环框架

NilName 官方开发资料与用户提供客户端都支持这一判断：脚本运行在 NilName/WoW Lua 环境上，由开发者自己组织 ticker、状态、对象扫描、施法、导航和业务逻辑。

所以 Sirus 应把 NilName 作为第一个 platform backend，而不是把职业循环写死在 NilName API 上。

### 2. 12.1 Aura 研究出现重要突破线索

公开的 `CuteOne/BadRotations` 当前 NN adapter 在 2026-03-27 的 `Initial Midnight NN support` 中新增了 secret-value compatibility layer，并从 NilName 环境引用：

- `issecretvalue`
- `secretunwrap`

随后它把同一转换思路用于：

- AuraData
- `C_Spell`
- `CombatLogGetCurrentEventInfo()`

并在 2026-04-20 增加 `C_UnitAuras` proxy。

这意味着目前最强公开证据已经从“12.1 Aura 也许只能靠 cache 重建”升级为：

> **NilName 很可能存在可直接把 Midnight secret-wrapped rotation data 转成普通 Lua 值的 runtime path。**

但这仍不是本地实机确认。正式 Sirus Aura Engine 前，必须按 `AURA_SECRET_DIRECT_PROBE_SPEC.md` 在用户当前 NN + WoW 12.1 环境确认。

### 3. Aura direct provider 应优先于 reconstruction

当前推荐顺序：

```text
NilName Direct / Secret Unwrap
        ↓
Event Cache（验证、恢复、事件触发）
        ↓
Mechanic Reconstruction（例外 fallback）
```

只有 direct path 不完整时才扩大 Event/cache reconstruction。

### 4. Object snapshot 应统一

成熟框架参考显示，同一 Tick 应只获取一次 object snapshot，让 Targeting / Aura / TTD / AoE 共享同一状态切片，避免高频枚举产生 count/index 不一致。

### 5. BadRotations 只作为研究参考

BadRotations 使用 GPL-3.0。除非未来明确选择 GPL-3.0 兼容发布方式，否则 Sirus 不复制其实现代码，只吸收公开事实、接口线索、测试方法与架构经验，并按自己的接口契约 clean-room 实现。

## 下一阶段 Gate

在开始 Sirus Core 或职业循环前，优先完成：

1. Pure NilName 环境，禁用 `_PrimeKitCore.nn`
2. `C_Timer.Nn / issecretvalue / secretunwrap` runtime discovery
3. player / target / non-target-object Aura direct path
4. `C_Spell` secret path
5. CombatLog secret path
6. UnitHealth / UnitHealthMax / TTD inputs
7. 然后冻结第一版 runtime-confirmed whitelist
