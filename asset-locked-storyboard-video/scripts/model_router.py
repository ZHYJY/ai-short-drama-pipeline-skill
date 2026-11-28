#!/usr/bin/env python3
"""跨平台模型路由与任务交接：仅标准库。兼容文本API需用户自行授权。"""
import argparse, json, os, re, subprocess, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from production_center import read,save,within,sha,change

KINDS={"manual","openai_compatible_text"}
DEFAULT_PROFILES=[
 {"id":"manual-image","label":"通用图片平台（手动）","provider":"manual","capabilities":["image"],"enabled":True},
 {"id":"manual-video","label":"通用视频平台（手动）","provider":"manual","capabilities":["video"],"enabled":True},
 {"id":"manual-audio","label":"通用配音平台（手动）","provider":"manual","capabilities":["audio"],"enabled":True},
 {"id":"text-api","label":"兼容接口的文本模型（需配置）","provider":"openai_compatible_text","capabilities":["text"],"enabled":False,"model":"","endpoint":"","api_key_env":"DRAMA_TEXT_API_KEY"}]
def utc():return datetime.now(timezone.utc).isoformat()
def profiles(root):
    p=read(root,"model-profiles.json",DEFAULT_PROFILES)
    if not isinstance(p,list):raise ValueError("模型配置应为列表")
    return p
def init(root):
    if not (root/"model-profiles.json").exists():save(root,"model-profiles.json",DEFAULT_PROFILES)
    if not (root/"jobs.json").exists():save(root,"jobs.json",[])
def configure(root,profile):
    init(root)
    if profile.get("provider") not in KINDS:raise ValueError("不支持的适配器")
    pid=profile.get("id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",pid):raise ValueError("配置ID非法")
    if not isinstance(profile.get("capabilities"),list) or not set(profile["capabilities"]) <= {"text","image","video","audio"}:raise ValueError("能力非法")
    if profile["provider"]=="openai_compatible_text":
        if profile["capabilities"]!=["text"]:raise ValueError("兼容接口只支持文本任务")
        endpoint=profile.get("endpoint","")
        u=urllib.parse.urlsplit(endpoint)
        if u.scheme!="https" or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("接口必须为不带凭证、查询参数的HTTPS URL")
        if not profile.get("api_key_env","").startswith("DRAMA_"):raise ValueError("密钥环境变量需以DRAMA_开头")
        if not profile.get("model"):raise ValueError("缺少模型ID")
    for key in profile:
        if "secret" in key.lower() or key.lower() in {"api_key","token","password"}:raise ValueError("禁止将密钥存入配置")
    p=profiles(root);p=[x for x in p if x.get("id")!=pid]+[profile];save(root,"model-profiles.json",p)
    return {"saved":pid}
def submit(root,body):
    init(root)
    prof=next((p for p in profiles(root) if p.get("id")==body.get("profile_id")),None)
    if not prof or not prof.get("enabled"):raise ValueError("模型配置不存在或未启用")
    kind=body.get("kind")
    if kind not in prof.get("capabilities",[]):raise ValueError("该配置不支持此任务类型")
    shots=read(root,"shots.json",[])
    if body.get("shot_id") and body["shot_id"] not in {s["id"] for s in shots}:raise ValueError("镜头ID不存在")
    if not str(body.get("prompt","")).strip():raise ValueError("缺少任务提示词")
    jobs=read(root,"jobs.json",[])
    number=1;ids={j["id"] for j in jobs}
    while f"JOB-{number:05d}" in ids:number+=1
    job={"id":f"JOB-{number:05d}","profile_id":prof["id"],"provider":prof["provider"],
         "model":prof.get("model") or prof.get("label"),"platform":prof.get("label"),
         "kind":kind,"shot_id":body.get("shot_id"),"prompt":str(body["prompt"]),
         "parameters":body.get("parameters") or {},"status":"queued","created_at":utc(),
         "source_asset_ids":body.get("source_asset_ids") or [],"result_asset_id":None}
    if not isinstance(job["parameters"],dict):raise ValueError("参数必须是对象")
    assets=read(root,"assets.json",[])
    for x in job["source_asset_ids"]:
        if x not in {a["id"] for a in assets}:raise ValueError("未知引用素材 "+str(x))
    jobs.append(job);save(root,"jobs.json",jobs)
    return job
def handoff(root,job_id):
    jobs=read(root,"jobs.json",[])
    job=next((j for j in jobs if j["id"]==job_id),None)
    if not job:raise ValueError("任务不存在")
    out=root/"handoffs";out.mkdir(exist_ok=True)
    references=[]
    for a in read(root,"assets.json",[]):
        if a["id"] in job.get("source_asset_ids",[]):
            p=within(root,a.get("path"))
            references.append({"id":a["id"],"path":a.get("path"),"sha256":sha(p) if p.is_file() else None})
    package={**job,"reference_assets":references,"instructions":"在对应平台完成生成，将结果文件保存到项目目录，再在工作台导入。不得将未生成任务标为完成。"}
    dest=out/f"{job_id}.json";dest.write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding="utf-8")
    job["status"]="awaiting_external_generation";save(root,"jobs.json",jobs)
    return {"path":str(dest.relative_to(root)),"job":package}
