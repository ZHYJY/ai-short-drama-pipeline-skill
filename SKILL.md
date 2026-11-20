---
name: asset-locked-storyboard-video
description: 角色数字身份锁定与跨平台自适应 AI 短剧生产工作流。将故事转成剧本、分镜、角色/场景/道具资产、首帧与视频提示词，调用时自动探测当前平台能力，选择分段时长、参考图策略、镜头生成模式、音频方案、执行工具及质检方法。适合15秒短剧及其他时长、无限画布或独立视频生成工具。
---

# 自适应 AI 短剧生产 Skill ## 核心原则
**创作规范与平台执行解耦。先检测能力，再规划可执行方案。**
本 Skill 不预设任何平台一定支持某种参数、工具或API。任何执行都必须通过当前环境实际提供的工具完成；不能执行时交付生产包，并明确标注“未生成视频”。

## 触发与输入
当用户要求短剧、AI剧场、故事转分镜、角色一致性、首帧图生视频、逐段生成、跨平台迁移或失败修复时启用。
抽取：故事/脚本、总时长、单段偏好（默认15秒）、比例（默认9:16）、风格、平台名称或工具环境、角色参考、声音/字幕要求、预算与输出目标。
仅询问缺失且会阻断当前操作的必要信息。平台未指定时不要求用户先选平台：以平台无关方案先做创作包。

## 运行模式
- AUTO：自动完成可用的文本规划、能力预检与校验；实际高成本生成遵循用户授权及工具限制。
- REVIEW：剧本、分镜、资产、视频分别确认。
- STAGE：仅完成用户指定的阶段。
- MIGRATE：平台切换后只重算受影响的段长、参考图、参数与提示词，不重新设计无关资产。

## 阶段0：运行环境与能力发现（每次调用必须执行）
读 `references/adaptive-platform.md` 和 `references/capability-schema.json`。
1. 列举当前真实可用的生成/编辑工具和可访问平台。不得臆测拥有浏览器操作、视频生成或文件写入权限。
2. 如果用户指定平台，优先使用当前工具的可查询能力或官方文档/实际测试；无法验证时能力标记 `unknown`。
3. 如果未指定平台，使用 `generic` 配置，避免特定模型参数。
4. 输出 `capability_snapshot`，包括证据来源、验证日期、能力状态。上一次缓存仅供参考，关键参数需重新确认。
5. 运行决策引擎 `scripts/adapt.py`，或依照 `references/decision-engine.md` 同等规则手工决策。
6. 若用户从平台A切换B，比较快照，输出差异与最小迁移计划。

## 阶段1A：角色数字身份建档（必经质量门禁）
读 `references/character-bible.md`、`references/identity-lock-protocol.md`、`references/reference-image-standard.md`、`references/multicharacter-protocol.md`。
每个主角建立结构化 `character_id`、`identity_version`、完整人物圣经（脸、体型、造型、声音、表演、动态状态），附证据来源、确定性等级和可变更策略。
**用户参考图是外观事实优先来源**：能直接观察到的才标记已确认；不可见的背面、身高、声音等标为待定/创作假设，绝不伪称已从图片得出。
首次建档后先做一致性基准评估；需要生成角色参考图时先做候选与验收，再锁定最终参考。**没有真实参考图时只标记文本锁定，不宣称像素级一致**。
任何镜头引用固定身份字段时采用角色ID+版本+不可变特征清单；动作、表情、换装属于独立的动态状态。
检查 `references/character-qa-rubric.md`；主角身份基准未通过不得批量生成镜头。

## 阶段1：剧情与资产模型
读 `references/script-build.md`、`references/asset-lock.md`、`references/continuity-ledger.md`。
产出角色卡、场景卡、道具卡、剧情节拍、对白与跨镜状态台账。
身份字段稳定复用，动态状态按剧情更新。角色原始参考图不得覆盖。
若平台尚未确定，先写平台无关的剧情节拍，不提前把所有对白硬塞进15秒档。

