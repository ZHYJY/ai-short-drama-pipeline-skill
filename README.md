# 15 秒短剧 Skill · 全流程 AI 导演系统

面向 AI 短剧生产的 Skill：把故事拆成剧本、分镜、角色与场景资产、首帧与视频提示词，并在调用时先探测当前平台真实能力，再决定分段时长、参考图策略、镜头生成模式、音频方案与质检方法。

核心原则：**创作规范与平台执行解耦，先检测能力，再规划可执行方案。**

## 它解决什么问题

AI 短剧最难的不是"生成一帧好看的图"，而是跨镜头的一致性：角色脸、服装、发型、道具状态、空间关系、台词时长都可能在中途漂移。本 Skill 用一套可验收的流程把这些约束显式化：

- 角色数字身份建档（character_id + identity_version + 人物圣经），未知信息必须标记，不得伪称从参考图得出
- 镜头级角色绑定，写明角色ID、出现顺序、画面位置、起止姿态、机位与轴线
- 跨镜状态台账，合法变化需记录 `change_event`，禁止无记录的换脸换装
- 资产清单 + 视觉审核量表 + 漂移诊断与最小修复路径
- 依赖任务图（DAG）：只有真实存在且通过门禁的资产才能解除下游阻塞
- 逐项记录 `status=completed|failed|blocked|not_run`，不虚构平台参数与生成结果

## 能力边界

本 Skill 不预设任何平台一定支持某种参数、工具或 API：

- 没有真实工具时，停在"可执行生产包"并明确标注未生成视频，不假装调用平台
- 静态脚本只做数据逻辑校验，**不人脸识别、不证明口型同步、不生成视频**
- 角色一致性以证据验收为准，不做"绝对不变"的承诺
- 平台能力无法验证时标记 `unknown`，不写虚构参数

## 目录结构

```
SKILL.md                     主流程（阶段 0 能力发现 → 5 交付）
使用说明.md                   快速上手与调用示例
references/                  26 份规范：角色圣经、身份锁定、参考图标准、多人协议、
                             分镜连续性、导演引擎、空间调度、声音口型、任务编排、
                             质检门禁、故障修复、平台自适应等
templates/                   JSON 模板：人物圣经、镜头角色绑定、资产清单、
                             视觉审核、导演计划、任务图
scripts/                     可离线运行的校验脚本
examples/                    generic 能力快照与偏好示例
```

## 安装

把本仓库作为 Skill 目录安装到支持 Skills 的环境中（例如放到 `.skills/asset-locked-storyboard-video/`），目录名与 `SKILL.md` 里的 `name` 保持一致。

## 调用示例

> 把这个故事做成 60 秒竖屏短剧，使用 V6 自动导演模式。先锁定角色全维度形象与参考图，规划剧情节奏、空间走位、逐镜台词与音频，检测当前平台能力后生成可执行任务图；有真实工具才生成视频，逐镜验收。

运行模式：`AUTO` 全自动、`REVIEW` 分阶段确认、`STAGE` 只做指定阶段、`MIGRATE` 平台切换后只重算受影响部分。

## 离线校验

仅需 Python 3，无第三方依赖：

```bash
python scripts/adapt.py examples/generic-capability.json
python scripts/director_validate.py templates/director-plan.template.json
python scripts/workflow_plan.py templates/workflow.template.json
python scripts/validate_characters.py templates/character-bible.template.json
python scripts/review_gate.py templates/visual-review.template.json
python scripts/asset_audit.py --help
```

这些脚本只校验结构、引用与时间轴逻辑，输出通过不代表真实画面或角色身份已通过视觉审核。

## 使用约定

- 用户提供的参考图是外观事实的优先来源；不可见的背面、身高、声音标注为待定或创作假设
- 原参考图不可覆盖，资产登记路径、来源、哈希、视角、版本与批准状态
- 同一镜头连续两次定向修复失败即停止盲试，改用拆镜、减少遮挡或换用已验证参考
- 不以规避平台审核为目标修改提示词

## 声明

本仓库为创作流程与工程规范文档，不含任何第三方 API 凭证、个人数据或受限素材。实际生成依赖使用者所拥有并授权的工具与平台。
