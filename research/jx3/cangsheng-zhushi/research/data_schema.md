# 战斗资料字典与接口研究字段

## 先区分ID空间
- `heart_id`（心法ID）；**当前正式服数值待重新核验**。
- `routine_id`（套路ID）；**并非技能ID**，当前正式服数值待核验。
- `skill_id`（具体招式/奇穴技能ID）；必须来自2026-10-29及之后对应客户端版本。
- `skill_level` 技能等级；名称映射中的0只是来源字段，不意味着“0级/离GCD”。
- `buff_id` Buff/减益ID；不要把SkillID直接冒充BuffID。
- `icon_id` 图标ID；不能拿来判断施法。
- `talent_option_id` 奇穴点选标识；未确认是否与对应SkillID一致，需复核。

## 技能结构字段（来自JX3BOX skill元数据结构）
- 技能类型：`IsPassiveSkill`、`IsChannelSkill`、`EffectType`、`FunctionType`。
- 目标：`CastMode`、`TargetRelationSelf/Enemy/Ally`、`CheckReachable`、`Use3DObstacle`。
- 特殊释放约束：`SelfHorseStateRequest`、`IsAutoTurn`、`NeedOutOfFight`、`IgnoreSilence`。
- 这些是**字段定义**，并不是某个技能的2026-10-29实际字段值。

## Buff结构字段
- `BuffID`、`Level`、`BuffName`、`BuffType`、`MaxStackNum`、`DetachType`、`CanCancel`、`Interval`、`IsStackable`。
- 要单独研究控制状态与免控状态的覆盖关系、驱散、剩余时间和叠层。

## PVP决策输入优先顺序
自己的技能CD/战意/Buff > 目标免控/控制/血量 > 目标距离与视线 > 友方集火/保护 > 对手关键技能事件历史。敌人未公开的CD不得假设能直接读取。

## 数据未覆盖
- GCD触发、实际公共调息、独立CD、当前技能伤害公式和控制持续时间。
- 2026-10-29的九重奇穴列表及其混选池。
- 新门派/新模式可能不在当前静态映射。必须与正式服核对后补录。

数据源：
- https://github.com/JX3BOX/jx3box-data/blob/master/data/app/skill.json
- https://github.com/JX3BOX/jx3box-data/blob/master/data/app/buff.json
