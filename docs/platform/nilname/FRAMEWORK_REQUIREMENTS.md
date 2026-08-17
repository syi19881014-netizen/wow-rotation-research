# NilName Rotation Framework Requirements

## 目标

NilName 给出了足够强的底层能力，但并没有证据显示它提供 Workout 式完整 Rotation Host。因此如果后续决定迁移，应把“平台 API”和“循环框架”严格分离。

## 推荐架构

```text
NilName / WoW
    |
    +-- Script Bootstrap
    +-- Unlock protected WoW APIs
    +-- Object Manager / XYZ / TraceLine
    +-- Navigation / HTTP / Crypto / FS
    |
    v
Rotation Framework (我们自建)
    |
    +-- Scheduler / Clock
    +-- API Facade
    +-- Object Cache
    +-- State Snapshot
    +-- GCD + Action Scheduler
    +-- Target Manager
    +-- APL Engine
    +-- Ground AoE Solver
    +-- Manual Override
    +-- Optional Navigation
    +-- Settings / UI / Logging
    +-- Licensing / Build
    |
    v
Class/Spec Modules
```

## 1. Bootstrap

NilName 当前入门页证明：脚本放 `/scripts/`，进入世界或 `/reload` 后执行；`local nn = ...` 可获得 NilName 对象。

框架需要自己定义：

- 唯一 bootstrap 入口
- 模块加载顺序
- duplicate-load 防护
- reload 后状态清理
- fatal error 隔离

不要假设存在 Workout 的 `Main()`。

## 2. Scheduler / Tick

官方示例自行用 `C_Timer.After(...)` 构造周期函数，因此我们必须自己管理 tick。

建议：

- Core tick：20–50 ms 可配置，但实际频率必须通过 CPU/frame-time benchmark 决定。
- Object refresh：不必每 core tick 全量扫描；分层刷新。
- UI/debug：低频。
- HTTP/license：极低频、异步。

必须实现：

- reentrancy guard
- frame hitch detection
- per-layer execution budget
- rolling performance counters

## 3. API Facade

禁止职业模块直接散落调用 NilName API。

Facade 应至少提供：

```text
GetObject(token)
ObjectExists(obj)
ObjectPosition(obj)
Enemies(range/filter)
Distance(a,b)
Facing(a,b)
Aura(...)
Cooldown(...)
Resource(...)
Cast(...)
CastGround(x,y,z)
Interact(...)
```

其中 Aura/Cooldown/Resource/Spell usability 可能主要来源于解锁后的 WoW API，而不是 NilName 独立函数；必须按当前客户端实测建立白名单，不能凭普通 WoW AddOn 经验猜。

## 4. Object Cache

Guidelines 的性能警告是整个框架最重要的设计约束之一。

不要：

```text
Objects()
 -> 每个对象 ObjectType()
 -> 每个职业模块再次重复扫描
```

优先：

- 如果 `ObjectManager(type)` 当前实机确认可用，按 type 获取。
- 一次扫描形成 frame snapshot。
- unit/player/gameobject 分开缓存。
- 缓存中保存 object id、exists、position、基础 flags。
- aura/spell 等高成本数据按需求 lazy read。

## 5. State Snapshot

每个 rotation decision 只能读取同一 snapshot，避免一个决策周期中数据时序漂移。

建议字段：

```text
now
player
  combat
  position
  facing
  health
  resources
  movement
  casting/channeling
  gcd
  buffs

target
  exists/alive/attackable
  position
  distance/reach
  casting
  debuffs
  ttd(optional)
enemies[]
  object
  id
  position
  distance
  health
  combat state
  relevant auras
```

## 6. Protected Action Layer

`Unlock(function, ...)` 是 NilName 与普通 WoW Lua 最大的结构差异之一。

Action 层必须集中处理：

- 受保护 spell call
- target/focus/mouseover bridge
- facing/movement
- ground targeting
- interact

不要让职业 APL 自己决定哪些函数要 Unlock。

## 7. GCD / Queue / Action Scheduler

不能把 Workout 的 pending/queue 经验直接照搬。

NilName 要单独实测：

