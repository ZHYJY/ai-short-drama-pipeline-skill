#!/usr/bin/env python3
"""Local deterministic planning helper. No external network or platform calls."""
import json, sys
def supported(cap, key):
    obj=cap.get("capabilities",{}).get(key,{})
    return obj.get("status") in ("verified","documented") and obj.get("value") is not None
def plan(cap, preferences):
    caps=cap.get("capabilities",{})
    def val(k): return caps.get(k,{}).get("value")
    checks=[]
    preferred=float(preferences.get("segment_seconds",15))
    durations=val("durations_seconds") if supported(cap,"durations_seconds") else []
    durations=sorted({float(x) for x in durations if isinstance(x,(int,float)) and x>0})
    if durations:
        duration=min(durations,key=lambda x:(abs(x-preferred),-x))
    else:
        duration=None
        checks.append("验证平台支持的生成时长档位")
    multishot=bool(preferences.get("prefer_multishot")) and supported(cap,"multi_shot") and val("multi_shot") is True
    if not supported(cap,"multi_shot"): checks.append("验证模型是否支持单次生成内部多镜")
    if not supported(cap,"max_reference_images"): checks.append("验证最大参考图数量")
    if not supported(cap,"native_dialogue"): checks.append("验证是否原生支持对白")
    ref=val("max_reference_images") if supported(cap,"max_reference_images") else None
    ref_strategy=("needs_validation" if ref is None else "text_only" if ref==0 else "first_frame_first" if ref==1 else "prioritized_references")
    gen=any(supported(cap,k) and val(k) is True for k in ("video_generation_tool",))
    return {
      "platform":cap.get("platform","generic"),
      "preferred_segment_seconds":preferred,
      "generation_segment_seconds":duration,
      "shot_strategy":"multi_shot" if multishot else "per_shot",
      "audio_strategy":"native_dialogue" if supported(cap,"native_dialogue") and val("native_dialogue") is True else "post_production",
      "reference_strategy":ref_strategy,
      "execution_mode":"tool_assisted" if gen else "package_only",
      "unresolved_checks":checks,
      "note":"tool_assisted仅代表配置声明可用，执行前仍须确认真实工具权限。"
    }
if __name__=="__main__":
    if len(sys.argv)!=3:
        print("Usage: python adapt.py capability.json preferences.json");sys.exit(2)
    with open(sys.argv[1],encoding="utf-8") as f: cap=json.load(f)
    with open(sys.argv[2],encoding="utf-8") as f: prefs=json.load(f)
    print(json.dumps(plan(cap,prefs),ensure_ascii=False,indent=2))