def import_result(root,job_id,path,asset_id,notes=""):
    jobs=read(root,"jobs.json",[])
    job=next((j for j in jobs if j["id"]==job_id),None)
    if not job:raise ValueError("任务不存在")
    if job["status"]=="completed":raise ValueError("任务已完成")
    p=within(root,path)
    if not p.is_file() or p.stat().st_size==0:raise ValueError("真实结果文件不存在或为空")
    if job["kind"]=="video" and p.suffix.lower() not in {".mp4",".mov",".mkv",".webm"}:raise ValueError("视频文件格式不符")
    if job["kind"]=="image" and p.suffix.lower() not in {".png",".jpg",".jpeg",".webp"}:raise ValueError("图片文件格式不符")
    if job["kind"]=="audio" and p.suffix.lower() not in {".wav",".mp3",".ogg",".m4a"}:raise ValueError("音频文件格式不符")
    kind={"text":"text","image":"image","video":"video","audio":"audio"}[job["kind"]]
    if job["kind"]=="text" and p.suffix.lower() not in {".txt",".md",".json"}:raise ValueError("文本文件格式不符")
    data={"id":asset_id,"shot_id":job.get("shot_id"),"kind":kind,"path":path,
          "model":job["model"],"platform":job["platform"],"prompt":job["prompt"],
          "parameters":job["parameters"],"sources":job["source_asset_ids"],"notes":notes,
          "job_id":job_id,"file_sha256":sha(p)}
    result=change(root,"asset",data)
    assets=read(root,"assets.json",[])
    for a in assets:
        if a["id"]==asset_id:
            a["job_id"]=job_id;a["file_sha256"]=sha(p)
    save(root,"assets.json",assets)
    job["status"]="completed";job["result_asset_id"]=asset_id;job["completed_at"]=utc()
    save(root,"jobs.json",jobs)
    return result
def run_text(root,job_id):
    jobs=read(root,"jobs.json",[])
    job=next((j for j in jobs if j["id"]==job_id),None)
    if not job:raise ValueError("任务不存在")
    prof=next((p for p in profiles(root) if p["id"]==job["profile_id"]),None)
    if not prof or prof["provider"]!="openai_compatible_text" or job["kind"]!="text":raise ValueError("此任务不能自动调用")
    if job["status"]=="completed":raise ValueError("任务已完成")
    key=os.environ.get(prof["api_key_env"])
    if not key:raise ValueError("未设置密钥环境变量 "+prof["api_key_env"])
    endpoint=prof["endpoint"]
    # No redirects; avoid inadvertently sending API keys to a different host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(NoRedirect())
    body=json.dumps({"model":prof["model"],"messages":[{"role":"user","content":job["prompt"]}],"stream":False}).encode()
    req=urllib.request.Request(endpoint,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with opener.open(req,timeout=60) as response:
            if response.status!=200:raise ValueError("接口返回非成功状态")
            raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError("响应过大")
            result=json.loads(raw)
        content=result["choices"][0]["message"]["content"]
        if not isinstance(content,str) or not content:raise ValueError("接口未返回有效文本")
    except (urllib.error.URLError,KeyError,IndexError,ValueError) as e:
        raise ValueError("文本模型调用失败："+str(e)) from e
    out=root/"generated_text";out.mkdir(exist_ok=True)
    dest=out/(job_id+".txt");dest.write_text(content,encoding="utf-8")
    return import_result(root,job_id,str(dest.relative_to(root)),job_id+"-TEXT")
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["init","profiles","configure","submit","handoff","import","run-text","jobs"])
    parser.add_argument("project_dir");parser.add_argument("arg",nargs="?")
    parser.add_argument("--file");parser.add_argument("--path");parser.add_argument("--asset-id")
    a=parser.parse_args();root=Path(a.project_dir).resolve()
    if a.command=="init":root.mkdir(parents=True,exist_ok=True);init(root);result={"initialized":str(root)}
    elif a.command=="profiles":result=profiles(root)
    elif a.command=="jobs":result=read(root,"jobs.json",[])
    elif a.command=="configure":result=configure(root,json.loads(Path(a.file).read_text(encoding="utf-8")))
    elif a.command=="submit":result=submit(root,json.loads(Path(a.file).read_text(encoding="utf-8")))
    elif a.command=="handoff":result=handoff(root,a.arg)
    elif a.command=="import":result=import_result(root,a.arg,a.path,a.asset_id)
    else:result=run_text(root,a.arg)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
