#!/usr/bin/env python3
"""Static checks only. Does not inspect images or certify facial identity."""
import json,sys
def validate(chars,shots):
    issues=[]; byid={}
    for c in chars:
        cid=c.get("character_id")
        if not cid or cid in byid: issues.append(f"duplicate/missing character_id: {cid}")
        byid[cid]=c
        lock=c.get("identity_lock",{})
        if len(lock.get("anchor_features",[]))<5: issues.append(f"{cid}: fewer than 5 confirmed identity anchors")
        if not lock.get("canonical_asset_ids"): issues.append(f"{cid}: no canonical reference assets (text-only lock)")
        if c.get("identity_status")!="approved":issues.append(f"{cid}: identity not approved")
    prev={}
    for s in shots:
        sid=s.get("shot_id","unknown")
        for b in s.get("characters",[]):
            cid=b.get("character_id")
            if cid not in byid:issues.append(f"{sid}: unknown character {cid}");continue
            c=byid[cid]
            if str(b.get("identity_version"))!=str(c.get("identity_version")):issues.append(f"{sid}: identity version mismatch for {cid}")
            outfit=(b.get("outfit_id"),str(b.get("outfit_version")))
            key=(cid,s.get("scene_id"))
            if key in prev:
                old=prev[key]
                if outfit!=old["outfit"] and not b.get("change_event_ids"):issues.append(f"{sid}: unrecorded outfit change {cid}")
                if old["exit"] and b.get("entry_state") and old["exit"]!=b["entry_state"] and not b.get("change_event_ids"):
                    issues.append(f"{sid}: state discontinuity for {cid}; inspect if intentional")
            prev[key]={"outfit":outfit,"exit":b.get("exit_state")}
    return issues
if __name__=="__main__":
    if len(sys.argv)!=3:sys.exit("usage: validate_characters.py characters.json shots.json")
    with open(sys.argv[1],encoding="utf-8") as fp:chars=json.load(fp)
    with open(sys.argv[2],encoding="utf-8") as fp:shots=json.load(fp)
    if isinstance(chars,dict):chars=[chars]
    if isinstance(shots,dict):shots=[shots]
    result=validate(chars,shots)
    print(json.dumps({"passed":not result,"issues":result,"note":"Static validation only; visual identity requires image/video review."},ensure_ascii=False,indent=2))
    sys.exit(1 if result else 0)
