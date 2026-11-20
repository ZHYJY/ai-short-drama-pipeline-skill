# 提示词适配器
内部中间表示IR字段：story_beat, character_ids, identity_lock, scene_id, lighting, props, shot, start_state, end_state, action, dialogue, timing, audio, aspect_ratio, reference_assets, exclusions。
从IR生成：
- generic：自然语言分镜+角色/场景/道具固定描述+动作起止状态，不写未证实的专有参数。
- image_to_video：突出首帧、连续动作、机位与终态；不要求整段人物坐站位置不变。
- text_to_video：加入必要的角色与场景外观描述，说明身份一致性风险。
- per_shot：每镜单独提示词，附剪辑拼接说明。
- multi_shot：仅在模型已验证时提供镜头时间标记和切换指令。
- post_audio：视频画面、配音台词、口型同步、混音分别交付。
不要将某个平台的字段名、JSON参数或负面提示词语法硬套到其他平台。
