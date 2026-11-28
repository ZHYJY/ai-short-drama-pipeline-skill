# 决策引擎
输入 capability_snapshot 和 project_preferences；输出 plan。
1. 支持已验证多镜且 prefer_multishot=true → multi_shot，否则 per_shot；不具备逐镜拼接工具时仍可交付逐镜提示词。
2. 在支持的时长档位中选最接近偏好段长的档位；如果未提供档位，不臆造时长，标记待验证并保留偏好时长作为创作目标。
3. 原生对白仅在能力明确支持时启用；否则 audio_strategy=post_production。
4. 参考图限制为0→text_only；1→first_frame_first；大于1→按首帧、人物、场景、道具排序；未知→reference_strategy=needs_validation。
5. 生成工具不可用→execution_mode=package_only；可用→tool_assisted。
6. 输出每条决策的 reason、confidence、unresolved_checks。
7. 对切换平台执行差异比较；仅标记受影响阶段为 stale，保留 unaffected 阶段。
