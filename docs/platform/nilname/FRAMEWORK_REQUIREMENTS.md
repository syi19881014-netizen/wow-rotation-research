# Sirus on NilName — Framework Requirements

> Updated: 2026-08-17

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
        ├─ Aura Provider
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

## 5. SecretValue Adapter — 12.1 新增的核心要求

BadRotations 当前 NN adapter 为我们提供了强外部证据：Midnight NN runtime 可能暴露：

- `issecretvalue`
- `secretunwrap`

并且成熟 framework 把其用于 AuraData、`C_Spell`、CombatLog 等 rotation-critical 数据。

所以 Sirus 必须单独建立：

```text
Platform/NilName/SecretValueAdapter
```

职责：

- detect secret-wrapped scalar；
- unwrap scalar；
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

## 6. Aura Engine

新的 provider 顺序：

```text
NilName Direct Aura Provider
        ↓
Event Cache
        ↓
Mechanic Reconstruction
```

### Direct provider

如果 `AURA_SECRET_DIRECT_PROBE_SPEC.md` 通过，直接读取 AuraData 并由 SecretValueAdapter 正常化。

### Event cache

即便 Direct 可用，仍保留：

- applied/refresh/remove 变化触发；
- direct 结果交叉校验；
- stale state recovery；
- proc history；
- TTD / damage history 输入。

### Reconstruction

只用于 direct/event 均不能完整覆盖的个别效果。必须有 confidence 标记：

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

BadRotations 线索表明 `C_Spell` 也可能受到 secret wrapping，因此 Spell Provider 必须经过 SecretValueAdapter，而不是直接把 `C_Spell` table 交给 APL。

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

开发前必须确认 health 对 non-target NN objects 在 combat 中可读，并确定是否需要 SecretValueAdapter。

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

统一输出 NORMALIZED_EVENT。

如果 CombatLog 字段 secret-wrapped：

```text
CombatLogGetCurrentEventInfo
→ NilName SecretValueAdapter
→ NORMALIZED_EVENT
```

Event consumers 不应知道 secret wrapper。

## 13. Logging / Profiler

至少记录：

- Tick cost
- Object scan cost
- Aura query count/cost
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

UI 只消费状态，不驱动 combat runtime。未来可实现 Sirus 控制台，但第一阶段 runtime/Aura/GCD/TTD 未确认前不要投入 UI。

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
3. SecretValue direct-path probe
4. Aura player/target/non-target object
5. C_Spell secret-sensitive fields
6. CombatLog secret-sensitive fields
7. Health/TTD inputs
8. Object snapshot semantics/performance
9. Cast/GCD semantics
10. Ground-target minimum proof

然后冻结：

```text
NILNAME_API_WHITELIST v1
NILNAME_SECRET_CAPABILITY_MATRIX v1
NILNAME_WOW_API_COMPAT_MATRIX v1
```

再开始职业 Rotation Module 迁移。
