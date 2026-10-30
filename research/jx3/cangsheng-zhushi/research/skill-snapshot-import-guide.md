# 2026年天策技能原始表采集和校验

- 本项目已入库 **2026-10-30旗舰端九重奇穴**，当季奇穴全量72项见 `data/tiance/talents_20261030.csv`。
- 技能来源：`https://github.com/JX3BOX/jx3box-talent/tree/master/raw` 的 `skill.txt` 与 `skills.tab`，其最新Git提交是 **2026-10-13**（不是10月29日）！
- `scripts/import_skill_snapshot.py` 使用 Python 标准库下载GB18030/GBK原始技能表，采集天策核心技能及10月30日奇穴描述提及的技能，保留全部候选技能ID、等级和效果、原始调息相关列。
- 自动化工作流 `.github/workflows/jx3-tiance-collect.yml` 在工作流创建时触发或支持手动触发，若仓库Actions权限允许则将提取结果提交回本仓库。
- 导出 `skills_candidates_20261013.csv` 是**2026-10-13候选表，不是最终正式服技能表**；若同名技能有多个ID则全部保留。
- `skills_name_audit_20261013.csv` 专门显示未匹配/重复匹配的技能；它仍不保证涵盖未在现行奇穴说明提及的技能。
- `skill_import_report.json` 记录GBK解码、数据大小、候选数、撼如雷ID候选、调息字段。

## 验收标准
1. 先看工作流是否运行成功，确认数据导出真实存在，再开始审计技能ID。
2. 实际新版 `SkillID` 需要10月29日后的客户端或实时技能接口二次确认；10月13日数据只能提供强候选。
3. 任何GCD必须从当前客户端公开字段和实机测试交叉验证；不能将调息字段直接等于公共GCD。
4. 必须核对固定爆发技能**撼如雷**、疾如风、任驰骋、骑御、下马形态，及奇穴主动、衍生技能。

## 2026-10-30实跑结果
GitHub Actions 工作流已成功运行，报告文件已真正提交到主分支：
- `skills_candidates_20261013.csv`：341条原始候选（包括NPC/子技能）。
- `skills_name_audit_20261013.csv`：47个目标名称，46个匹配。
- `skill_import_report.json`：撼如雷同名候选404/444/445/37105。
- `skills_priority_audit_20261013.csv`：筛选高相关候选，另显示置信分类，仍有待剔除的同名技能变体。
