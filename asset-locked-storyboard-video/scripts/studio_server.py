#!/usr/bin/env python3
"""本地独立控制中心：复用原有工作台并增加模型路由接口。"""
import argparse, json, threading, webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
from production_center import Handler,init,state,read,checks,gate
from model_router import profiles,configure,submit,handoff,import_result,run_text,init as init_router
from platform_handoff import export as host_export

class StudioHandler(Handler):
    def do_GET(self):
        if urlparse(self.path).path=="/api/models":
            self.send_json({"profiles":profiles(self.root),"jobs":read(self.root,"jobs.json",[])});return
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in {"/api/model-config","/api/model-submit","/api/model-handoff","/api/model-import","/api/model-run-text","/api/host-handoff"}:
            return super().do_POST()
        try:
            origin=self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"}:
                raise ValueError("拒绝跨站写入请求")
            n=int(self.headers.get("Content-Length","0"))
            if n<0 or n>1024*1024:raise ValueError("请求体过大")
            body=json.loads(self.rfile.read(n)) if n else {}
            with self.lock:
                if path=="/api/model-config":result=configure(self.root,body)
                elif path=="/api/model-submit":result=submit(self.root,body)
                elif path=="/api/model-handoff":result=handoff(self.root,body["job_id"])
                elif path=="/api/model-import":result=import_result(self.root,body["job_id"],body["path"],body["asset_id"],body.get("notes",""))
                elif path=="/api/host-handoff":
                    files=host_export(self.root,body["host"],body["job_id"])
                    result={"files":[str(x.relative_to(self.root)) for x in files],"status":"handoff_only_not_executed"}
                else:result=run_text(self.root,body["job_id"])
            self.send_json(result)
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self.send_json({"error":str(e)},400)
        except Exception as e:self.send_json({"error":"服务端错误："+type(e).__name__},500)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",default="projects/我的短剧")
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--no-browser",action="store_true")
    args=p.parse_args()
    root=Path(args.project).expanduser().resolve()
    init(root);init_router(root)
    StudioHandler.root=root
    srv=ThreadingHTTPServer(("127.0.0.1",args.port),StudioHandler)
    url=f"http://127.0.0.1:{srv.server_port}"
    print("短剧生产控制中心："+url,flush=True)
    print("项目目录："+str(root),flush=True)
    print("仅限本机访问；按 Ctrl+C 关闭。",flush=True)
    if not args.no_browser:threading.Timer(0.8,lambda:webbrowser.open(url)).start()
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()
if __name__=="__main__":main()
