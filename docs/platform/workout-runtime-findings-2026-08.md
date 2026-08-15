# Workout Runtime 实机结论（2026-08）

更新时间：2026-08-15

本文只记录“魔兽循环”项目中已经通过当前 Workout 客户端实机观察确认、并会直接影响自动循环架构的行为。

## 1. Spell Queue 行为

### 结论

当前 Workout `cast()` **不能依赖一次提前调用自动进入 WoW Spell Queue**。

2026-08-14 狂徒训练假人 Probe：在旧 GCD 剩余约 `0.369s / 0.247s / 0.142s / 0.058s` 时分别只提前调用一次 `cast("影袭")`，旧 GCD 归零后均未自动触发下一次 GCD。

状态：`CONFIRMED_RUNTIME`

### 可行执行方式

从预执行窗口开始，每个 `Main()` tick 重复尝试 `cast()`，可以稳定在旧 GCD 结束后的首个或次个 tick 成功。

当前框架因此采用：

`Decision -> pre_execute_window -> GCDExecutor 每 tick retry -> cast success`

而不是：

`提前一次 cast -> 等待平台/客户端自动排队`

## 2. Workout Lua 兼容性

### `next` 不可用

实机已多次出现：

`attempt to call a nil value`，定位到 `next(...)`。

当前结论：Workout Lua 环境中不要使用 `next()`。

已验证可替代：`pairs()`。

状态：`CONFIRMED_RUNTIME`

当前项目同时避免依赖：

- `setmetatable`
- `require`
- `module`
- `pcall`
- `xpcall`

其中 `next()` 是已通过错误日志明确确认的问题；其他项继续按平台兼容约束处理。

## 3. 多目标扫描

实机多人训练假人测试曾出现：

- 当前目标存在；
- 距离正常；
- 正在战斗；
- 但框架 `target_count = 0`。

修复后 TargetEngine 使用双扫描容错：

1. `距离<8 + 可攻击 + 可视`
2. `距离<8 + 可攻击`

取更可信的数量，并以当前有效攻击目标作为最低 `1` 的 fallback。

修复后狂徒可以正确进入 AoE，并自动维护剑刃乱舞。

状态：`CONFIRMED_RUNTIME_RESULT`

## 4. 高频传感器性能

历史 RC3 在每个 Main tick 高频重复执行大量 aura alias、spellKnown、talent、hero talent、target scan、TTD、UI Render 查询时，实机 FPS 曾从约 `109` 降到约 `11`。

当前框架原则：

- 动态战斗 Proc Aura：高频；
- 天赋/英雄天赋/技能解析：静态缓存，脱战周期刷新；
- 目标扫描：限频；
- TTD：限频采样；
- UI Render：限频；
- GCDExecutor 负责 queue-window 内 retry，不让 Scheduler 累积每 tick 的重复动作。

状态：`CONFIRMED_PERFORMANCE_DIRECTION`

## 5. 开发验收原则

任何新职业进入 Workout 前，至少需要通过以下平台级 Probe：

- 当前版本关键 SpellID / zhCN 名称；
- `spellKnown` 解析；
- cooldown 返回；
- aura / stacks 返回；
- `cast()` 实际施法；
- 多目标扫描；
- GCD queue-window 行为；
- 长时间运行 FPS。

不要仅以“APL 逻辑正确”作为可运行结论。
