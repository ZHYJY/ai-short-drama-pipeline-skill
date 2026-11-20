# 场景空间与人物调度
为每个场景定义右手或明确标记的二维地面坐标系：原点、x/y单位（米或归一化单位）、入口、出口、门窗、家具、多边形障碍、光源方位。相机可记录(x,y,z)、朝向目标点和轴线侧。
人物每镜记录 entry_position、exit_position、facing_target、gaze_target、pose、held_prop_id、held_hand、contact_points、movement_path。道具记录owner/position/state。
硬切连续性：若时间连续，上一镜人物exit与下一镜entry应一致或在容差内；若时间跳跃，标注ellipsis=true及解释。人物在同一时刻不能占据两个互斥位置。
180度轴线：记录对话人物连线及相机侧；越轴时使用建立镜头、移动镜头或明确风格意图。不要强制人物永远处于画面固定左右。
接触点检查：手与门把/手机/桌面、脚与地面、臀部与椅面；模型提示词应写明接触起止状态。脚本只能检查坐标与状态字段，不能证明图像中没有悬浮。
多人镜头逐角色绑定character_id，镜头屏幕位置不能取代角色ID。
