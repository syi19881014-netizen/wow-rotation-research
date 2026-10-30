# 剑网3·苍生铸世 天策 PVP 机制与技能资料库

建立日期：2026-10-30 | 旗舰端 | **资料采集/机制建模项目，并非已验证的实战自动施法系统**。

## 当前已入库的内容

- `data/tiance/skills.csv`：傲血战意与铁牢律各自18条面板套路技能关联，共36条记录（包含1条上游暂缺名称的ID 427）。记录名称、技能ID、上游等级、心法ID、套路分组；**当前效果和GCD目前均待实测**。
- `data/tiance/specializations.json`：两套心法的ID和套路ID，区分“心法ID”和“套路ID/奇穴KungFuID”。
- `data/tiance/talents_candidates.csv`：优先核实的候选奇穴、流派名称及历史映射ID；不是正式服奇穴选择清单。
- `data/tiance/talents_legacy_12tier.csv`：旧版12重历史奇穴选项，**不得当作苍生铸世九重奇穴**。
- `data/tiance/buffs_to_verify.csv`：PVP关键Buff、免控、减疗、击倒、破军/战意等状态清单。
- `research/gcd_verification.md`：GCD、独立CD、施法锁、失败与延迟的实验设计。
- `research/pvp_state_machine.md`：抓点、防守、追击等状态机草案。
- `research/verification_queue.md`：当前缺项与下一批工作。
- `SOURCES.md`：来源和证据等级。

## 已定位心法标识
- **傲血战意**：心法ID `10026`，奇穴表旧KungFuID `6`，门派ForceID `3`
- **铁牢律**：心法ID `10062`，奇穴表旧KungFuID `8`，门派ForceID `3`

## 使用限制
数据字段为 `待核验` 时，不能把它用于自动施法或假定离GCD；同名技能可能存在不同等级、派生触发和被动效果。名剑大会等PVP场景请遵守游戏规则；本库优先用于离线状态机、技能提示、录像分析和合法插件能力评估。

**范围说明：** 本阶段专注天策的两套心法和傲血流派（破重围、戎行、流血）。后续可按同一模式扩展全门派心法。

## 第二批扩充（跨门派技能ID候选总表）

- `data/all-specializations/skills_candidates.csv`：按每个已收录心法列出上游套路技能，含技能名、SkillID及GCD/效果留空待核验。
- `data/all-specializations/heart_coverage.csv`：枚举心法ID、覆盖情况、缺失情况。
- `data/tiance/talents_current_9tier_template.csv`：正式服9层奇穴采集模板（当前留空、不得臆填）。
- `updates/2026-10-15-tiance-test.md`：天策测试服两条技能/奇穴修复记录。
- `research/data_schema.md`：解释心法、技能、奇穴、Buff、图标的ID空间和未来数据读取字段。

**范围警告：** 全门派总表仅覆盖JX3BOX当前静态映射所含心法，不代表2026-10-29正式服所有门派已完整覆盖；特别是新职业/新流派需要额外补录。
