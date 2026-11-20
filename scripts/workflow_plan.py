#!/usr/bin/env python3
"""Dependency planner only: no generation, API access, or fabricated outputs."""
import json,sys
def plan(w):
    tasks=w.get("tasks",[]);d={t.get("task_id"):t for t in tasks}
    issues=[]
    if len(d)!=len(tasks) or None in d:issues.append("duplicate or missing task IDs")
    for t in tasks:
        for dep in t.get("depends_on",[]):
            if dep not in d:issues.append(f"{t.get('task_id')}: unknown dependency {dep}")
    visiting=set();visited=set()
    def visit(n):
        if n in visiting:issues.append(f"cycle detected at {n}");return
        if n in visited:return
        visiting.add(n)
        for dep in d[n].get("depends_on",[]):
            if dep in d:visit(dep)
        visiting.remove(n);visited.add(n)
    for n in d:visit(n)
    ready=[];blocked=[];completed=[]
    if not issues:
        for t in tasks:
            name=t["task_id"];status=t.get("status")
            if status=="completed":
                if not t.get("output_asset_ids"):issues.append(f"{name}: completed without output assets")
                completed.append(name);continue
            if status in ("failed","running"):continue
            pending=[dep for dep in t.get("depends_on",[]) if d[dep].get("status")!="completed" or d[dep].get("gate")!="approved"]
            if pending:blocked.append({"task_id":name,"blocked_by":pending})
            else:ready.append(name)
    return {"valid":not issues,"issues":issues,"ready":ready,"blocked":blocked,"completed":completed,"note":"No tasks were executed"}
if __name__=="__main__":
    if len(sys.argv)!=2:sys.exit("usage: workflow_plan.py workflow.json")
    with open(sys.argv[1],encoding="utf-8") as fp:w=json.load(fp)
    r=plan(w);print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r["valid"] else 1)
