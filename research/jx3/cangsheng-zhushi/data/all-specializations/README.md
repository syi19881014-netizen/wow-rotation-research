# 剑网3 · 苍生铸世：全门派/心法资料（2026-10-30）

> **目标：用于天策PVP对抗各心法的机制认知与状态判断；不是可直接上线的自动战斗脚本。**

采集方式：`scripts/import_all_specializations.py` + GitHub Actions `.github/workflows/jx3-all-specializations.yml`。

## 数据源与时效
- JX3BOX 2026-10-30 旗舰端全心法奇穴快照：`https://github.com/JX3BOX/jx3box-talent/blob/master/output/std/v20261030.json`
- JX3BOX 2026-10-13 `skill.txt`、`skills.tab`：`https://github.com/JX3BOX/jx3box-talent/tree/master/raw`
- JX3BOX 2026-10-13 `buff.txt`、`buff.tab`：同上
- 全部通过Git提交SHA锁定内容以实现可重复抽取。
- 此前2023/2024旧版静态映射**没有**混入本次采集。
- 2026-10-29后正式服完整技能和Buff实测尚未取得。**技能ID是10/13候选，不是假定已验证的新版本。**

## 每个心法有四份文件
- `<心法>/talents_20261030.csv`：36个唯一奇穴，保留描述、来源ID、原始`is_skill`标签；第7～9重共用一个12选项池。
- `<心法>/skills_candidates_20261013.csv`：根据当季奇穴提及、奇穴技能ID、门派前缀从10月13日技能表筛选出的候选技能（含派生及替换候选）；任何GCD/独立CD/是否能施放保持未知。
- `<心法>/buff_links_20261013.csv`：从被索引技能文本中精确解析`<BUFF ID Level ...>`的Buff引用及原始效果/持续字段；引用关系不代表实战必然施加。
- `<心法>/pvp_signals_20261030.csv`：按控制、免控、防御、减疗、位移、爆发等关键词标记的奇穴；**标签不是实战验证**。

## 汇总资料
- `INDEX_20261030.csv`：各心法覆盖数量和缺口。
- `TALENTS_ALL_20261030.csv`：全部32心法唯一奇穴整合。
- `PVP_SIGNALS_ALL_20261030.csv`：跨心法的PVP关键词索引。
- `IMPORT_REPORT_20261030.json`：数据来源、文件大小、快照日期与缺口。
- `research/all-specializations-audit.md`：人工审计与后续验证顺序。

**重要：** `is_skill=1` 只是JX3BOX的原始标签，不能理解成当前已确认可以按键施法；`is_skill=0`也可能对应技能替换、二段技能或被动解锁主动技能。BuffID与SkillID和奇穴ID必须严格区分。

## 下一步重点
- 抓取游戏中2026-10-29之后的技能面板、奇穴主动/替换、BUFF等级和实际控制时长；不能由10月13日表推断GCD。
- 对每个对战心法构建“核心爆发/控制/免控/减疗/治疗、长短增益、PVP应对”而不是只列技能名。
