# 资料来源与版本核验

采集日期：2026-10-30（按中国时间）；目标：**旗舰端 / 苍生铸世 / 天策 / 傲血战意与铁牢律**。切勿与缘起服、“悟”招式、测试服或往期赛季混用。

## 数据映射（已实际读取）
- 心法名与心法ID：https://github.com/JX3BOX/jx3box-data/blob/master/data/xf/xf.json
- 技能套路分组：https://github.com/JX3BOX/jx3box-data/blob/master/data/martial/kungfu_std.json
- 名称→技能ID/等级：https://github.com/JX3BOX/jx3box-data/blob/master/data/xf/std/skill_name_id_level.json
- 旧版奇穴表（**历史数据，非当前正式服！**）：https://github.com/JX3BOX/jx3box-data/blob/master/raw/std/tenextrapoint.tab
- 技能表完整源及原始结构：https://github.com/JX3BOX/jx3box-data/blob/master/raw/std/skill.txt
- 编译脚本：https://github.com/JX3BOX/jx3box-data/blob/master/build/skill_name_to_id_level.js

### 数据时间陷阱
上游的 `tenextrapoint.tab` 仍有 **12层、需求等级108～120**，不符合苍生铸世9重奇穴及50级世界。它的历史技能ID不能直接作为当前可点奇穴。上游 `skill_name_id_level.json` 只证明“数据集中该名字映射到对应ID”，并不能证明技能/等级/GCD/效果在2026-10-29版本仍有效。尤其“映射等级=0”是映射表值，不等于技能未学习，也不等于GCD=0。

## 当季公告与参考
- 官网公告列表：https://jx3.xoyo.com/announce/
- 官网9月8日天策首轮武学调整目录：https://jx3.xoyo.com/list-2466-0.html
- 9月8日技能流派调整方向（转载）：https://news.17173.com/content/09082026/171757985.shtml
- 10月16日及后续测试服技改记录：https://jx3.xoyo.com/launcher/update/latest_exp.html
- 10月29日天策正式服技改页面（检索到页面地址，正文未核验，禁止据此断言数值）：https://jx3.xoyo.com/show-2466-7574-1.html
- 2026年5月武学助手宏展示（**旧版本参考**）：https://www.sina.cn/news/detail/5303560575387840.html
- 技能/Buff字段元数据：https://github.com/JX3BOX/jx3box-data/blob/master/data/app/skill.json 和 https://github.com/JX3BOX/jx3box-data/blob/master/data/app/buff.json

## 证据等级
- A：2026-10-29之后正式服客户端实际数据+可重复测试记录；可用于正式服结论
- B：2026-10-29之后官方明确技能文本；等待实机验证
- C：第三方数据库当前抓取、未核验版本；可用作候选ID，不得视为实机效果
- H：旧版/测试服数据；**隔离在历史或候选文件**
- U：未知；保持空字段，不猜测

每项结论应标注来源链接、数据发布日期/读取日期、客户端版本、是否旗舰端、心法和实测方法。
