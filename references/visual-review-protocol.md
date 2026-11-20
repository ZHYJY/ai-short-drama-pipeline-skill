# 视觉一致性审核协议
只对真实可见的图像/视频关键帧打分。审核者可为人工或明确具备图像理解能力的工具；若不可访问图像，必须标 not_reviewed。
## 比对对象
同一角色的已批准基准参考、目标镜头首帧、中间关键帧、末帧；多人镜头逐人比对。侧脸优先同视角基准；不同角度只评价可见的稳定特征。
## 维度与权重（项目默认，可配置）
face_geometry 25, eyes_brows 15, nose_mouth 15, hairline 10, body_proportion 10, outfit 10, distinctive_marks 10, cross_shot_state 5。权重仅用于报告汇总，不代表生物识别准确率。
每项 score 0/1/2 或 null（不可见）；同时记录 visible、evidence（可见依据）、issue_type、severity。不能把不可见项目当作满分。
## 阻断规则
P0：明显换脸、骨相改变、独特标记无故消失/移位、角色间五官互换、严重体型比例漂移；直接 reject。
P1：无记录换装、道具突然消失/易手、声音错配；需修复或核对剧情事件。
技术问题：严重模糊、过曝、遮挡、画面损坏；不能据此判定身份不一致，应标 review_required 或 technical_fail。
## 门槛
所有可见P0项需score=2；非P0适用项加权归一化均分建议≥1.7/2；至少有face_geometry、eyes_brows、nose_mouth中的两项可见，否则不得自动通过身份门禁。
如果没有人工/视觉模型审阅证据，gate只能为 needs_review。即使通过也表示“本次审核符合标准”，绝不表示跨平台绝对不漂移。
## 输出
每项记录 `dimension, score, visible, evidence, severity`，并提供审核者、基准资产ID、目标资产ID、镜头ID、审核时间、是否有真实图像访问、处理建议。
