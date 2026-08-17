# BadRotations NilName Adapter Audit

> 日期：2026-08-17  
> 目的：把公开的成熟 Rotation Framework 对 NilName 的接入方式作为**架构参考与 runtime probe 线索**，不把其代码直接并入 Sirus。

## 1. 来源与版本状态

审计对象：`CuteOne/BadRotations`，默认分支 `master`，重点文件 `Unlockers/nn.lua` 与 `Expansions/Retail/Functions.lua`。

仓库当前为公开、非 archived，许可证为 **GPL-3.0**。GitHub 元数据显示仓库最近 push 时间为 2026-05-26；`nn.lua` 的 2026-03-27 提交明确写有 `Initial Midnight NN support`，随后 2026-04-20 又补了一层 `C_UnitAuras` proxy。

**许可规则：** 本项目只提取架构事实、API 名称、行为假设和测试线索。除非未来明确决定让 Sirus 采用 GPL-3.0 兼容发布方式，否则不要复制 BadRotations 的实现代码。

## 2. 最重要的新发现：Midnight Secret Value 不是只能靠 cache 重建

当前 `Unlockers/nn.lua` 在进入 NilName 环境后会切换执行环境到 `C_Timer.Nn`，随后引用两个关键 runtime symbol：

- `issecretvalue`
- `secretunwrap`

BadRotations 用它们建立三层转换：

1. **scalar unwrap**：函数多返回值中，如果某个值是 secret-wrapped scalar，就先解除包装再返回给框架；
2. **generic table unwrap**：对 `C_Spell` 等返回 table 的字段逐项处理；
3. **Aura-specific unwrap**：对 AuraData table 做专门处理，并额外处理 `points` 这种嵌套数值数组。

这不是旧代码里一直存在的逻辑。对比 2026-03-27 前的父提交，旧 `nn.lua` 只是直接把 `C_UnitAuras.GetAuraDataByIndex/GetBuffDataByIndex/GetDebuffDataByIndex` 的结果返回给框架，没有 secret unwrap。2026-03-27 的 `Initial Midnight NN support` 提交新增了 secret unwrap helpers；2026-04-20 又新增 `C_UnitAuras` proxy，让 Retail compatibility layer 通过统一入口也能得到处理后的 AuraData。

### 当前推论

这构成了目前最强的公开证据：

> **NilName runtime 很可能已经向 framework 暴露了一个“把 Midnight secret-wrapped value 转回普通 Lua value”的能力。**

但这仍然只是 `EXTERNAL_FRAMEWORK_OBSERVED`，不是我们自己的 `RUNTIME_CONFIRMED`。必须在用户提供的当前 NilName + WoW 12.1 环境里实机验证 `C_Timer.Nn.issecretvalue` / `C_Timer.Nn.secretunwrap` 是否存在、签名是否一致、Aura fields 是否真的能解除为普通 Lua 值。

## 3. BadRotations 的 Aura 数据路径

当前 NN adapter 的实际思路可抽象为：

```text
C_UnitAuras index lookup
        ↓
ObjectUnit(unit) 统一 token / NN object
        ↓
AuraData table
        ↓
Secret detection
        ↓
NilName runtime secret unwrap
        ↓
普通 AuraData
        ↓
BadRotations Retail compatibility layer
        ↓
Rotation buff/debuff logic
```

它没有把 12.1 Aura 的主路径设计成“CombatLog 推断 + cache 重建”。至少在当前公开 NN adapter 中，**首选路径是直接读取 C_UnitAuras，然后解除 secret wrapper**。

这和目前外部开发者给用户透露的“有办法直接能用”高度吻合，但不能证明对方使用的是完全相同实现。

## 4. 需要注意的 Aura 实现细节

### 4.1 它优先处理 index-based Aura API

NN adapter 显式包装：

- `GetAuraDataByIndex`
- `GetBuffDataByIndex`
- `GetDebuffDataByIndex`

同时建立 `b.C_UnitAuras` proxy，让 Retail compatibility layer 继续走统一的 `C_UnitAuras` 风格 API。

### 4.2 Object 与 unit token 被统一

BadRotations 使用一个 Object→Unit bridge：数字/object reference 会先经 `Object(...)` 转换，普通字符串 unit token 则直接保留。

对 Sirus 的直接启发：

```text
Sirus UnitRef
├─ player/target/focus/nameplate token
└─ NilName object reference
```

职业模块不应该知道底层是哪一种引用。

### 4.3 nested fields 需要单独处理

AuraData 并不只有平铺 scalar。BadRotations 对 `points` 做了专门处理。这说明 Sirus 不能只写一个“table 第一层字段 unwrap”然后认为全部结束。runtime probe 应覆盖：

- spellId
- applications/stacks
- duration
- expirationTime
- sourceUnit
- isHelpful/isHarmful
- points[]
- 其他嵌套字段

### 4.4 Secret unwrap 不只用于 Aura

当前 adapter 还把相同思想用于：

- NilName environment 中的一批 Unit/全局函数返回值；
- `C_Spell` table/scalar 返回值；
- `CombatLogGetCurrentEventInfo()`。

因此 Sirus 最终更合理的设计不是 `AuraSecretHack()`，而是：

```text
Platform/NilName/SecretValueAdapter
        ↓
Aura Provider
Spell Provider
CombatLog Provider
Unit Provider
```

让“secret → normal value”的处理集中在 NilName backend，不扩散到职业模块。

## 5. Object Manager / Snapshot 的架构借鉴

BadRotations 在对象枚举上有一个很值得保留的原则：

> **同一轮对象扫描只取一次 `Objects()` snapshot。**

它先取得一张对象表并缓存，然后 `GetObjectCount()` 与 `GetObjectWithIndex()` 都消费同一张 snapshot，避免在高频环境中 count 与 index 来自不同瞬间导致越界/错位。

