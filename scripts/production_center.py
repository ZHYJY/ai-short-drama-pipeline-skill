#!/usr/bin/env python3
"""短剧本地生产控制中心：标准库 + 可选 ffprobe。"""
import argparse, hashlib, json, mimetypes, os, shutil, subprocess, sys, threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote

def now(): return datetime.now(timezone.utc).isoformat()
def read(root,name,default): 
    p=root/name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def save(root,name,data):
    p=root/name; tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(p)
def within(root,rel):
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts: raise ValueError("无效相对路径")
    p=(root/rel).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError("路径越界")
    return p
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def probe(path):
    if not shutil.which("ffprobe"): return {"status":"unverified","reason":"未安装ffprobe"}
    try:
        proc=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)],capture_output=True,text=True,timeout=25)
        if proc.returncode: return {"status":"failed","reason":proc.stderr[:250]}
        info=json.loads(proc.stdout)
        return {"status":"pass","duration":info.get("format",{}).get("duration"),"streams":[{"codec_type":s.get("codec_type"),"width":s.get("width"),"height":s.get("height"),"r_frame_rate":s.get("r_frame_rate")} for s in info.get("streams",[])]}
    except (OSError,ValueError,subprocess.TimeoutExpired) as e: return {"status":"unverified","reason":str(e)}
def state(root):
    return {k:read(root,k,default) for k,default in [
        ("project.json",{"title":"未命名项目","target_duration_seconds":15}),
        ("shots.json",[]),("assets.json",[]),("reviews.json",[]),("tasks.json",[]), ("visual-review-queue.json",[])]}
def checks(root):
    data=state(root); shots=data["shots.json"]; assets=data["assets.json"]
    errors=[]; warnings=[]; detail={}
    sid={s.get("id") for s in shots}; aid=[a.get("id") for a in assets]
    if len(aid)!=len(set(aid)): errors.append("重复素材ID")
    if len(sid)!=len(shots): errors.append("重复镜头ID")
    for a in assets:
        id=a.get("id","?")
        if a.get("shot_id") and a["shot_id"] not in sid: errors.append(f"{id}: 未知镜头")
        for x in (a.get("sources") or []):
            if x not in aid: errors.append(f"{id}: 未知来源 {x}")
        if not a.get("path"):
            detail[id]={"status":"unverified","reason":"无实际文件"};continue
        try:
            p=within(root,a["path"])
            if not p.is_file(): errors.append(f"{id}: 文件不存在");detail[id]={"status":"failed"};continue
            d={"status":"pass","bytes":p.stat().st_size,"sha256":sha(p)}
            if p.stat().st_size==0: errors.append(f"{id}: 空文件");d["status"]="failed"
            if p.suffix.lower() in {".mp4",".mov",".webm",".mkv",".mp3",".wav",".ogg"}:
                d["media"]=probe(p)
                if d["media"]["status"]=="failed": errors.append(f"{id}: 媒体无法解码")
                elif d["media"]["status"]=="unverified": warnings.append(f"{id}: 媒体元数据未验证")
            detail[id]=d
        except ValueError as e: errors.append(f"{id}: {e}");detail[id]={"status":"failed"}
    ordered=sorted(shots,key=lambda s:(s.get("order",999999),s.get("start",0)))
    for a,b in zip(ordered,ordered[1:]):
        if a.get("end",0)>b.get("start",0): errors.append(f"{a.get('id')}/{b.get('id')}: 时间重叠")
        if a.get("end",0)<b.get("start",0): errors.append(f"{a.get('id')}/{b.get('id')}: 时间缺口")
    if ordered and ordered[0].get("start")!=0: errors.append("时间轴未从0开始")
    target=data["project.json"].get("target_duration_seconds")
    if ordered and target is not None and abs(ordered[-1].get("end",0)-target)>0.05: errors.append("镜头时间轴未覆盖目标时长")
    result={"timestamp":now(),"status":"failed" if errors else ("unverified" if warnings else "pass"),"errors":errors,"warnings":warnings,"assets":detail}
    save(root,"technical-check.json",result)
    return result
def valid_review(r,scope,target,hash_value):
    return r.get("scope")==scope and r.get("target_id")==target and r.get("result")=="pass" and bool(r.get("evidence")) and r.get("asset_sha256")==hash_value and r.get("reviewer") and r.get("checked_at")
