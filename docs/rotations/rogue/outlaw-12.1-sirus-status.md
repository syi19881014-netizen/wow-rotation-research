# Sirus 狂徒潜行者 12.1 当前状态

更新时间：2026-08-15

状态：`PROVISIONAL / ACTIVE_DEBUG`

## 当前目标

在同装备、同天赋、同战斗条件下，先达到当前 SimulationCraft APL 的统计等效基线，再叠加高端实战策略与机器执行增强。

当前装备阶段：**MID1 / 旧 4pc 过渡期**。

## 推荐配套天赋

项目当前 PRIMARY：**Trickster（欺诈者）**。

配置名：`SIRUS_OUTLAW_12_1_MID1_TRICKSTER`

导入代码：

```text
CQQAAAAAAAAAAAAAAAAAAAAAAAgx2MYmZmZmtZmZmZMmNeAmZbaZw2MAAAAAgZbbmZGmZmZGzMzyAAAAwYAwYWMMkBmFWoF2YAmZwAD
```

来源基线：SimulationCraft `midnight` 分支 `profiles/MID1/MID1_Rogue_Outlaw_Trickster.simc`。

Fatebound 保留为 ALTERNATIVE，不作为当前 Sirus 默认开发/验收 Profile。

> MID2 / S2 套装启用后必须重新核验，不自动沿用 MID1 Profile。

## 当前 APL 基线

当前 12.1 SimC 狂徒 APL核心包含：

- Adrenaline Rush 维持；
- 2+ 目标 Blade Flurry；
- Preparation 重置 AR / BTE / Killing Spree；
- Keep It Rolling；
- stage-based Roll the Bones；
- Blade Rush；
- Hidden Opportunity 下 Vanish / Ambush；
- BTE；
- Killing Spree 与 Supercharger 联动；
- Coup de Grace；
- Dispatch；
- Opportunity / Fan the Hammer / Pistol Shot builder 逻辑。

## 已通过实机验证

- Profession 注册与激活正常；
- GCD 执行链可真正自动施法；
- 大技能开关与设置页同步；
- AoE 开关与设置页同步；
- 多目标人数识别修复后可自动进入 AoE；
- 2+ 目标可自动维护 Blade Flurry；
- 当前客户端 Killing Spree 中文名/SpellID 已实机确认：`影舞步 / 51690`；
- 当前客户端 Roll the Bones 中文名/SpellID 已实机确认：`命运骨骰 / 1214909`。

## RC3.8 当前客户端映射

```text
KILLING_SPREE:
  primary id   = 51690
  primary zhCN = 影舞步
  aliases      = 杀戮盛筵 / Killing Spree

ROLL_THE_BONES:
  primary id   = 1214909
  primary zhCN = 命运骨骰
  aliases      = 315508 / Roll the Bones
```

## 当前仍需继续验证

1. 命运骨骰在 RC3.8 后是否恢复稳定施放；
2. 影舞步（Killing Spree）在当前 Trickster + Supercharger 条件下是否恢复；
3. Supercharge 隐藏 Aura 在 Workout 中是否可直接读取；
4. 若不可读，AR Aura edge / `lastcast()` fallback 是否足够稳定；
5. Preparation 是否在 KS/BTE 进入 CD 后正常触发；
6. Trickster 特有英雄天赋状态是否需要进一步显式建模；
7. 完整木桩统计结果与同条件 SimC 差距。

## 架构原则

职业文件保持单文件优先：`Rotations/Rogue/Outlaw.lua`。

通用层负责：

- Scheduler / GCDExecutor；
- ActionExecutor；
- Target / Aura / Resource / TTD sensors；
- Interrupt；
- UI settings；
- 当前客户端 SpellID/名称映射基础设施。

职业层负责：

- APL；
- Talent / Hero Spec 分支；
- Burst admission；
- AoE / ST；
- 职业特色维护；
- 调试原因输出。

不要继续把单个职业拆成大量微模块，除非确实形成跨职业复用价值。
