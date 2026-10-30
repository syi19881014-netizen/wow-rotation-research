#!/usr/bin/env python3
# JX3BOX 2026 client skill data collector: read GBK snapshot, never fabricate GCD.
import csv, io, json, pathlib, re, urllib.request
from datetime import datetime, timezone
BASE = "https://raw.githubusercontent.com/JX3BOX/"
DEST = pathlib.Path(__file__).resolve().parents[1] / "data" / "tiance"
DEST.mkdir(parents=True, exist_ok=True)
FILES = {
    "skill": "jx3box-talent/master/raw/skill.txt",
    "skills": "jx3box-talent/master/raw/skills.tab",
    "talents": "jx3box-talent/master/output/std/v20261030.json",
}
# Current snapshot dates must be reported separately; skill tables are 2026-10-13,
# talent snapshot is 2026-10-30. Client validation still required.
INFO = {
 "skill_table_snapshot":"2026-10-13",
 "talent_snapshot":"2026-10-30",
 "skill_upstream_commit":"8751fb0474aa5f37c47a99c611ba12736f5028ce",
 "talent_upstream_commit":"c8a6f9b1508e3d743ad14249315c4963273f1a9b",
}
CORE = [
 "穿云","龙吟","龙牙","沧月","破风","破罡","破军",
 "疾如风","撼如雷","守如山","啸如虎","御","突","疾","灭",
 "战八方","任驰骋","乘龙箭","断魂刺","破坚阵","骑御",
 "破重围","车悬阵","啸西风","卷千旗","力破万钧","渊",
 "定军","崩","力撼河山","号令三军","破阵乐","霹雳","绕龙城·悟",
]
def download(rel):
    url = BASE + rel
    req = urllib.request.Request(url, headers={"User-Agent":"jx3-tiance-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()
def decode(raw):
    for enc in ("utf-8-sig","gb18030","gbk"):
        try:
            return raw.decode(enc),enc
        except UnicodeDecodeError:
            continue
    raise ValueError("Cannot decode source without replacement")
def tsv(rel):
    raw = download(rel)
    txt,enc = decode(raw)
    rows=list(csv.DictReader(io.StringIO(txt), delimiter="\t", quoting=csv.QUOTE_NONE))
    return rows,enc,len(raw)
def clean(s):
    return str(s or "").replace("\x00","").strip()
def write_csv(path, headers, rows):
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        out=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        out.writeheader()
        out.writerows(rows)
def main():
    skills,enc_skill,size_skill=tsv(FILES["skill"])
    skill_props,enc_prop,size_prop=tsv(FILES["skills"])
    talents=json.loads(download(FILES["talents"]).decode("utf-8"))
    all_talents=[]
    for heart in ("傲血战意","铁牢律"):
        for tier,part in talents[heart].items():
            for slot,entry in part.items():
                if slot.startswith("_") or not isinstance(entry,dict): continue
                all_talents.append((heart,tier,entry))
    # Core names + candidate active skills explicitly mentioned in current talent descriptions.
    skill_names=set(CORE)
    refs={}
    for heart,tier,e in all_talents:
        text=clean(e.get("desc"))
        for match in re.findall(r"[“\"]([^”\"]{1,16})[”\"]",text):
            term=match.strip()
            if term and not any(c in term for c in "，。、：；（）"):
                skill_names.add(term)
                refs.setdefault(term,set()).add(f"{heart}第{tier}重:{e.get('name')}")
        if e.get("is_skill")==1:
            skill_names.add(clean(e.get("name")))
    by_id={}
    for obj in skill_props:
        sid=clean(obj.get("SkillID"))
        if sid:
            by_id[sid]=obj
    found={}
    for row in skills:
        name=clean(row.get("Name"))
        if name in skill_names:
            found.setdefault(name,[]).append(row)
    # Expand with exact current talent IDs (not just their names).
    current_ids={clean(e.get("id")) for h,t,e in all_talents}
    output=[]
    raw_prop_headers=list(skill_props[0].keys()) if skill_props else []
    cd_like=[k for k in raw_prop_headers if re.search(r"cool|cd|cast|interval|prepare|channel|time|delay|limit|mount|passive",k,re.I)]
    for row in skills:
        sid=clean(row.get("SkillID"))
        name=clean(row.get("Name"))
        if name not in skill_names and sid not in current_ids:continue
        extra=by_id.get(sid,{})
        out={
          "技能名":name,"SkillID":sid,"技能等级":clean(row.get("Level")),
          "完整效果":clean(row.get("Desc")),
          "Remark":clean(row.get("Remark")),
          "HelpDesc":clean(row.get("HelpDesc")),
          "SpecialDesc":clean(row.get("SpecialDesc")),
          "SimpleDesc":clean(row.get("SimpleDesc")),
          "来源":"JX3BOX/jx3box-talent/raw/skill.txt + raw/skills.tab",
          "数据快照":"2026-10-13(资料片上线前)",
          "相关奇穴": " | ".join(sorted(refs.get(name,set()))),
          "候选主动":("是(奇穴is_skill标记)" if any(clean(e.get("id"))==sid and e.get("is_skill")==1 for h,t,e in all_talents) else "需核验"),
          "是否触发GCD":"待核验",
          "GCD毫秒":"","独立CD毫秒":"",
          "2026-10-29正式服确认":"否：仅10月13日原始数据候选",
        }
        for k in cd_like:out["raw_"+k]=clean(extra.get(k))
        output.append(out)
    output.sort(key=lambda o:(o["技能名"],int(o["SkillID"]) if o["SkillID"].isdigit() else 0,int(o["技能等级"]) if o["技能等级"].isdigit() else 0))
    headers=list(output[0].keys()) if output else []
    if not output:raise RuntimeError("No skill rows found. Refuse to silently publish an empty dataset.")
    write_csv(DEST/"skills_candidates_20261013.csv",headers,output)
    # Audit unsatisfied names and ambiguous IDs, not automatically claim completeness
    audit_rows=[]
    for name in sorted(skill_names):
        matches=found.get(name,[])
        ids=sorted({clean(v["SkillID"]) for v in matches if v.get("SkillID")})
        audit_rows.append({
          "技能名或当前奇穴提及词":name,
          "候选SkillID集合":"|".join(ids),
          "匹配记录数":len(matches),
          "备注":"需实机确认；未命中可能仅为Buff/效果名" if not ids else ("多个候选ID需逐个分辨" if len(ids)>1 else "单个候选不等于正式服验证"),
          "源表日期":"2026-10-13",
          "当前状态":"未完成正式服核对"
        })
    write_csv(DEST/"skills_name_audit_20261013.csv",list(audit_rows[0]),audit_rows)
    report={
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      **INFO,
      "sources":{key:BASE+value for key,value in FILES.items()},
      "encoding":{"skill":enc_skill,"skills":enc_prop},
      "source_sizes_bytes":{"skill":size_skill,"skills":size_prop},
      "current_talent_entries":len(all_talents),
      "candidate_name_count":len(skill_names),
      "matched_name_count":sum(bool(found.get(n)) for n in skill_names),
      "candidate_rows":len(output),
      "raw_cooldown_columns":cd_like,
      "critical_skill":"撼如雷",
      "critical_skill_candidate_ids":sorted(set(clean(r.get("SkillID")) for r in found.get("撼如雷",[]))),
      "warning":"原始技能数据为2026-10-13，比2026-10-29正式服早；GCD字段未做API或实测验证，严禁当作当前正式服完备技能表。"
    }
    (DEST/"skill_import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
