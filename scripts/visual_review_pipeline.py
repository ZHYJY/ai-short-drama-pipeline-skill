#!/usr/bin/env python3
"""真实视频抽帧、待审核清单、异常返工任务。不会伪造视觉模型审核结论。"""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from datetime import datetime, timezone
from production_center import read,save,within,sha,probe

def audit(root, asset_id, count=7):
    if not 3 <= count <= 30: raise ValueError('抽帧数量必须在3至30之间')
    assets=read(root,'assets.json',[])
    a=next((x for x in assets if x.get('id')==asset_id),None)
    if not a: raise ValueError('未知素材ID')
    if a.get('kind') not in ('video','final_video'): raise ValueError('仅支持视频或成片')
    src=within(root,a.get('path'))
    if not src.is_file(): raise ValueError('视频文件不存在')
    meta=probe(src)
    if meta.get('status')!='pass': raise ValueError('无法验证视频流，请安装ffprobe并检查文件')
    if not any(s.get('codec_type')=='video' for s in meta['streams']): raise ValueError('没有视频轨道')
    if not shutil.which('ffmpeg'): raise ValueError('未安装ffmpeg，无法抽帧')
    duration=float(meta.get('duration') or 0)
    if duration<=0: raise ValueError('视频时长无效')
    h=sha(src); out=root/'review_frames'/''.join(c if c.isalnum() or c in '-_' else '_' for c in asset_id)/h[:12]
    out.mkdir(parents=True,exist_ok=True)
    frames=[]
    # 避开严格末尾边界，同时覆盖片头、片中、片尾
    for i in range(count):
        t=(min(duration*0.02,0.1) + (max(0.0,duration-min(0.25,duration*0.1))-min(duration*0.02,0.1))*i/(count-1))
        dst=out/f'frame_{i:02d}.png'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.4f}','-i',str(src),'-frames:v','1',str(dst)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
        if r.returncode or not dst.is_file() or dst.stat().st_size==0: raise RuntimeError('抽帧失败：'+r.stderr[-250:])
        frames.append({'time_seconds':round(t,3),'path':str(dst.relative_to(root)),'sha256':sha(dst)})
    shots=read(root,'shots.json',[])
    shot=next((s for s in shots if s.get('id')==a.get('shot_id')),None)
    character_ids=(shot or {}).get('character_ids',[])
    checklist=['角色面部及身体比例','发型服装和标志特征','人物与道具连续性','画面伪影和运动合理性','镜头首尾衔接','对白与口型同步','音频噪声与声线']
    if a.get('kind')=='final_video': checklist+=['成片镜头顺序','成片字幕和片尾','叙事节奏与故事完整性']
    report={'asset_id':asset_id,'asset_sha256':h,'created_at':datetime.now(timezone.utc).isoformat(),
        'status':'needs_visual_review','technical_metadata':meta,'frames':frames,
        'character_ids':character_ids,'checklist':[{'name':x,'status':'unverified'} for x in checklist],
        'note':'抽帧仅提供审核证据，不代表已验证身份、动作或口型。动态内容须实际查看连续视频。'}
    reports=read(root,'visual-review-queue.json',[])
    reports=[r for r in reports if not(r.get('asset_id')==asset_id and r.get('asset_sha256')==h)]+[report]
    save(root,'visual-review-queue.json',reports)
    return report

def issue(root,asset_id,category,description,severity='high'):
    if not description.strip(): raise ValueError('必须提供具体问题描述')
    assets=read(root,'assets.json',[])
    a=next((x for x in assets if x.get('id')==asset_id),None)
    if not a:raise ValueError('未知素材')
    if severity not in ('low','medium','high','critical'):raise ValueError('非法严重程度')
    tasks=read(root,'tasks.json',[])
    number=1
    ids={t.get('id') for t in tasks}
    while f'FIX-{number:04d}' in ids:number+=1
    t={'id':f'FIX-{number:04d}','shot_id':a.get('shot_id'),'asset_id':asset_id,
       'type':'review_fix','status':'planned','severity':severity,'category':category,
       'notes':description,'created_at':datetime.now(timezone.utc).isoformat(),
       'source_sha256':sha(within(root,a['path'])) if a.get('path') and within(root,a['path']).is_file() else None}
    tasks.append(t);save(root,'tasks.json',tasks)
    return t

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','issue']);p.add_argument('project_dir');p.add_argument('asset_id')
    p.add_argument('--count',type=int,default=7);p.add_argument('--category',default='visual');p.add_argument('--description',default='');p.add_argument('--severity',default='high')
    a=p.parse_args();root=Path(a.project_dir).resolve()
    result=audit(root,a.asset_id,a.count) if a.command=='audit' else issue(root,a.asset_id,a.category,a.description,a.severity)
    print(json.dumps(result,ensure_ascii=False,indent=2))
