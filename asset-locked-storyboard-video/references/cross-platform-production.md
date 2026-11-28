# 跨平台独立控制中心规范

工作台与模型解耦。统一项目数据：project.json、shots.json、assets.json、reviews.json、tasks.json、jobs.json、model-profiles.json。
每个生成任务包含唯一job_id、shot_id、profile_id、model、platform、kind、prompt、parameters、source_asset_ids、status。
允许不同平台生成同一镜头多个候选素材，但只能选择一个最终采用的镜头视频；保留全部生成历史。
平台切换必须保持角色ID、角色身份版本、基准参考图、镜头ID和道具状态；仅改变受影响的提示词格式和生成参数。模型能力未证实则先保守处理。
手动适配器：导出包含来源素材哈希的JSON交接包；真实生成结果导入时绑定原任务、模型与哈希。
文本API适配器：仅支持符合 chat/completions 的HTTPS文本接口；密钥来自DRAMA_前缀环境变量。未授权时禁止发起调用。
图像/视频/音频平台的自动API调用尚未实现，不能用通用文本接口假装完成媒体生成。
审核门禁：沿用素材技术检查、视觉/音频复核、问题返工和成片独立复核。任何未审核或已变更素材不可跳过门禁。
运行：`python scripts/studio_server.py --project ./projects/my-drama`。本地单机运行，不提供公网部署安全保证。