Sirus 应采用同样的**思想**，但独立实现：

```text
Tick N
  Objects() once
      ↓
  ObjectSnapshot[N]
      ↓
  Targeting / AoE / TTD / Aura 全部消费同一 snapshot
```

这样还能保证同一 Tick 的 TTD、位置、Aura、目标选择尽量来自一致状态。

## 6. Protected API 与普通/NN API 分层

BadRotations 把 API 大致分为两类：

### A. 需要 `Unlock(...)` 的 protected action

例如施法、目标、移动、宏等受保护操作。

### B. `C_Timer.Nn` environment 暴露/覆盖的能力

例如部分 Unit/Geometry/File 能力，adapter 统一代理到框架 API。

这支持 Sirus 当前计划：

```text
Rotation Module
    ↓
Sirus Combat API
    ↓
Platform Adapter
    ↓
NilName Runtime / Unlock / WoW API
```

不要让职业 APL 直接调用 `Unlock`。

## 7. C_Spell 也是 12.1 Secret 兼容面

BadRotations 当前为 `C_Spell` 建立 proxy：

- method 第一次访问时动态包装并缓存；
- scalar 返回值经过 secret unwrap；
- table 返回值逐字段处理。

这提示我们的 12.1 Probe 不能只测 Aura。至少还要测：

- cooldown data
- charges
- spell info
- usable/range 等 rotation 依赖字段

否则 Aura 修好后，APL 仍可能被其他 secret 值卡住。

## 8. Combat Log 也需要验证

当前 NN adapter 对 `CombatLogGetCurrentEventInfo()` 的多返回值执行 secret unwrap。

因此 Sirus 的 Event Layer 应区分：

```text
RAW_EVENT (WoW/NN)
  ↓
NilName SecretValueAdapter
  ↓
NORMALIZED_EVENT
  ↓
Aura Cache / TTD / Proc State / Logging
```

即使 Aura direct path 可用，Event Cache 仍值得保留为：

- 交叉验证；
- 状态变化触发；
- 异常恢复；
- proc/伤害历史；
- TTD 数据输入。

但它不再是默认 Aura 真相源。

## 9. 对 TTD 的进一步证据

`nn.lua` 的 NN-provided/global capability 列表包含并代理：

- `UnitHealth`
- `UnitHealthMax`
- `UnitGUID`
- `UnitExists`
- `UnitIsDead`
- `UnitIsVisible`
- `UnitReaction`

这说明成熟框架确实按“NN object/unit bridge → UnitHealth/UnitHealthMax”这条路线消费生命值。它增强了 Sirus TTD Engine 的可行性判断，但当前仍要在 12.1 实机验证：

1. 对 `target` 可读；
2. 对 NN Object Manager 中非当前目标可读；
3. 数值不是 secret，或可以通过相同 unwrap 层转成普通 number；
4. 高频读取稳定、无明显性能问题。

## 10. 对 Sirus 架构的直接采纳项（思想级）

### 必须采纳

1. **Platform Adapter 与 Rotation 解耦**
2. **统一 UnitRef/ObjectRef**
3. **每 Tick 单次 Object Snapshot**
4. **Secret Value Adapter 独立成 NilName backend 子层**
5. **Aura direct provider 优先，Event/cache 作为 secondary/fallback**
6. **C_Spell / CombatLog 同时进入 secret capability probe**
7. **所有 secret-unwrapped 值在进入 Core 前做类型与范围验证**

### 不直接复制

- BadRotations 的 wrapper 代码；
- API 表组织方式；
- Aura 实现细节；
- GPL-3.0 源文件片段。

Sirus 要按自己的接口契约 clean-room 重写。

## 11. 现在应该改变的 Probe 顺序

原计划偏向：

```text
C_UnitAuras → Unlock → Object → Event reconstruction
```

基于 BadRotations 证据，第一轮应该改成：

```text
A. NilName environment discovery
   ├─ C_Timer.Nn 是否存在
   ├─ issecretvalue 是否存在
   └─ secretunwrap 是否存在

B. Secret scalar sanity
   ├─ 正常值传入行为
   ├─ secret value detection
   └─ unwrap 后 type/运算/比较

C. Aura direct path
   ├─ player
   ├─ target
   └─ NN object / 非当前目标

D. C_Spell direct path

E. CombatLog direct path

F. Health/TTD inputs

G. 只有 Direct path 不完整时，再做 Event/cache reconstruction
```

## 12. Runtime confirmation gates

只有以下条件全部满足，才能把 `secretunwrap` 路线升级成 Sirus production dependency：

- 当前用户 NilName build 中 symbol 真实存在；
- combat 中可调用；
- target/player/非当前 object 至少达到职业循环需要的覆盖率；
- Aura fields unwrap 后是稳定普通 Lua 类型；
- 不因不存在/非 secret 值导致错误；
- `points` 等嵌套字段行为明确；
- 12.1 实际 combat 下连续运行无错误；
- 性能预算通过；
- zone/reload/target swap 后不会产生 stale state。

## 13. 当前结论

**证据等级：HIGH external evidence, NOT local runtime confirmation.**

BadRotations 给出的最重要信息不是“某个旧框架也支持 NN”，而是它公开展示了一个针对 Midnight 的 NN Secret Value compatibility layer，并明确把 Aura、C_Spell、CombatLog 的 secret values 转换放在 unlocker/platform adapter 层。

因此当前 Sirus-NN 的最优研究方向应从“先设计 Aura cache 重建系统”改为：

> **先验证 NilName runtime 的 secret unwrap direct path；成功后让它成为 Aura 真相源，cache/event 只承担一致性、恢复和 fallback。**
