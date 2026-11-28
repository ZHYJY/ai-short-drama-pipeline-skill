# 有向任务图与执行纪律
任务类型：script, character_bible, character_reference, scene_asset, shot_plan, first_frame, video_shot, voice, lip_sync, edit, visual_review, audio_review, final_delivery。
任务字段：task_id, type, depends_on[], status, gate, platform_scope, input_asset_ids, output_asset_ids, retries, max_retries, approved, error。
合法状态：planned, ready, running, completed, failed, blocked, not_run。`completed`不代表质检通过，gate=approved才允许被要求质检的下游使用。
执行前检查依赖全部completed，且需审批的依赖gate=approved；阻断下游时写出原因。不得为模拟完成而伪造产物ID。
支持最小返工：只将发生变更的任务及依赖它的后代标记stale；不影响的角色圣经和剧本保留。
跨平台迁移：平台专属video_shot、prompt adapter、音频能力、输出格式重新评估；通用剧情/人物身份不无故重写。
每任务最多配置有限重试，超过上限停止并交人工/换策略；付费、发布、覆盖动作必须遵守授权。
工作流脚本仅做依赖规划，不执行网络调用或媒体生成。
