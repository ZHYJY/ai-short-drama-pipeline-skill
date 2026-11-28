# 视觉复核与返工闭环
1. 依赖 ffmpeg/ffprobe 抽取视频采样帧，记录时间点、帧哈希、原视频哈希；抽帧并非身份识别。
2. 用角色ID查找人物圣经和基准图，检查五官、体型、服装、道具、动作、镜头首尾与多人同框。
3. 仅在实际有权限的视觉模型或人工查看真实素材后，才能写入审核结论及证据；工具不可用时状态保持 needs_visual_review。
4. 音频、口型和动态动作必须实际查看连续视频、听取音频或调用对应分析工具，不能只看抽帧。
5. 发现问题创建 FIX-* 返工任务，记录严重程度、受影响素材、素材哈希；高风险未关闭问题阻断门禁。
6. 返工产生新素材ID；旧素材及审核记录保留；新素材重新进行技术、视觉和音频复核。
7. 成片 final_video 独立抽帧并复核完整视频，检查字幕、音轨、转场、角色、故事完整度和片尾。
命令：
python scripts/visual_review_pipeline.py audit ./my-drama A001 --count 7
python scripts/visual_review_pipeline.py issue ./my-drama A001 --category identity --severity high --description "发型发生漂移"
局限：均匀抽帧不是自动镜头边界识别；本包未预接第三方视觉模型。
