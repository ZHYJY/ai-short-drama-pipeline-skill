#!/usr/bin/env python3
"""Offline asset technical audit; does not recognize or match faces."""
import argparse,json,hashlib,math,os
from pathlib import Path
from PIL import Image,ImageStat,ImageFilter
def audit(manifest_path,root):
    m=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    assets=[];views=set()
    for a in m.get("assets",[]):
        p=(Path(root)/a.get("file_path","")).resolve()
        rec={"asset_id":a.get("asset_id"),"view":a.get("view"),"approval":a.get("approval"),"exists":p.is_file()}
        if p.is_file():
            try:
                data=p.read_bytes();rec["sha256"]=hashlib.sha256(data).hexdigest()
                with Image.open(p) as im:
                    im.verify()
                with Image.open(p) as im:
                    im=im.convert("RGB")
                    w,h=im.size;rec["width"]=w;rec["height"]=h;rec["aspect_ratio"]=round(w/h,4)
                    im.thumbnail((512,512))
                    gray=im.convert("L")
                    mean=ImageStat.Stat(gray).mean[0]
                    # heuristic edge contrast, not an identity metric
                    edges=gray.filter(ImageFilter.FIND_EDGES)
                    edge_std=ImageStat.Stat(edges).stddev[0]
                    rec["mean_luminance"]=round(mean,2)
                    rec["edge_std_heuristic"]=round(edge_std,2)
                    rec["warnings"]=[]
                    if min(w,h)<512:rec["warnings"].append("low_resolution")
                    if mean<35 or mean>225:rec["warnings"].append("extreme_exposure")
                    if edge_std<12:rec["warnings"].append("low_edge_detail_review")
                if a.get("approval")=="approved":views.add(a.get("view"))
            except Exception as e:rec["error"]=str(e)
        assets.append(rec)
    required=m.get("required_views",[])
    return {"assets":assets,"required_views":required,"approved_view_coverage":sorted(views),"missing_approved_views":[v for v in required if v not in views],"identity_verification":"not_performed","note":"Image metrics are technical heuristics only; identity requires visual review."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--root",default=".")
    a=p.parse_args()
    print(json.dumps(audit(a.manifest,a.root),ensure_ascii=False,indent=2))
