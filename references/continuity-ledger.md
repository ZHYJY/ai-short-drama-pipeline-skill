# 跨段连续性台账
固定身份（不可漂移）：角色ID、脸部特征、发型、服装基础款、声音设定；场景ID、空间布局、主光源方向；道具ID、材质外观。
动态状态（必须按剧情变化）：段/镜号、人物坐标或画面左右、姿态、视线、情绪、手持物及左右手、衣服变化理由、道具所在位置与开合状态、镜头轴线、上镜结束动作、下镜开始动作。
建议表头：`segment,shot,character_id,screen_side,pose,gaze,emotion,held_prop,prop_hand,prop_state,scene_id,light_direction,entry_state,exit_state,continuity_notes`
段N的exit_state必须能解释段N+1的entry_state；出现跳跃时补过渡镜、修改分镜或明确省略时间。
180度轴线规则作用于空间方向和视线关系，不能简单要求人物在所有正反打镜头中固定屏幕左右。
用户已有图像必须保持原图，派生图标记来源与版本。