## 阶段2：自适应分段与分镜
读 `references/shot-continuity.md`、`references/timing-and-validation.md`。
- 先依据平台允许的时长档位选择分段策略；15秒是偏好而非不可突破的硬约束。
- `single_shot`：单镜生成，后期拼接。
- `per_shot`：每镜独立生成，后期硬切；平台内部多镜未验证时优先此模式。
- `multi_shot`：仅当平台多镜能力已验证且用户希望时采用。
- 不支持目标段长时拆段或采用可剪裁档位，保证剧情和对白不被裁断。
- 所有镜头时间轴从0到目标段长连续覆盖；台词以有效说话时间及测试语速校验。

## 阶段1B：角色资产生产与视觉质量基线
读 `references/asset-production-pipeline.md`、`references/visual-review-protocol.md`。
先从人物圣经建立 `asset_manifest` 和覆盖矩阵，明确正脸、左右侧脸、3/4脸、全身、背面、表情、服装细节哪些是必需、哪些是可选。根据镜头实际需要决定补图优先级，不盲目生成全套。
已有参考图须登记路径、来源、哈希、视角、角色ID、身份版本、批准状态；原图不可覆盖。可运行 `scripts/asset_audit.py` 进行图像格式、尺寸、宽高比、清晰度启发式、曝光、文件完整性与覆盖检查。该脚本不判断是不是同一个人。
在有真实视觉分析工具或人工审核时，按 `references/visual-review-protocol.md` 对骨相、五官、体型、衣装、特征点和跨镜状态打分；没有视觉能力时 `identity_status=unverified`，不得标为通过。

## 阶段2A：导演决策、空间调度与表演设计
读 `references/director-engine.md`、`references/spatial-blocking.md`、`references/audio-lipsync.md`。
对每段设定：戏剧任务、冲突/转折、观众信息增量、情绪曲线、关键视觉动作、镜头切换动机、音频重点、段尾钩子。镜头不以数量为目标，而以清晰表达为目标。
建立场景坐标系、人物入/出场位置、视线目标、相机方位、动作接触点与道具归属。空间不明时不得假定人物左右固定。
对白使用时间区间和speaker_id绑定，规划语音、反应、静默与口型；不支持原生音频则交付后期声音任务。
运行 `scripts/director_validate.py` 检查镜头时长、场景坐标、人物/台词引用、角色起止状态与音频时间线；静态检查不等于模型真实执行效果。

## 阶段2B：镜头级角色一致性绑定
每镜写明角色ID/版本、角色出现顺序、画面位置、与其他人的空间关系、服装版本、发型状态、持物手、表情、起止姿态、机位与镜头轴线。
多角色同框按 `references/multicharacter-protocol.md` 明确绑定角色与参考图；当平台无法可靠处理多人参考时拆镜、分层生成或后期合成，标注各自风险。
镜头开始与结束状态必须与相邻镜头台账一致。角色发生合法变化时记录 `change_event`，禁止无记录的“自动换脸/换装”。

## 阶段3：资产、首帧与提示词适配
读 `references/prompt-templates.md`、`references/prompt-adapters.md`、`references/identity-lock-protocol.md`、`references/reference-image-standard.md`。
- 将提示词分为：不变的故事意图、角色身份、场景空间、镜头动作、平台参数、负面约束。
- 根据参考图数量限制自动分配：当前镜首帧 > 人物身份 > 场景 > 道具；不足时使用经验证的合成参考板或拆镜，不声称合成板必然有效。
- 首帧是镜头起始状态，不锁死镜头中后续动作和走位。
- 无法原生生成对白时，拆为画面生成、配音、口型/剪辑后期；没有相应工具时输出操作说明。
- 输出平台无关主提示词及平台专用适配提示词；能力未知时不写虚构参数。

## 阶段4：执行与质量门禁
读 `references/quality-gates.md`、`references/troubleshooting.md`、`references/execution-contract.md`、`references/character-qa-rubric.md`。
- 每项任务执行前检查输入资产是否真实存在、工具是否可用、用户是否授权。
- 执行结果必须包含：`status=completed|failed|blocked|not_run`、产物路径/ID（如真实存在）、实际参数、可验证证据。
- 按剧本→分镜→资产→首帧→视频→拼接的依赖关系推进。允许在用户已提供合格上游产物时跳过重复生成，但不跳过校验。
- 失败优先最小范围修复：提示词→首帧→该镜→依赖镜头；不反复盲试。
- 无工具时停止在可执行生产包，不假装调用平台。

