# JX3BOX 傲血战意“原始数据”页面：接口与技能ID采集方案

日期：2026-10-30
目标页面：https://www.jx3box.com/bps/raw?subtype=%E5%82%B2%E8%A1%80%E6%88%98%E6%84%8F

## 本轮已核实的内容

从开源前端 `JX3BOX/bps` 的 `src/views/Raw.vue` 找到了**该路径的渲染逻辑**，包括“心法被动”、“武学套路技能”、“奇穴”、技能描述、SkillID、IconID、Level等字段。源代码仓库于2025-02-25归档，**不能据此确认2026年页面仍使用完全相同接口或数据已更新**。

页面不同于旧 `jx3box-data` 静态技能ID文件，其源码通过服务器接口获取当前心法技能面板，通过CDN数据获取奇穴关系：

1. `getKungfuPanel({ mount_id, client })`
   - 源码位置：https://github.com/JX3BOX/bps/blob/master/src/service/node.js
   - 旧前端请求地址：`GET https://node.jx3box.com/api/node/v2/kungfu/panel?mount_id=10026&client=std`
   - 说明：`mount_id=10026` 是上游旧心法映射提供的参数值，**须在2026年实际接口复核**；`client=std` 表示旗舰端。
   - 旧前端解析 `res.data.data`，其中包含 `kungfu_id`、`kungfu_name`、`skill` 等信息；分类为心法被动、阵法、武学套路。
2. `getTalents(client)`
   - 源码位置：https://github.com/JX3BOX/bps/blob/master/src/service/raw.js
   - 旧前端数据地址：`GET https://cdn.jx3box.com/data/qixue/std/talents.json`
   - 说明：根据心法ID查奇穴技能ID数组，**必须核验当前是否仍为九重**。
3. `getSkills({ ids, client })`
   - 源码位置同上
   - 旧前端请求地址：`GET https://node.jx3box.com/skills?ids=<逗号连接的ID>&client=std`
   - 说明：依照奇穴ID查每个奇穴技能详情；可能有同一SkillID多Level结果。
4. `Raw.vue` 页面：
   - https://github.com/JX3BOX/bps/blob/master/src/views/Raw.vue
   - 字段在源码中明确出现：`SkillID`、`Name`、`IconID`、`Desc`、`parse.desc`、`parse.talent_desc`、`Level`、`Remark`、`HelpDesc`、`SimpleDesc`、`SpecialDesc`。
   - 说明：源码并未证明直接返回**GCD、准确调息、当前BuffID**。

## 本轮可访问性
- 已核实该页面存在相应开源路由、渲染和数据读取实现。
- 直接网页访问与三个数据源请求在目前工具环境中未成功，**没有获取当季技能/奇穴JSON**。
- 因此绝不把请求路径存在理解成“当前线上接口一定可用”，也不得凭旧字段补齐技能ID。

## 正式服取数验收条件
1. 成功请求当前网页的`Network`返回值，记录抓取时间/响应状态/版本字段。
2. 对技能面板逐项记录 `Name`、`SkillID`、`Level`、`Desc`，特别核对 **撼如雷**。
3. 对九重奇穴逐项抓取`talents.json`下的ID序列与`/skills`的详情响应，证明数据是当季九重而不是旧12重。
4. 验证主动/被动、派生技能、技能置换以及GCD的可得字段；无法从页面确认的保持“待实测”。
5. 同10月29日官方天策武学更新说明和正式服客户端交叉验证后，才允许标记为“当前正式服核准”。

**性质：已定位高价值取数入口，但尚未取得并验证实时响应。**
