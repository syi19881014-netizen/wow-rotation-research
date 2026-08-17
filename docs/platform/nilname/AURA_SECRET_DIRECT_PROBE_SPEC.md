# NilName 12.1 Aura Secret Direct-Path Probe Spec

> 状态：SPEC ONLY — 不代表 runtime confirmed  
> 日期：2026-08-17

## 目标

验证 BadRotations 公共 NN adapter 暴露出的关键线索是否在用户当前 NilName + WoW 12.1 环境中成立：

- `C_Timer.Nn`
- `issecretvalue`
- `secretunwrap`
- `C_UnitAuras` index-based AuraData direct path
- `C_Spell` secret-sensitive return values
- `CombatLogGetCurrentEventInfo()` secret-sensitive return values

第一版 Probe **不自动施法、不做职业循环、不加载 Sirus、不依赖 PrimeKit**。

## 环境要求

1. `_PrimeKitCore.nn` 暂时移出 `/scripts/` 或禁用自动加载。
2. 只加载 Probe 本身。
3. 记录 NilName build / WoW build / locale / spec。
4. 测试分为脱战与战斗两个阶段。

## Gate A — Runtime namespace discovery

只检查存在性与 `type()`，禁止猜调用：

- `C_Timer`
- `C_Timer.Nn`
- `C_Timer.Nn.issecretvalue`
- `C_Timer.Nn.secretunwrap`
- 当前 script vararg `nn = ...`

输出：

```text
[AURA_PROBE] namespace C_Timer.Nn type=...
[AURA_PROBE] symbol issecretvalue type=...
[AURA_PROBE] symbol secretunwrap type=...
```

若 `secretunwrap` 不存在，停止 Direct-Path 分支，转入普通 Secret 行为测量；不要发明替代 API。

## Gate B — Safe normal-value behavior

目的：确认 helper 对普通 Lua 值的行为，不先碰 Aura。

测试输入：

- nil
- false/true
- integer
- float
- string

只在明确不会导致 fatal error 的前提下逐项 protected-call。

记录：

- `issecretvalue(normal)` 返回 shape
- `secretunwrap(normal)` 是 no-op、报错还是其他行为

所有调用必须 `pcall/xpcall` 隔离。

## Gate C — Player Aura direct path

选择人为可触发、容易观察的 player buff。Probe 不负责施放，用户手动触发。

对同一个 AuraData 记录：

- table 是否返回
- 每个关键 field 的 `type`
- `issecretvalue(field)`
- 若为 secret，`secretunwrap(field)` 后的 `type` 与值
- unwrap 后能否：
  - `==`
  - `< / >`
  - `- GetTime()`
  - 存入普通 table

关键 fields：

- `spellId`
- `applications`
- `duration`
- `expirationTime`
- `sourceUnit`
- `isHelpful`
- `isHarmful`
- `points`

禁止把 secret value 直接拼接进字符串或做算术；必须先通过安全检测。

## Gate D — Target / harmful Aura

用户手动给训练假人施加一个可识别 debuff。

重复 Gate C，同时验证：

- `target`
- target change 后是否 stale
- debuff refresh
- debuff remove

## Gate E — NilName Object / 非当前目标

如果 Object Manager / Object bridge 已在独立 Probe 中确认安全，再测试：

1. 获取附近至少两个 attackable objects；
2. 不切目标；
3. 对 object reference 调用已确认的 Unit/Aura bridge；
4. 验证非当前目标 Aura 是否可直读和 unwrap。

成功标准不是“能看到名字”，而是能得到普通 Lua 类型的：

```text
spellId / stacks / expirationTime
```

这一步决定刺杀等多目标 DoT 是否能做真正 per-object tracking。

## Gate F — C_Spell

只读测试若干 rotation 会依赖的 API，至少覆盖：

- spell info
- cooldown data
- charges
- usable/range（若 API 在当前 build 存在）

记录 table/scalar field 是否 secret，以及同一 unwrap 层是否有效。

## Gate G — CombatLog

注册 `COMBAT_LOG_EVENT_UNFILTERED`，取得 `CombatLogGetCurrentEventInfo()`：

- 记录每个返回位置的 `type`
- 标记 secret scalar
- 尝试 unwrap
- 对 spellID/sourceGUID/destGUID 等 rotation/event-cache 关键字段验证普通 Lua 可消费性

## Gate H — Health / TTD inputs

只读：

- `UnitHealth(target)`
- `UnitHealthMax(target)`
- 已确认 object/unit bridge 后，对非当前 enemy object 重复

验证：

- 返回普通 number 还是 secret
- unwrap 是否需要/是否可用
- 高频采样是否稳定

这一步只是确认 TTD 数据源，不在本 Probe 内实现 TTD 算法。

## Logging schema

每条结果统一：

```text
[NN12_AURA]
phase=<A-H>
source=<WOW|NN_ENV|AURA|SPELL|CLEU|HEALTH>
api=<name>
unit=<token/object-kind>
field=<field-or-return-index>
raw_type=<type>
is_secret=<true|false|unknown>
unwrap_ok=<true|false|na>
unwrapped_type=<type|na>
operation_test=<pass|fail|na>
error=<sanitized-error|none>
```

不要输出账户名、session token、HTTP credential 等敏感值。

## Result classification

### RUNTIME_CONFIRMED_DIRECT

当前 build 中：

- helper 存在；
- combat 中工作；
- 关键 AuraData 字段成功变为普通 Lua 类型；
- 连续刷新/移除/换目标稳定。

### PARTIAL_DIRECT

部分字段/单位类型可用，但存在 coverage gap。

### DIRECT_FAILED

helper 不存在，或不能把 rotation 关键字段转换为普通可计算值。

### UNKNOWN

测试环境/目标不满足，不能下结论。

## 对 Sirus 的决策规则

如果 `RUNTIME_CONFIRMED_DIRECT`：

```text
Sirus.Aura
  ↓
NilName Direct Aura Provider   [primary]
  ↓
Event Cache                    [validation/recovery]
  ↓
Mechanic Reconstruction        [exception only]
```

如果 `PARTIAL_DIRECT`：按字段/单位类型建立 provider capability matrix，不做“一刀切”。

如果 `DIRECT_FAILED`：才正式投资 Event/cache reconstruction。

## Codex implementation constraints

- 不依赖 BadRotations 源码；按本规格独立实现 Probe。
- 不复制 GPL-3.0 wrapper。
- 不加载 PrimeKit。
- 不自动施法。
- 不写 Sirus Core。
- 不使用 `ObjectField` raw offsets。
- 所有未知 symbol 先 `type`/protected-call 探测，禁止假设签名。
