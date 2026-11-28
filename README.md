# 15 秒短剧 Skill · 四平台专用与独立生产控制中心

一套跑在你自己电脑上的短剧生产控制中心，加上四个 Agent 宿主（豆包 Work / Codex / TRAE / WorkBuddy）的专用 Skill 入口。工作台负责管住「每个镜头用了哪个平台、哪个模型、哪一版被采用、谁审过、哪条返工没关」，四个平台 Skill 负责在你实际干活的宿主里把任务正确交接出去。

三条原则，写进了代码而不只是文档：

1. **宿主和模型是两个维度。** 豆包 Work、Codex、TRAE、WorkBuddy 是调用环境；真正生成画面的平台和模型由 `model-profiles.json` 与实际任务记录决定。不能因为宿主叫 Codex 就把视频模型记成 Codex。
2. **工作台管数据，模型可替换。** 换平台不重置角色 ID、身份版本、基准参考图、镜头 ID、道具状态与审核记录，只改受影响的提示词格式和生成参数。
3. **没看过就不能判通过。** AI 没有实际查看的画面不得判定人物一致；没有检查过的成片不得标记已通过；缺少视频理解能力时显示「待视觉复核」，而不是假装检查完成。

## 仓库里有什么

| 位置 | 作用 |
| --- | --- |
| `asset-locked-storyboard-video/` | 完整导演 Skill：主流程、30 份规范、11 个脚本、6 个模板、工作台页面 |
| `平台专用技能包/` | 四个独立可安装的 Skill 文件夹（`codex` / `doubao-work` / `trae` / `workbuddy`），每个含 `SKILL.md` 与 `使用提示.md` |
| `四平台独立技能安装包/` | 上述四个 Skill 的成品 ZIP，直接导入各平台技能管理入口 |
| `启动工作台_Windows.bat` / `启动工作台_Mac_Linux.command` | 一键启动独立工作台 |
| `跨平台运行说明.md` | 运行环境、模型配置、典型流程、安全与局限 |
| `详细使用操作手册.md` | 十章完整操作手册：从环境准备到上线验收清单 |
| `使用说明.md` | 最短路径上手：安装、调用、控制中心启动 |

```
asset-locked-storyboard-video/
├── SKILL.md              主流程：阶段 0 能力发现 → 5 交付，含跨平台生产与四宿主入口的强制条款
├── control-center/       工作台页面（进度、素材、审核、返工、模型路由、任务交接）
├── references/           30 份规范 + 1 份能力 schema
├── scripts/              11 个可离线运行的脚本
├── templates/            6 个 JSON 模板
└── examples/             generic 能力快照与偏好示例
```

## 这一版升级了什么

上一版是一个「导演 Skill + 生产控制中心」，这一版把它变成**可独立运行的跨平台生产系统**。

### 一、独立工作台取代内嵌服务

新增 `scripts/studio_server.py`：一条命令启动，自动打开浏览器，可指定任意项目目录，未指定时用 `projects/我的短剧`。Windows 双击 `启动工作台_Windows.bat`，macOS / Linux 运行 `sh 启动工作台_Mac_Linux.command`。服务只监听 `127.0.0.1`，仍然拒绝跨站写入。

原有的 `production_center.py` 保留，继续提供 `init / check / preflight / final / serve`，并作为工作台的底座被复用。

### 二、跨平台模型路由

新增 `scripts/model_router.py`，把「配置模型 → 建任务 → 导出交接 → 导入真实结果」串成闭环：

- **模型配置**：预置通用图片 / 视频 / 配音三个手动平台配置，外加一个可选的兼容文本接口配置。配置是「能力声明」，声明支持 `text / image / video / audio` 哪些任务类型
- **任务队列**：每个任务拿到唯一 `JOB-00001` 形式的 ID，记录 `shot_id`、`profile_id`、模型、平台、任务类型、提示词、参数、引用素材、状态
- **交接包**：导出 `handoffs/JOB-xxxxx.json`，含镜头信息、提示词、参数与来源素材的 SHA256，明确标注「在对应平台完成生成，不得将未生成任务标为完成」
- **结果导入**：把真实文件放回项目目录后导入，系统按任务类型校验扩展名（视频 `mp4/mov/mkv/webm`、图片 `png/jpg/jpeg/webp`、音频 `wav/mp3/ogg/m4a`、文本 `txt/md/json`），非空才算数，并自动登记模型、平台、提示词、参数、来源素材、文件哈希，同时把任务置为 `completed`
- **重复导入拦截**：已完成的任务不允许再导入，避免一任务多结果导致台账失真
- **可选文本接口**：只接受不带凭证与查询参数的 HTTPS `chat/completions` 端点，密钥必须放在 `DRAMA_` 前缀的环境变量里（配置文件里写 `api_key`、`token`、`password` 会被直接拒绝），调用时不跟随重定向，防止密钥被转到别的主机

