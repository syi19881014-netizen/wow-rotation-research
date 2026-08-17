# NilName / NoName API 研究档案

> 抓取日期：2026-08-17  
> 目标：为“魔兽循环”项目建立可审计的 NilName API 能力清单，判断其是否适合作为自研 Rotation Framework 的底层。

## 结论摘要

NilName 当前更接近 **Unlocker + Lua 执行环境 + Object Manager + Navigation + HTTP/Crypto/FileSystem 基础设施**，而不是 Workout 那种已经提供 `Main()`、`cast()`、`energy()`、`combo()` 等高层循环接口的完整 Rotation Host。

官方开发入门页显示：

- Lua 文件放在 `/scripts/` 下，进入游戏世界或 `/reload` 后执行。
- 脚本可通过 `local nn = ...` 获取 NilName 对象。
- 受保护的 WoW API 可以经 `Unlock(function, ...)` 调用；官方示例使用 `Unlock(CastSpellByName, "Fishing")`。
- 官方示例自己使用 `C_Timer.After(...)` 构造 ticker，说明调度器/循环驱动需要开发者自行实现。
- `Objects()` / `Object(...)` / Object Descriptor API 提供 Object Manager 能力。
- `ObjectPosition()`、`ClickPosition()`、`TraceLine()`、`GeneratePath()` 等提供完整空间/导航基础。
- `HTTP:Request()`、AES、SHA/HMAC、FileSystem、Storage、`GetWowAccount()` 足以构建远程授权、联网时间锁和本地 token 缓存。

因此，如果后续迁移到 NilName，建议不要直接移植 Workout 的平台层，而是建立一个薄而明确的自研框架：

`Bootstrap -> Scheduler -> API Facade -> Object Cache -> State Snapshot -> Action Scheduler -> APL Engine -> Ground AoE Solver -> Optional Navigation -> Licensing/Build`

## 本目录

- `API_CATALOG.md`：当前公开 API 的人工审计目录、签名、状态、用途和风险。
- `api_catalog.json`：机器可读 API 清单，后续供 Codex/生成器/白名单使用。
- `FRAMEWORK_REQUIREMENTS.md`：如果基于 NilName 自建循环框架，需要补齐哪些上层能力。
- `LEGACY_CURRENT_DIFF.md`：当前官方文档与旧 IPFS 文档镜像之间的版本漂移和疑似废弃 API。
- `FETCH_GAPS.md`：当前因为 403/TODO/正文缺失而未能完整确认的页面；严禁根据函数名猜签名。
- `SOURCES.md`：官方页面、旧镜像与证据等级说明。

## 状态标签

| 标签 | 含义 |
|---|---|
| `CURRENT_BODY_CAPTURED` | 当前官方页面正文已成功读取，签名/返回值有直接证据 |
| `CURRENT_INDEX_ONLY` | 当前官方侧栏/索引确认存在，但具体页面正文无法读取 |
| `CURRENT_TODO` | 当前官方页面存在，但官方正文仍为 TODO |
| `LEGACY_MIRROR_CAPTURED` | 旧官方文档镜像有正文，当前页面未确认 |
| `DOC_INCONSISTENCY` | 当前官方页面存在明显拼写、类型或示例不一致 |
| `UNVERIFIED_LEGACY` | 仅旧镜像出现，必须实机 Probe 后才能加入正式 API 白名单 |

## 使用规则

1. **正式 Rotation Framework 只允许默认依赖 `CURRENT_BODY_CAPTURED` API。**
2. `CURRENT_INDEX_ONLY` 可以列入研究清单，但代码不得自行猜测参数。
3. `ObjectField()` 属于直接 descriptor/memory offset 读取，应视为高级危险接口；普通循环禁止依赖硬编码 offset。
4. 旧镜像 API 不等于当前可用 API。任何 `LEGACY_MIRROR_CAPTURED` / `UNVERIFIED_LEGACY` 项必须做版本实机验证。
5. 对官方文档自身的明显错误保留原始证据，并在本库中标注，不擅自“修正成我们认为正确的签名”。
6. 本目录是**结构化摘要和能力审计**，不镜像/复制官方文档全文。

## 当前最重要的能力判断

### 对战斗循环

NilName 提供足够底层能力，但需要我们自己构建：

- scheduler/ticker
- spell/cooldown/resource/aura state adapters
- GCD / queue / retry
- target manager
- APL/state machine
- manual override
- logging/debug
- settings/UI（如需要）

### 对地面 AoE

NilName 已公开 `ObjectPosition(object) -> x,y,z` 和 `ClickPosition(x,y,z)`，并明确说明 `ClickPosition` 常用于 AoE spellcasting。因此可以实现真正的怪群几何求解，例如：扫描敌人坐标 -> 求覆盖最多目标的 Blizzard 圆心 -> 施放地面技能 -> 点击最优 XYZ。

### 对授权/发行

当前公开能力至少包括：

- `GetWowAccount()`：账号级稳定身份候选
- `HTTP:Request()`：远程授权服务器
- SHA/HMAC + AES：签名/加密
- FileSystem / Storage：本地 token/cache

这比把授权逻辑完全塞进普通 Lua 字符串里更适合做“账号绑定 + 服务端 UTC 时间锁 + 签名 token + 加密发行”。