def gate(root,stage):
    data=state(root); technical=checks(root); assets=data["assets.json"]; reviews=data["reviews.json"]
    reasons=list(technical["errors"])
    if technical["warnings"]: reasons.extend(technical["warnings"])
    selected=[a for a in assets if a.get("selected")]
    tasks=data["tasks.json"]
    for t in tasks:
        if t.get("type")=="review_fix" and t.get("status")!="completed" and t.get("severity") in ("high","critical"):
            if any(a.get("id")==t.get("asset_id") for a in selected):
                reasons.append(f"{t.get('id')}: 存在未解决的高风险返工问题")
    if stage=="preflight":
        for s in data["shots.json"]:
            chosen=[a for a in selected if a.get("shot_id")==s.get("id") and a.get("kind")=="video"]
            if len(chosen)!=1: reasons.append(f"{s.get('id')}: 必须且只能选择一个正式镜头视频")
        required=("identity","visual","continuity","audio")
    else:
        chosen=[a for a in assets if a.get("kind")=="final_video" and a.get("selected")]
        if len(chosen)!=1: reasons.append("必须且只能选择一个最终成片")
        required=("final_visual","final_audio","final_continuity","final_narrative")
        # 任何成片复核都以通过前置门禁为基础
        prev=read(root,"preflight-gate.json",{})
        if prev.get("status")!="pass": reasons.append("尚无通过的素材前置门禁")
        else:
            snapshot=prev.get("selected_sha256",{})
            current={a["id"]:technical["assets"].get(a["id"],{}).get("sha256") for a in assets if a.get("selected") and a.get("kind")=="video"}
            if snapshot!=current: reasons.append("前置门禁后镜头素材已变更，需重新审核")
    for a in chosen if stage=="final" else [a for a in selected if a.get("kind")=="video"]:
        id=a.get("id");d=technical["assets"].get(id,{})
        h=d.get("sha256")
        if d.get("status")!="pass" or d.get("media",{}).get("status")!="pass":
            reasons.append(f"{id}: 媒体技术检查未通过或无法验证")
        for scope in required:
            if not any(valid_review(r,scope,id,h) for r in reviews):
                reasons.append(f"{id}: 缺少有效 {scope} 复核证据")
    status="blocked" if reasons else "pass"
    result={"status":status,"timestamp":now(),"reasons":reasons}
    if stage=="preflight":
        result["selected_sha256"]={a["id"]:technical["assets"].get(a["id"],{}).get("sha256") for a in selected if a.get("kind")=="video"}
    save(root,f"{stage}-gate.json",result)
    return result
def init(root):
    root.mkdir(parents=True,exist_ok=True)
    defaults={
      "project.json":{"project_id":"DEMO","title":"示例短剧项目","target_duration_seconds":15,"aspect_ratio":"9:16"},
      "shots.json":[{"id":"SH01","order":1,"start":0,"end":7,"description":"镜头一"},{"id":"SH02","order":2,"start":7,"end":15,"description":"镜头二"}],
      "assets.json":[],"reviews.json":[],"tasks.json":[]}
    for name,content in defaults.items():
        if not (root/name).exists():save(root,name,content)
def change(root,action,body):
    if action=="task":
        tasks=read(root,"tasks.json",[])
        tid=body.get("id")
        if not tid or any(t.get("id")==tid for t in tasks): raise ValueError("任务ID缺失或重复")
        tasks.append({"id":tid,"shot_id":body.get("shot_id"),"type":body.get("type","regenerate"),"status":"planned","notes":body.get("notes",""),"created_at":now()})
        save(root,"tasks.json",tasks);return {"created":tid}
    if action=="asset":
        assets=read(root,"assets.json",[])
        if not body.get("id") or any(a.get("id")==body["id"] for a in assets): raise ValueError("素材ID缺失或重复")
        if body.get("path"):within(root,body["path"])
        if body.get("shot_id") and body["shot_id"] not in {s["id"] for s in read(root,"shots.json",[])}:raise ValueError("未知镜头")
        a={k:body.get(k) for k in ("id","shot_id","kind","path","model","platform","prompt","parameters","sources","attempt","notes")}
        a["sources"]=a.get("sources") or []
        a["parameters"]=a.get("parameters") or {}
        a["selected"]=False;a["created_at"]=now()
        assets.append(a);save(root,"assets.json",assets);return {"created":a["id"]}
    if action=="select":
        assets=read(root,"assets.json",[])
        found=next((a for a in assets if a.get("id")==body.get("id")),None)
        if not found:raise ValueError("未知素材")
        for a in assets:
            if a.get("kind")==found.get("kind") and a.get("shot_id")==found.get("shot_id"):
                a["selected"]=a["id"]==found["id"]
        save(root,"assets.json",assets);return {"selected":found["id"]}
    if action=="review":
        assets=read(root,"assets.json",[])
        a=next((x for x in assets if x.get("id")==body.get("target_id")),None)
        if not a or not a.get("path"):raise ValueError("必须选择真实素材")
        p=within(root,a["path"])
        if not p.is_file():raise ValueError("文件不存在")
        if body.get("scope") not in {"identity","visual","continuity","audio","final_visual","final_audio","final_continuity","final_narrative"}:raise ValueError("审核类型不支持")
        if body.get("result") not in {"pass","fail","unverified"}:raise ValueError("审核结论不支持")
        if not body.get("reviewer") or not body.get("evidence"):raise ValueError("必须填写审核人和真实审核证据")
        reviews=read(root,"reviews.json",[])
        reviews.append({"scope":body["scope"],"target_id":a["id"],"result":body["result"],"reviewer":body["reviewer"],"evidence":body["evidence"],"asset_sha256":sha(p),"checked_at":now()})
        save(root,"reviews.json",reviews);return {"reviewed":a["id"]}
    raise ValueError("不支持的操作")