## 阶段3B：依赖任务图与安全执行
读 `references/task-orchestration.md`、`references/execution-contract.md`。
将剧本、角色基准、场景资产、镜头首帧、镜头视频、音频、剪辑、质检建成有向无环依赖图。运行 `scripts/workflow_plan.py` 可计算就绪、阻塞、完成和循环依赖。
只有真实存在、且经对应质量门禁批准的资产才能解除下游阻塞。没有外部工具时输出任务计划，不伪称执行。
平台切换时计算受影响任务，保留不受影响的剧本和角色资产；凡依赖失效任务的下游都需重新验证。

## 阶段4B：漂移诊断与定向修复
读 `references/drift-repair-playbook.md` 和 `references/visual-review-protocol.md`。
每个生成镜头保留首帧、中间关键帧、末帧的真实资产引用；将审核结果写入 `review_report.json`。
把问题分为身份漂移、发型/服装版本错误、多人特征串用、空间/道具状态跳变、技术画质问题；按问题类别执行最小范围修复。每次记录提示词版本、参考资产、平台能力快照、修改变量与复测结论。
若同一镜头连续两次定向修复仍失败，停止盲目重试，改用拆镜/减少遮挡/更换已验证参考或人工处理，并明确成本与风险。

## 阶段5：拼接与交付
统一画幅、分辨率、帧率、音量与字幕策略；检查段间人物/道具状态、台词完整、总时长。
交付 `项目配置`、`能力快照`、`剧本`、`资产卡`、`状态台账`、`分镜表`、`提示词`、`执行记录`、`质检报告` 和实际已生成的媒体。
输出三类清单：已完成、待执行、能力未知/风险。

## 不变的质量底线
角色身份一致（需证据验收，不能承诺绝对不变）、动作物理合理、跨镜道具状态连续、时间轴无缺口、无捏造的平台能力和生成结果。
用户明确要求字幕或屏幕文字时允许后期加字；不以规避审核为目标修改提示词。
原参考文档若与V3规则冲突，以本文件及新增适配规范为准。

## 新增模板与检查
- `templates/character-bible.template.json`：详细人物设定；所有未知信息必须标记，不能编造为参考图事实。
- `templates/shot-character-binding.template.json`：镜头级角色绑定和状态变化。
- `scripts/validate_characters.py`：静态校验角色ID、版本、关键字段、镜头引用、未经声明的换装及状态接续；**不能代替视觉识别或证明生成视频中的脸完全一致**。
- `references/character-qa-rubric.md`：人工视觉验收量表，含阻断条件。

## 资产与视觉质检工具
- `references/asset-production-pipeline.md`：按镜头需求规划角色资产，生成候选→审核→批准→冻结版本。
- `references/visual-review-protocol.md`：人工或具备视觉能力的模型逐项审核，明确证据与不可见项。
- `references/drift-repair-playbook.md`：按故障类别选择最小修复路径与重试上限。
- `templates/asset-manifest.template.json`：资产身份、版本、视角、哈希、来源、状态。
- `templates/visual-review.template.json`：逐项评分、证据、处理建议。
- `scripts/asset_audit.py`：离线资产检查、文件哈希、基础画质指标与覆盖率，不进行人脸识别。
- `scripts/review_gate.py`：验证人工/视觉模型的审核报告，计算门禁结果，拒绝缺证据的“通过”。
不得将这些静态脚本称作自动识别人脸或自动生成视频；外部平台调用仍需真实可用工具。

## 导演系统入口
- `references/director-engine.md`：镜头语言、剧情节奏、表演与导演决策。
- `references/spatial-blocking.md`：场景坐标、人物走位、视线、接触点、轴线。
- `references/audio-lipsync.md`：角色声线、台词节奏、音轨与口型工作流。
- `references/task-orchestration.md`：任务依赖、失效传播、重试与交付门禁。
- `templates/director-plan.template.json`、`templates/workflow.template.json`：结构化导演计划和任务图。
- `scripts/director_validate.py`、`scripts/workflow_plan.py`：可运行静态校验与任务规划。
所有自动校验只保证数据逻辑，不代表真实画面、口型或角色身份已通过视觉审核。
