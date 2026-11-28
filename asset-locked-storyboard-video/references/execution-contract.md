# 执行工具协议
执行器必须明确声明工具名称、可执行动作、输入类型、输出类型、权限、成本/限制和错误返回。
任务状态：planned, ready, running, completed, failed, blocked, not_run。
没有工具的任务永远不能变成 completed；文件名不等于已生成资产。
依赖：剧本→分镜→资产→首帧→视频→拼接；用户提供已验证资产可直接作为依赖输入。
每次调用写执行日志：task_id, platform, model_version, input_asset_ids, prompt_version, settings, status, output_ids, validation, error, retry_count。
批量前先小样，遇到平台不支持参数时调整方案而非无限重试。
用户未授权的外部发布、付费生成、不可逆覆盖不可自动执行。