class Handler(BaseHTTPRequestHandler):
    root=None
    lock=threading.Lock()
    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)))
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":
            data=(Path(__file__).parent.parent/"control-center"/"index.html").read_bytes()
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
        if path=="/api/state":
            self.send_json({**state(self.root),"technical":read(self.root,"technical-check.json",{}),"preflight":read(self.root,"preflight-gate.json",{}),"final":read(self.root,"final-gate.json",{})});return
        if path.startswith("/review-frame/"):
            parts=[unquote(x) for x in path.split("/")[2:]]
            if len(parts)!=3 or any(not x or x in (".","..") or "/" in x or "\\" in x for x in parts):
                self.send_error(400);return
            reports=read(self.root,"visual-review-queue.json",[])
            report=next((r for r in reports if r.get("asset_id")==parts[0] and r.get("asset_sha256","")[:12]==parts[1]),None)
            if not report:self.send_error(404);return
            entry=next((f for f in report.get("frames",[]) if Path(f.get("path","")).name==parts[2]),None)
            if not entry:self.send_error(404);return
            try:frame=within(self.root,entry["path"])
            except ValueError:self.send_error(403);return
            if not frame.is_file():self.send_error(404);return
            self.send_response(200);self.send_header("Content-Type","image/png");self.send_header("Content-Length",str(frame.stat().st_size));self.end_headers()
            with frame.open("rb") as f:shutil.copyfileobj(f,self.wfile)
            return
        if path.startswith("/media/"):
            aid=unquote(path[7:])
            a=next((a for a in read(self.root,"assets.json",[]) if a.get("id")==aid),None)
            if not a or not a.get("path"):self.send_error(404);return
            try:p=within(self.root,a["path"])
            except ValueError:self.send_error(403);return
            if not p.is_file():self.send_error(404);return
            # Simple local preview; range requests are not implemented.
            self.send_response(200);self.send_header("Content-Type",mimetypes.guess_type(str(p))[0] or "application/octet-stream")
            self.send_header("Content-Length",str(p.stat().st_size));self.end_headers()
            with p.open("rb") as f:shutil.copyfileobj(f,self.wfile)
            return
        self.send_error(404)
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in {"/api/check","/api/preflight","/api/final","/api/task","/api/asset","/api/select","/api/review","/api/analyze","/api/issue"}:self.send_error(404);return
        try:
            origin=self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"}:
                raise ValueError("拒绝跨站写入请求")
            n=int(self.headers.get("Content-Length","0"))
            if n>1024*1024:raise ValueError("请求体过大")
            body=json.loads(self.rfile.read(n)) if n else {}
            with self.lock:
                if path=="/api/analyze":
                    from visual_review_pipeline import audit
                    out=audit(self.root,body.get("asset_id"),int(body.get("count",7)))
                elif path=="/api/issue":
                    from visual_review_pipeline import issue
                    out=issue(self.root,body.get("asset_id"),body.get("category","visual"),body.get("description",""),body.get("severity","high"))
                elif path=="/api/check":out=checks(self.root)
                elif path=="/api/preflight":out=gate(self.root,"preflight")
                elif path=="/api/final":out=gate(self.root,"final")
                else:out=change(self.root,path.split("/")[-1],body)
            self.send_json(out)
        except (ValueError,KeyError,TypeError,JSONDecodeError) as e:self.send_json({"error":str(e)},400)
        except Exception as e:self.send_json({"error":f"操作失败：{type(e).__name__}"},500)
JSONDecodeError=json.JSONDecodeError
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["init","check","preflight","final","serve"])
    parser.add_argument("project_dir");parser.add_argument("--port",type=int,default=8765)
    args=parser.parse_args();root=Path(args.project_dir).resolve()
    if args.command=="init":init(root);print(root);return
    if not root.is_dir():parser.error("项目目录不存在，请先init")
    if args.command=="serve":
        Handler.root=root
        server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
        print(f"控制中心 http://127.0.0.1:{args.port}",flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
    else:
        result=checks(root) if args.command=="check" else gate(root,args.command)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result["status"] not in ("pass",):sys.exit(1)
if __name__=="__main__":main()
