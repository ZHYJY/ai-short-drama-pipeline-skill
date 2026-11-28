#!/usr/bin/env python3
"""从独立工作台生成四个Agent宿主可使用的任务交接包；不调用任何外部API。"""
import argparse,json,sys
from pathlib import Path
from datetime import datetime,timezone
from model_router import read,within,sha
HOSTS={"doubao-work","codex","trae","workbuddy"}
HOST_GUIDE={
 "doubao-work":"按角色圣经、镜头顺序生成素材；当前会话无真实媒体工具时输出生成提示词。将真实媒体交回独立工作台。",
 "codex":"检查工作区权限和依赖后执行可用脚本；使用真实工具生成、检查和记录结果，不能虚构审核通过。",
 "trae":"在当前可信项目工作区维护镜头、角色和任务数据；通过IDE终端运行工作台脚本，真实媒体必须存盘。",
 "workbuddy":"将任务分派给负责人，记录交付清单、素材模型、复核证据和待办；无本地权限时输出交接材料。"}
def export(root,host,job_id):
    if host not in HOSTS:raise ValueError("不支持的宿主")
    jobs=read(root,"jobs.json",[])
    job=next((x for x in jobs if x.get("id")==job_id),None)
    if not job:raise ValueError("任务ID不存在")
    assets=read(root,"assets.json",[])
    refs=[]
    for aid in job.get("source_asset_ids") or []:
        a=next((x for x in assets if x.get("id")==aid),None)
        if not a:raise ValueError("来源素材ID不存在: "+str(aid))
        p=within(root,a.get("path",""))
        refs.append({"asset_id":aid,"path":a.get("path"),"sha256":sha(p) if p.is_file() else None})
    shot=next((x for x in read(root,"shots.json",[]) if x.get("id")==job.get("shot_id")),None)
    packet={"schema":"drama-agent-handoff","target_host":host,"exported_at":datetime.now(timezone.utc).isoformat(),
            "project":read(root,"project.json",{}),"shot":shot,"job":job,"source_assets":refs,
            "instruction":HOST_GUIDE[host],
            "quality_gates":["real-media-check","identity-review-with-evidence","audio-review-with-evidence","final-independent-review"],
            "status":"handoff_only_not_executed"}
    dest=root/"handoffs"/host;dest.mkdir(parents=True,exist_ok=True)
    jsonfile=dest/(job_id+".json")
    jsonfile.write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding="utf-8")
    promptfile=dest/(job_id+".md")
    promptfile.write_text(f"# 短剧生成任务 {job_id}\n\n宿主：{host}\n\n{HOST_GUIDE[host]}\n\n## 任务提示词\n{job['prompt']}\n\n## 角色与素材引用\n"+ "\n".join(f"- {x['asset_id']}: {x['path']} (sha256: {x['sha256']})" for x in refs)+"\n\n## 强制质量要求\n生成后记录真实模型名称、平台和参数，保存文件；没有视觉/音频证据不得通过审核。\n",encoding="utf-8")
    return jsonfile,promptfile
def main():
    p=argparse.ArgumentParser()
    p.add_argument("project_dir");p.add_argument("host",choices=sorted(HOSTS));p.add_argument("job_id")
    a=p.parse_args()
    for x in export(Path(a.project_dir).resolve(),a.host,a.job_id):print(x)
if __name__=="__main__":main()