**图片、视频、音频平台的自动 API 调用尚未实现**，包内不会用文本接口假装完成媒体生成。

### 三、四宿主任务交接

新增 `scripts/platform_handoff.py` 与 `references/four-agent-hosts.md`：

```bash
python scripts/platform_handoff.py ./projects/我的短剧 codex JOB-00001
```

把 `codex` 换成 `doubao-work`、`trae`、`workbuddy` 即可。输出一份 JSON 和一份 Markdown，包含项目元数据、镜头定义、任务、来源素材哈希、宿主专属操作指引，以及四条强制质量门禁（`real-media-check`、`identity-review-with-evidence`、`audio-review-with-evidence`、`final-independent-review`）。状态固定为 `handoff_only_not_executed`——交接不等于执行。

### 四、四个平台专用 Skill

| 平台 | Skill 名称 | 面向谁 | 安装位置 | 关键约束 |
| --- | --- | --- | --- | --- |
| 豆包 Work | `drama-director-doubao-work` | 创作者、运营、不写代码的人 | 技能管理或自建技能入口导入 | 云端访问不到本地 `127.0.0.1` 时不得声称工作台已同步，导出 JSON 后由本地导入 |
| Codex | `drama-director-codex` | 开发者 | 项目内 `.agents/skills/drama-director-codex/` 或 `~/.agents/skills/` | 先探测 Python / FFmpeg、目录权限与可用媒体工具，真实外部调用需授权 |
| TRAE | `drama-director-trae` | IDE 用户 | 工作区 `.trae/skills/drama-director-trae/` | 打开可信工作区、确认技能已启用；无文件或终端权限时只给操作清单 |
| WorkBuddy | `drama-director-workbuddy` | 协作团队 | 技能管理入口上传技能包 | 重视任务分工、审核证据与交付清单；企业管理员可限制安装 |

四个 Skill 共用同一套创作与审核协议：角色圣经建档 → 镜头绑定 → 逐镜提示词 → 真实能力检测 → 任务交接 → 双道门禁 → 交付清单。四份 `使用提示.md` 各自写明安装方式、调用示例与平台约束。

### 五、工作台页面新增面板

控制台在原有「质量门禁」「视频抽帧与问题追踪」「生产任务与审核操作」「按剧情顺序排列的素材」「任务队列」之外，新增：

- **跨平台模型路由与任务交接**：创建跨平台生成任务（选配置、填镜头 ID、提示词、引用素材）、导入平台生成结果（填任务 ID、项目内结果路径、新素材 ID）
- **添加 / 修改模型配置**：配置 ID、显示名称、适配器（手动生成平台 / 兼容文本接口）、支持能力（视频 / 图片 / 音频 / 文本）、真实模型 ID、HTTPS 接口地址、密钥环境变量名称，页面明确标注「密钥只放在本机环境变量，不填写到网页配置里」
- **跨平台任务队列**：查看任务状态、导出通用交接包、导出豆包 Work / Codex / TRAE / WorkBuddy 专用包、对兼容文本接口任务发起真实调用，并与原有的返工任务队列分开展示

## 工作台怎么跑

最低要求 Python 3.10+；视频抽帧与媒体元数据检查另需 FFmpeg（`ffmpeg` / `ffprobe` 可用）。

- **Windows**：双击 `启动工作台_Windows.bat`（脚本会先试 `py -3`，失败再用 `python`）
- **macOS / Linux**：`sh 启动工作台_Mac_Linux.command`，或双击（可能需要系统允许执行）
- **手动指定项目**：`python asset-locked-storyboard-video/scripts/studio_server.py --project "/你的项目路径"`

默认项目目录是 `projects/我的短剧/`，会自动创建 `project.json`、`shots.json`、`assets.json`、`reviews.json`、`tasks.json`、`jobs.json`、`model-profiles.json`。工作台会尝试自动打开浏览器，没有打开就访问 `http://127.0.0.1:8765`；关闭终端或 Ctrl+C 即停止。

## 一部短剧怎么走完

