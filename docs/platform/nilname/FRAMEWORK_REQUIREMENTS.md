# Sirus on NilName — Framework Requirements

> Updated: 2026-08-17; 12.1 Aura-refactor correction applied

NilName 应作为 Sirus 的第一个 platform backend，而不是直接把职业 Rotation 写在 NN API 上。

## 1. Target architecture

```text
NilName Runtime / Unlock / WoW Lua
        ↓
Platform/NilName
        ├─ Runtime Adapter
        ├─ SecretValue Adapter
        ├─ Object Adapter
        ├─ Unit Adapter
        ├─ Spell Adapter
        ├─ Aura Capability Router
        │    ├─ NN Native Provider
        │    ├─ NN Privileged Identifier Provider
        │    ├─ NN Privileged Enumeration Provider
        │    └─ WoW Identifier Fallback
        ├─ Event Provider
        ├─ Geometry Adapter
        ├─ Navigation Adapter
        ├─ HTTP/Crypto/File Adapter
        └─ Identity Adapter
                ↓
Sirus Core
        ├─ Scheduler
        ├─ Snapshot
        ├─ Combat State
        ├─ GCD / Action Queue
        ├─ Aura Engine
        ├─ TTD Engine
        ├─ Target Engine
        ├─ AoE Solver
        ├─ APL Engine
        ├─ Logging / Profiler
        └─ Module Host
                ↓
Rotations
```

职业模块只消费 Sirus API，不直接调用 `Unlock`, `Object`, `C_UnitAuras`, `secretunwrap` 等 NilName/WoW backend 细节。

## 2. Scheduler

NilName 不提供 Workout 风格的固定 `Main()` contract，因此我们需要自己的 Scheduler。

要求：

- 可配置 Tick 频率；
- combat 与 out-of-combat 可不同频率；
- 单 Tick 内建立一致 Snapshot；
- 重活分帧/降频；
- 有运行预算与 profiler；
- zone/load/reload 时安全暂停与恢复。

## 3. Object Snapshot

当前成熟 NN framework 参考显示，同一轮对象枚举最好只调用一次 `Objects()`，随后所有消费者共用同一张 snapshot。

Sirus 要求：

```text
Tick N
  Objects() once
     ↓
  ObjectSnapshot[N]
     ├─ Targeting
     ├─ Aura
     ├─ TTD
     ├─ AoE
     └─ Movement
```

这样既减少调用量，也避免 count/index 来自不同瞬间。

## 4. UnitRef normalization

统一引用类型：

```text
player / target / focus / nameplate token
NN object reference
```

上层接口示例：

```text
Sirus.Unit.Exists(ref)
Sirus.Unit.Health(ref)
Sirus.Unit.Position(ref)
Sirus.Aura.Remains(ref, spellID)
Sirus.TTD(ref)
```

Platform/NilName 负责把 UnitRef 转成 NilName/WoW 当前调用实际接受的 representation。

## 5. SecretValue Adapter — pre-12.1 evidence, current runtime gate

BadRotations 的公开 NN adapter 为 **pre-12.1 Midnight** 提供了强外部证据：当时 NilName environment 暴露/可用过类似：

- `issecretvalue`
- `secretunwrap`

成熟 framework 将其用于 AuraData、`C_Spell`、CombatLog 等 rotation-critical 数据。

但 Blizzard 2026-06-18 的 12.1 Aura refactor 改变了 Aura API access model：某些 Aura calls 可能在返回值产生之前就 hard-error。因此 SecretValue Adapter 仍然值得建立，但它**不能被假定为 12.1 Aura 的完整答案**。

Sirus 仍建立：

```text
Platform/NilName/SecretValueAdapter
```

职责：

- detect secret-wrapped scalar；
- unwrap scalar（仅在当前 runtime 证明确实可用时）；
- normalize flat table；
- 对需要的 nested structures 做 schema-aware normalization；
- 类型验证；
- 范围/NaN/invalid 校验；
- error isolation；
- capability flags。

禁止让职业模块自行调用 `secretunwrap`。

### Capability examples

```text
secret.scalar
secret.aura.spellId
secret.aura.duration
secret.aura.expirationTime
secret.aura.points
secret.spell.cooldown
secret.cleu.spellId
secret.health
```

每项 runtime probe 后单独标记，避免“一项成功 = 所有 secret 都可用”的错误推断。

## 6. Aura Engine — 12.1 capability-routed provider

12.1 不再预设固定 provider 顺序。

候选 provider：

```text
NN_NATIVE_PROVIDER
NN_PRIVILEGED_IDENTIFIER
NN_PRIVILEGED_INDEX
WOW_IDENTIFIER_FALLBACK
EVENT_CACHE
MECHANIC_RECONSTRUCTION
```

### Capability router

`AURA_SECRET_DIRECT_PROBE_SPEC.md` 必须先建立当前 build 的 matrix：

- index / slot / auraInstanceID family；
- by-spellID / by-name identifier family；
- ordinary WoW vs NN privileged execution；
- `UNIT_AURA` event semantics；
- runtime-discovered NN-native Aura APIs；
- player / target / non-target NN object coverage。

只有 runtime-proven provider 才进入生产路由。

### Direct/privileged providers

如果某条 current-12.1 path 可以直接取得 rotation 需要的 ordinary framework values，它应作为该 capability 的 truth source。不要因为 pre-12.1 代码存在就假定 index enumeration 一定是这个 provider。

### Event cache

Event/cache 可以承担：

