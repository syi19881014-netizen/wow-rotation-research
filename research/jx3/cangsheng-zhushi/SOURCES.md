# 数据来源与时效审计（2026-10-30）

## 官方：当前赛季的首要依据
- 2026-10-29天策武学调整专页：https://jx3.xoyo.com/show-2466-7574-1.html （官方目录可确认存在，网页正文当前未成功读取）
- 官方新闻目录：https://jx3.xoyo.com/list-2466-0.html （列出10/29天策专题）
- 正式服公告目录：https://jx3.xoyo.com/announce/
- 测试服10月中旬更新：https://jx3.xoyo.com/launcher/update/latest_exp.html （两条天策修复，限测试服）

## JX3BOX：服务与GitHub仓库必须区分
- 在线数据库：https://www.jx3box.com/app/database/ （页面可能需要浏览器渲染，未拿到2026-10-29以后的天策全量数据）
- 已检索到的一个JX3BOX线上技能页面显示**基础库2026-10-05**：https://origin.jx3box.com/app/database/?query=132&type=skill 。这比10月29日正式上线早24天；**不能据此确认苍生铸世正式服有效性**。该日期只表示所见页面显示版本，不推定整个网站当前最新同步时间。
- GitHub原始静态库：https://github.com/JX3BOX/jx3box-data
- 名称映射上游文件最后提交：2023-11-12，GitHub commit `8a16f1f535077509b28f7f5b5f037391813b2562`：
  https://github.com/JX3BOX/jx3box-data/commits/master/data/xf/std/skill_name_id_level.json
- 原始技能表最后提交：2024-09-03，GitHub commit `8076e078bd75e2cc036522585975a93bebbcfb4a`：
  https://github.com/JX3BOX/jx3box-data/commits/master/raw/std/skill.txt
- 旧奇穴表最后提交：2024-09-03：
  https://github.com/JX3BOX/jx3box-data/commits/master/raw/std/tenextrapoint.tab

**结论：不能用这些仓库旧静态文件证明2026年10月29日的技能ID、技能效果、GCD或奇穴。不要从这些静态文件重新生成正式服资料。**

## 辅助来源限制
- 其他Wiki、攻略、视频可作为定位线索，必须注明上传日期和对应赛季。
- 不能把2026年10月17日更新但自身明示“端游已删除”的历史武学说明当作10月29日实际技能表。

## 证据等级
- A：10月29日及以后正式服客户端实际技能/奇穴/战斗数据（含客户端版本）+可重复检验
- B：10月29日后官方明确武学描述/修订+可定位到正式服版本
- T：2026年测试服官方内容（只作版本变更线索）
- U：未取得当季权威证据，必须留空，不输入正式技能库

## 2026-10-30新增：JX3BOX傲血原始技能/奇穴展示页
- 入口：https://www.jx3box.com/bps/raw?subtype=%E5%82%B2%E8%A1%80%E6%88%98%E6%84%8F
- 已找到归档前端相关实现：https://github.com/JX3BOX/bps/blob/master/src/views/Raw.vue
- 该前端通过 `getKungfuPanel` 获取面板技能，`getTalents` 获取奇穴ID结构，`getSkills` 获取奇穴技能详情。
- **不是2023年静态GitHub映射表**；但该归档前端代码不能证明2026年实际线上数据最新。实时请求尚未成功，数据版本未校验。
- 完整请求地址/数据字段/采集与验收流程：`research/jx3box-raw-interface.md`。

## 2026-10-30真实同日奇穴快照（新来源，优先）
- https://github.com/JX3BOX/jx3box-talent/blob/master/output/std/v20261030.json （2026-10-30最新旗舰端文件，天策两系第1～9重）
- https://github.com/JX3BOX/jx3box-talent/blob/master/output/std/v20261029.json （前日正式服首日快照，可比较）
- https://github.com/JX3BOX/jx3-skill-parser （技能Lua解析器，源码有对技能属性/Buff/冷却/子技能引用的处理能力，但需要当季脚本数据才能使用）
- 审计详情：`research/2026-10-30-talent-audit.md`