1. **准备输入**：故事、总时长、画幅（默认 9:16）、风格、角色参考图、声音与字幕要求
2. **先锁角色再拆镜头**：建立人物圣经（脸型骨相、五官比例、发际线、肤色、头身比、服装材质配饰、声线、表演习惯），分离永久身份与剧情可变状态；没有批准的参考图不声称角色已锁定
3. **建镜头时间轴**：逐镜写角色 ID 与身份版本、服装版本、站位视线、动作起止、道具归属、场景坐标、对白与音效，时间轴从 0 连续覆盖目标时长
4. **配置模型**：在工作台添加配置，声明它能做哪类任务
5. **创建任务**：选配置、填镜头 ID 与提示词、勾选引用素材，得到 `JOB-xxxxx`
6. **导出交接包**：把 `handoffs/JOB-xxxxx.json` 交给对应平台，或直接导出四宿主专用包
7. **去平台生成**：在真实平台出图出视频，把结果复制到项目的 `media/` 目录
8. **导入结果**：输入任务 ID、文件相对路径、新素材 ID，系统登记模型与哈希并把任务置为已完成
9. **抽帧与复核**：对视频抽 3–30 帧（记录时间点、帧哈希、原视频哈希），由真实视觉工具或人工填写审核证据；发现问题登记 `FIX-*` 返工任务
10. **合成前门禁**：每个镜头必须且只能有一个被采用的正式视频，且 `identity / visual / continuity / audio` 四类证据齐全，否则阻断合成
11. **合成**：门禁通过后才允许合成
12. **成片门禁**：成片作为 `final_video` 导入，完成 `final_visual / final_audio / final_continuity / final_narrative` 四类独立复核，且前置门禁仍有效、素材哈希未变化，才允许交付
13. **交付**：区分「已真实执行 / 已规划未执行 / 待审核」三类清单

## 数据文件

| 文件 | 作用 |
| --- | --- |
| `project.json` | 项目元数据（标题、目标时长、画幅） |
| `shots.json` | 镜头列表，按剧情顺序与时间轴排布 |
| `assets.json` | 每次生成的独立素材：路径、平台、模型、提示词、参数、来源、任务 ID、文件哈希、采用状态 |
| `reviews.json` | 审核证据：绑定素材哈希、审核维度、结论、审核人、时间 |
| `tasks.json` | 返工与生成任务：类型、状态、严重程度、分类 |
| `jobs.json` | 跨平台任务：任务 ID、配置、模型、平台、类型、提示词、参数、来源素材、状态 |
| `model-profiles.json` | 模型配置与能力声明（不含任何密钥） |
| `visual-review-queue.json` | 抽帧结果与待复核清单 |
| `handoffs/` | 导出的交接包（通用包与四宿主专用包） |
| `media/` | 从各平台拿回来的真实素材 |
| `generated_text/` | 兼容文本接口真实调用产生的文本 |
| `technical-check.json` / `preflight-gate.json` / `final-gate.json` | 三类检查的最近一次结果快照 |

## 脚本一览

| 脚本 | 职责 |
| --- | --- |
| `studio_server.py` | 独立工作台启动器：项目初始化、模型路由接口、自动开浏览器 |
| `production_center.py` | 基础工作台与门禁：`init` / `check` / `preflight` / `final` / `serve` |
| `model_router.py` | 模型配置、任务提交、交接包导出、结果导入、可选文本接口调用 |
| `platform_handoff.py` | 生成四宿主专用交接包（JSON + Markdown） |
| `visual_review_pipeline.py` | 视频抽帧建档（`audit`）与返工任务登记（`issue`） |
| `adapt.py` | 能力快照驱动的参数与策略决策 |
| `director_validate.py` | 导演计划静态校验：时长、坐标、台词、音频时间线 |
| `workflow_plan.py` | 任务图就绪 / 阻塞 / 完成 / 循环依赖计算 |
| `validate_characters.py` | 角色 ID、版本、镜头引用、未声明换装与状态接续校验 |
| `review_gate.py` | 校验审核报告并计算门禁，拒绝缺证据的「通过」 |
| `asset_audit.py` | 资产格式、尺寸、宽高比、清晰度启发式、曝光、完整性与覆盖检查 |

## 安装 Skill

- **四个平台入口**：直接导入 `四平台独立技能安装包/` 里的 ZIP，或把 `平台专用技能包/<平台>/` 整个目录按上表位置放好，目录内直接包含 `SKILL.md`
- **完整导演 Skill**：把 `asset-locked-storyboard-video/` 整个目录安装到支持 Skills 的环境，目录名与 `SKILL.md` 里的 `name` 保持一致
- **工作台**：不需要安装，它是本仓库自带的本机程序，双击启动脚本即可

## 调用示例