- invalidation / tracked-Aura re-read trigger；
- direct 结果交叉校验；
- stale state recovery；
- proc history；
- TTD / damage history 输入。

如果 12.1 `UNIT_AURA` payload 不可读，但 unit identity 可用，则 event 只作为 invalidation signal。

### Reconstruction

只用于所有 direct/identifier/native paths 都无法完整覆盖的明确效果。必须有 confidence 标记：

```text
CONFIRMED
INFERRED_HIGH
INFERRED_LOW
UNKNOWN
```

重要爆发决策默认不得消费低置信度状态。

## 7. Spell/GCD Engine

需要独立确认 NilName/WoW 12.1 当前：

- cast API semantics；
- protected action 通过 `Unlock` 的调用模式；
- GCD start/duration；
- spell cooldown；
- charges；
- usable/range；
- cast/channel；
- queue/retry 行为；
- ground-target sequence。

Pre-12.1 framework 线索表明 `C_Spell` 也可能受到 secret wrapping，因此 Spell Provider 仍需独立 capability probe，并在需要时经过 SecretValueAdapter，而不是把 `C_Spell` table 直接交给 APL。

## 8. Action Queue

不要继承 Workout PendingAction 的具体实现；在 NilName 上重新实测。

至少需要：

```text
Intent
→ Admission
→ Queue/Retry
→ Execute
→ Confirm/Reject
→ Recover
```

并区分：

- GCD action
- off-GCD action
- ground-target action
- channel/cast protection
- manual override/insertion

## 9. TTD Engine

第一阶段数据源：

- UnitHealth
- UnitHealthMax
- stable UnitRef/object identity
- Event/damage history

输出不要只有一个数字：

```text
TTD_FAST
TTD_MID
TTD_SLOW
TTD_STABLE
confidence
```

还要支持 per-object 与 pack-level TTD。

开发前必须确认 health 对 non-target NN objects 在 combat 中可读，并确定是否 Secret / 是否需要当前 NN runtime 的 normalization。

## 10. Target Engine

输入：

- Object Snapshot
- attackable/dead/visible
- health / TTD
- position / distance / facing
- Aura state
- target priority

输出：

- primary target
- multidot targets
- AoE candidate set
- interrupt target
- swap recommendation

## 11. Ground AoE Solver

NilName 当前官方文档已经提供 `ObjectPosition`, `ClickPosition`, `TraceLine` 等关键底层能力。

Sirus AoE Solver 目标：

```text
Enemy XYZ set
→ candidate centers
→ skill radius scoring
→ priority/TTD weighting
→ terrain/LOS validation
→ best point
→ ground-target execute
```

不能只做“选择最密集那只怪”作为最终方案。

## 12. Event Layer

统一输出 `NORMALIZED_EVENT`。

如果 CombatLog 字段 secret-wrapped 且当前 NN runtime 可以合法/稳定 normalize：

```text
CombatLogGetCurrentEventInfo
→ NilName SecretValueAdapter
→ NORMALIZED_EVENT
```

如果 12.1 某事件 payload 本身不可读，则 Event Provider 必须降级为触发/失效信号，不可伪造 payload。

Event consumers 不应知道 secret wrapper。

## 13. Logging / Profiler

至少记录：

- Tick cost
- Object scan cost
- Aura query count/cost by provider
- Aura hard-error counts
- Secret unwrap count/failures
- TTD update cost
- APL branch
- Intent reject reason
- cast confirm/reject
- ground AoE candidate count
- stale cache recovery

正式框架必须有性能预算，避免把高频 Object/Aura API 每 Tick 无限制重复调用。

## 14. UI

UI 与 Core 解耦。

UI 只消费状态，不驱动 combat runtime。第一阶段 runtime/Aura/GCD/TTD 未确认前不要投入 UI。

## 15. Licensing / Distribution

NilName 已确认的 HTTP/Crypto/File/Identity 能力使未来授权系统可行，但授权不进入第一阶段 Combat Core。

优先顺序：

```text
Combat correctness
→ Stability/performance
→ Rotation modules
→ UI
→ Licensing/distribution
```

## 16. Source-license boundary

BadRotations 为 GPL-3.0。

本项目可以借鉴：

- adapter 分层思想；
- object snapshot 原则；
- secret-value capability 发现；
- probe target；
- 公开 API 名称。

不得在未做 GPL 发布决策前复制其代码实现到 Sirus。

## 17. Pre-Sirus Gates

正式写 Sirus Core 前必须通过：

1. Pure NN loader
2. Runtime namespace discovery
3. 12.1 Aura restriction baseline
4. Ordinary index/slot/instance control group
5. Ordinary identifier-read control group
6. NN privileged execution comparison
7. NN-native Aura provider discovery
8. Aura player/self-proc/target/non-target object matrix
9. C_Spell Secret-sensitive fields
10. CombatLog Secret-sensitive fields
11. Health/TTD inputs
12. Object snapshot semantics/performance
13. Cast/GCD semantics
14. Ground-target minimum proof

然后冻结：

```text
NILNAME_API_WHITELIST v1
NILNAME_SECRET_CAPABILITY_MATRIX v1
NILNAME_WOW_12_1_COMPAT_MATRIX v1
```

再开始职业 Rotation Module 迁移。

## 18. Evidence policy

- March/April 2026 BadRotations/Ascended Secret-Aura behavior = **pre-12.1 architecture evidence**.
- August 2026 Ascended 12.1 releases = **post-refactor viability evidence**, not implementation evidence.
- Only the user's current runtime probe may upgrade an Aura provider to `LOCAL_RUNTIME_CONFIRMED`.