- 在 GCD 剩余 400/300/200/100/50ms 时一次性提交技能，是否进入 WoW Spell Queue。
- 连续 tick 重复提交的行为。
- `Unlock(CastSpellByName/ID)` 的返回/错误行为。
- spellcast callbacks/events 是否可作为 ACK。
- off-GCD 与 on-GCD action 是否可同 tick 安全处理。

框架最终需要：

```text
Intent -> Admission -> Queue/Submit -> ACK/Fail -> Re-evaluate
```

## 8. APL Engine

职业模块只负责：

- variables
- target branch
- cooldown admission
- finisher/builder priority
- pool conditions
- movement/TTD conditions

框架负责执行语义。

这可以让 SimC APL 映射保持平台无关。

## 9. Ground AoE Solver

这是 NilName 相比当前 Workout 已知接口最大的优势之一。

基础链：

```text
Enemy Object Cache
 -> ObjectPosition(obj)
 -> generate candidate centers
 -> calculate coverage by spell radius
 -> optional TraceLine / terrain validation
 -> select best center
 -> Unlock(spell)
 -> ClickPosition(bestX,bestY,bestZ)
```

候选中心不应只用“某只怪脚下”。后续可以实现：

- enemy positions
- pairwise circle intersections
- weighted targets
- min-target threshold
- boss/high-priority weighting
- movement prediction
- LoS/terrain check

适用：Blizzard、Flamestrike、Rain of Fire、Earthquake 等地面技能。

## 10. Target Manager

NilName 的 Object Manager 允许比普通 target-token 更强的 target selection。

框架应支持：

- highest priority target
- interrupt target
- multi-dot target
- densest AoE cluster
- independent pet/player target（若职业需要）
- mouseover/focus/npc bridge

所有切目标行为需要配置“是否真正改变玩家当前 target”，尽量优先无目标切换施法路径，避免 UI/人工操作冲突。

## 11. Movement / Navigation

Rotation 与 Bot/Nav 必须分层。

Rotation 默认只允许：

- facing suggestion/optional correction
- short-range skill-required movement（如明确开启）
- ground spell geometry

完整 `GeneratePath` / `ClickToMove` 进入可选 Navigation 模块，不应默认影响纯 DPS rotation。

## 12. Manual Override

必须从第一版就支持玩家人工插入：

- 识别当前玩家手动 cast/channel
- 不抢占用户关键技能
- 可配置下一 GCD 插入优先级
- cooldown toggle / AoE toggle / interrupt toggle

NilName 的低层能力越强，越要明确人工优先级，避免自动动作与玩家输入互相争抢。

## 13. Logging / Replay

建议统一事件格式：

```text
TICK
SNAPSHOT
DECISION
INTENT
SUBMIT
SPELLCAST_ACK
ERROR
TARGET_CHANGE
GROUND_POINT
PERF
```

后续可以把实机日志与 SimC/WCL action timeline 做自动差异分析。

## 14. Licensing / Distribution

NilName 当前公开能力允许不依赖额外本地 loader 构建基本授权体系：

```text
GetWowAccount()
  -> HTTPS request
  -> server UTC + license record
  -> signed token
  -> HMAC verify
  -> encrypted/local cached grace token
```

推荐：

- 服务端为时间真源，本地系统时间不作为授权最终依据。
- 账号标识以 `GetWowAccount()` 实机稳定性为前提。
- token 必须签名，不信任客户端返回字段。
- 允许短离线宽限期。
- Lua 混淆只是增加逆向成本，不作为安全根。
- 如果使用 AES 脚本加载，密钥管理仍应避免静态硬编码成为唯一保护。

## 15. 首轮开发 Probe 清单

在写任何职业循环前，只做一次平台能力验收：

1. script bootstrap/reload lifecycle
2. scheduler jitter / max sustainable tick rate
3. `ObjectManager(type)` 是否当前真正可用、返回格式
4. `Object`/`Objects`/`ObjectExists` 生命周期
5. position/facing/trace accuracy
6. protected spell casting + GCD queue behavior
7. aura/cooldown/resource 所需 WoW APIs 的 Unlock/availability
8. ground spell `ClickPosition` 顺序和 cursor state
9. focus/mouseover bridge
10. `GetWowAccount` 稳定性
11. HTTP callback/threading/reload behavior
12. FileSystem path sandbox
13. crypto functions current names/casing

Probe 通过后冻结 `NILNAME_API_WHITELIST`，职业模块才允许开始接入。
