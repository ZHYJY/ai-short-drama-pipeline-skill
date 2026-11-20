#!/usr/bin/env python3
"""Gate on documented visual review; never infer identity from image pixels."""
import json,sys
WEIGHTS={"face_geometry":25,"eyes_brows":15,"nose_mouth":15,"hairline":10,"body_proportion":10,"outfit":10,"distinctive_marks":10,"cross_shot_state":5}
P0={"face_geometry","eyes_brows","nose_mouth","distinctive_marks","body_proportion"}
def gate(r):
    if not r.get("has_visual_access") or r.get("review_status")!="completed":
        return {"decision":"needs_review","reason":"No completed review with real image access"}
    dims={d.get("dimension"):d for d in r.get("dimensions",[])}
    visible=[]
    for k,w in WEIGHTS.items():
        d=dims.get(k)
        if d and d.get("visible") and d.get("score") in (0,1,2) and str(d.get("evidence","")).strip():
            visible.append((k,w,d["score"]))
        elif d and d.get("visible"):
            return {"decision":"needs_review","reason":f"Missing valid score or evidence: {k}"}
    core=sum(1 for k in ("face_geometry","eyes_brows","nose_mouth") if any(x[0]==k for x in visible))
    if core<2:return {"decision":"needs_review","reason":"Insufficient visible core facial dimensions"}
    if r.get("blockers"):return {"decision":"reject","reason":"Explicit blocking issues","blockers":r["blockers"]}
    for k,w,s in visible:
        if k in P0 and s<2:return {"decision":"reject","reason":f"P0 identity dimension failed: {k}"}
    total=sum(w for _,w,_ in visible)
    avg=sum(w*s for _,w,s in visible)/total
    return {"decision":"pass" if avg>=1.7 else "reject","weighted_score_out_of_2":round(avg,3),"reason":"Reviewed dimensions and evidence only; not biometric proof"}
if __name__=="__main__":
    if len(sys.argv)!=2:sys.exit("usage: review_gate.py review.json")
    with open(sys.argv[1],encoding="utf-8") as fp:r=json.load(fp)
    print(json.dumps(gate(r),ensure_ascii=False,indent=2))
