# 四个平台专用调用入口

**宿主（Agent）与媒体生成模型必须分开记录。** 豆包 Work、Codex、TRAE、WorkBuddy 是本 Skill 的调用环境；生成平台/模型由 `model-profiles.json` 和实际任务记录决定。不能因为宿主叫 Codex 就把视频模型记为 Codex。

- 豆包 Work：创作者自然语言调用，先检测是否可调用图片/视频工具；云端无法访问本地127.0.0.1时导出任务交接包。
- Codex：项目技能位于 `.agents/skills/drama-director-codex/SKILL.md`；使用项目终端与脚本验证，真实外部调用需要权限。
- TRAE：项目技能位于 `.trae/skills/drama-director-trae/SKILL.md`；打开可信工作区、确认技能已启用。
- WorkBuddy：使用技能管理的本地上传入口；重视任务分工、审核证据与交付清单，无法执行脚本时走人工交接。

统一任务交接命令：
`python scripts/platform_handoff.py /项目路径 codex JOB-00001`
将 `codex` 替换为 `doubao-work`、`trae`、`workbuddy`。输出 JSON 和 Markdown，均为未执行任务，不能冒充生成结果。

四个技能包在根目录 `平台专用技能包`，可独立安装；完整工作台与项目素材在 `核心工作台`。同一个工作台项目不要并行用多个进程直接写入JSON。