> 请使用「短剧全流程导演-豆包 Work」技能，先建立角色圣经与镜头清单，逐镜生成可执行提示词。确认当前会话可用的真实图片 / 视频工具；能调用才执行，否则输出交接任务包。将结果按照镜头编号、模型和平台登记到独立工作台，成片前后均复核。

命令行侧的等价入口：

```bash
# 提交任务并导出交接包
python asset-locked-storyboard-video/scripts/model_router.py submit ./projects/我的短剧 --file job.json
python asset-locked-storyboard-video/scripts/model_router.py handoff ./projects/我的短剧 JOB-00001

# 导入真实结果
python asset-locked-storyboard-video/scripts/model_router.py import ./projects/我的短剧 JOB-00001 \
  --path media/SH01_v1.mp4 --asset-id A001

# 抽帧与问题登记
python asset-locked-storyboard-video/scripts/visual_review_pipeline.py audit ./projects/我的短剧 A001 --count 7
python asset-locked-storyboard-video/scripts/visual_review_pipeline.py issue ./projects/我的短剧 A001 \
  --category identity --severity high --description "第 3 秒起发型发生漂移"
```

运行模式：`AUTO` 全自动、`REVIEW` 分阶段确认、`STAGE` 只做指定阶段、`MIGRATE` 平台切换后只重算受影响部分。

## 离线校验

除抽帧之外，其余脚本不需要 FFmpeg、不调用任何平台：

```bash
python asset-locked-storyboard-video/scripts/adapt.py asset-locked-storyboard-video/examples/generic-capability.json asset-locked-storyboard-video/examples/generic-preferences.json
python asset-locked-storyboard-video/scripts/director_validate.py asset-locked-storyboard-video/templates/director-plan.template.json
python asset-locked-storyboard-video/scripts/workflow_plan.py asset-locked-storyboard-video/templates/workflow.template.json
python asset-locked-storyboard-video/scripts/review_gate.py asset-locked-storyboard-video/templates/visual-review.template.json
python asset-locked-storyboard-video/scripts/production_center.py init ./demo
python asset-locked-storyboard-video/scripts/production_center.py check ./demo
```

`validate_characters.py` 需要两个输入（角色列表与分镜列表），按 `... validate_characters.py <人物圣经.json> <分镜.json>` 调用。

## 能力边界

这部分如实写，不包装成「全自动审核」：

- **图片、视频、音频平台的自动 API 调用未实现**。手动平台走「导出交接包 → 平台生成 → 导入结果」；兼容文本接口只支持 `chat/completions` 风格的 HTTPS 文本端点，接口兼容性需以提供商文档和实测为准
- **自动抽帧与问题管理已实现**，但「是否换脸、动作是否自然、口型是否同步」仍需接入视觉与音频理解模型，或由人工实际查看。当前包未预接任何第三方视觉模型
- 没有 `ffmpeg` / `ffprobe` 时不会假装检验过视频：抽帧直接报错说明缺依赖，技术检查返回 `unverified`，而 `unverified` 永远不等于 `pass`
- 工作台的「生成」按钮只登记任务，不伪造平台调用；模型配置是能力声明，不是对供应商全部接口能力的动态验证
- 技术检查、抽帧与文件哈希不能证明人物身份一致，也不能代替成片复核
- 服务只监听 `127.0.0.1`，无账号系统、团队权限、云同步和后台任务持久化；JSON 写入用临时文件替换，但不等于事务数据库，多个进程同时写同一项目不受支持
- 门禁判定已逐条验证过：无审核证据阻断、四类证据缺项阻断、高风险返工未关闭阻断、素材改动后旧证据失效、双道证据齐全时放行。验证的是判定逻辑本身，它只消费真实文件与真实哈希

## 使用约定

- 用户提供的参考图是外观事实的优先来源；不可见的背面、身高、声音标注为待定或创作假设，不伪称从图片得出
- 原参考图不可覆盖；资产登记路径、来源、哈希、视角、版本与批准状态
- AI 没实际看过的画面不判人物一致；没检查过的成片不标已通过
- 素材修改或替换后按新素材 ID 重新审核，旧证据不得沿用
- 同一镜头连续两次定向修复失败即停止盲试，改用拆镜、减少遮挡或换用已验证参考
- 密钥只放环境变量，不写进项目 JSON、提示词或任务包
- 不以规避平台审核为目标修改提示词

## 声明

本仓库为创作流程与工程规范文档，不含任何第三方 API 凭证、个人数据或受限素材。实际生成依赖使用者所拥有并授权的工具与平台。
