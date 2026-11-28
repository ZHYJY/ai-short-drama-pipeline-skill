#!/usr/bin/env python3
"""Static director timeline, speaker, and movement continuity validation."""
import json,sys,math
def check(p):
    issues=[]
    ids={c.get("character_id") for c in p.get("characters",[])}
    scene_ids={p.get("scene",{}).get("scene_id")}
    total=0
    for seg in p.get("segments",[]):
        sid=seg.get("segment_id","?")
        shots=seg.get("shots",[])
        end=0.0;last={}
        for sh in shots:
            name=sh.get("shot_id","?")
            start=float(sh.get("start_seconds",0));stop=float(sh.get("end_seconds",0))
            if abs(start-end)>1e-6:issues.append(f"{name}: timeline gap/overlap at {end}")
            if stop<=start:issues.append(f"{name}: nonpositive duration")
            if sh.get("scene_id") not in scene_ids:issues.append(f"{name}: unknown scene")
            seen=set()
            for c in sh.get("characters",[]):
                cid=c.get("character_id")
                if cid not in ids:issues.append(f"{name}: unknown character {cid}")
                if cid in seen:issues.append(f"{name}: duplicate character {cid}")
                seen.add(cid)
                if cid in last:
                    old=last[cid]
                    if old["pos"]!=c.get("entry_position") and not sh.get("ellipsis"):
                        issues.append(f"{name}: position discontinuity {cid}")
                    if old["state"]!=c.get("entry_state") and not sh.get("ellipsis"):
                        issues.append(f"{name}: state discontinuity {cid}")
                last[cid]={"pos":c.get("exit_position"),"state":c.get("exit_state")}
            for line in sh.get("dialogue",[]):
                if line.get("speaker_id") not in seen:issues.append(f"{name}: speaker absent {line.get('speaker_id')}")
                a=float(line.get("start_seconds",0));b=float(line.get("end_seconds",0))
                if a<start or b>stop or b<=a:issues.append(f"{name}: dialogue out of bounds {line.get('line_id')}")
            end=stop
        if abs(end-float(seg.get("duration_seconds",0)))>1e-6:issues.append(f"{sid}: segment duration not covered")
        total+=float(seg.get("duration_seconds",0))
    if abs(total-float(p.get("target_duration_seconds",0)))>1e-6:issues.append("total project duration mismatch")
    return {"passed":not issues,"issues":issues,"note":"Static checks only; visual blocking and audio synchronization not verified"}
if __name__=="__main__":
    if len(sys.argv)!=2:sys.exit("usage: director_validate.py director-plan.json")
    with open(sys.argv[1],encoding="utf-8") as fp:p=json.load(fp)
    print(json.dumps(check(p),ensure_ascii=False,indent=2))
    sys.exit(0 if check(p)["passed"] else 1)
