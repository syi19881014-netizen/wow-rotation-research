#!/usr/bin/env python3
"""Audit 撼如雷 spell 404 vs persistent buff vs 激雷 burst buff.
Source buff snapshots are 2026-10-13 and NOT 10/29 live-verified.
"""
import csv, io, json, pathlib, re, urllib.request
from datetime import datetime, timezone

TARGET = pathlib.Path(__file__).resolve().parents[1] / "data" / "tiance"
TARGET.mkdir(parents=True, exist_ok=True)
BASE = "https://raw.githubusercontent.com/JX3BOX/jx3box-talent/master/raw/"
FILES = ["buff.txt", "buff.tab"]
TERMS = ("激雷","撼如雷")
FOCUS_BUFF_IDS = {"362","6363","2766","2767","10697"}

def download(name):
    req = urllib.request.Request(BASE+name, headers={"User-Agent":"jx3-tiance-audit/1.0"})
    with urllib.request.urlopen(req,timeout=90) as resp:
        return resp.read()

def parse_file(name):
    data=download(name)
    for encoding in ["utf-8-sig","gb18030","gbk"]:
        try:
            content=data.decode(encoding)
            break
        except UnicodeDecodeError:
            pass
    else:
        raise RuntimeError("No lossless decoder")
    reader=csv.DictReader(io.StringIO(content),delimiter="\t",quoting=csv.QUOTE_NONE)
    return list(reader),encoding,len(data)

def clean(v):
    return str(v or "").strip()

def csv_write(name,rows):
    if not rows: raise RuntimeError("No results: refusing empty import")
    keys=list(dict.fromkeys(key for row in rows for key in row))
    with open(TARGET/name,"w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def main():
    details=[]
    stats={}
    for name in FILES:
        rows,enc,size=parse_file(name)
        headers=list(rows[0]) if rows else []
        stats[name]={"count":len(rows),"size_bytes":size,"encoding":enc,"columns":headers}
        for item in rows:
            id_=clean(item.get("BuffID") or item.get("ID"))
            level=clean(item.get("Level"))
            buffname=clean(item.get("BuffName") or item.get("Name"))
            remark=clean(item.get("Remark"))
            desc=clean(item.get("Desc"))
            # Both explicit ID and exact named candidates; remark textual association
            hit=(id_ in FOCUS_BUFF_IDS or
                 any(x in f"{buffname} {remark}" for x in TERMS))
            if not hit: continue
            result={
                "source_snapshot":"2026-10-13 (prior to 苍生铸世)",
                "source_file":name,
                "BuffID":id_,"Level":level,
                "BuffName":buffname,"Remark":remark,"Desc":desc,
                "match_reason":("target explicit BuffID" if id_ in FOCUS_BUFF_IDS else "related name/remark"),
                "type_to_verify":("long_team_buff_candidate" if id_=="362"
                                  else "burst_buff_candidate_multiple_levels" if id_=="6363"
                                  else "related_buff_variant_or_homonym"),
                "2026-10-29_verified":"NO",
            }
            # Retain raw timing and effect fields without inventing seconds.
            for key in ["Count","Interval","MinInterval","MaxInterval",
                        "MaxStackNum","IsStackable","ShowTime","IsCombatBuff",
                        "BuffType","KindType","FunctionType","DetachType",
                        "AppendType","BeginAttrib1","BeginValue1A","BeginValue1B",
                        "BeginAttrib2","BeginValue2A","BeginValue2B",
                        "BeginAttrib3","BeginValue3A","BeginValue3B","ScriptFile"]:
                result["raw_"+key]=clean(item.get(key))
            details.append(result)
    csv_write("hanrulei_buff_candidates_20261013.csv",details)
    # Dedupe list by ID / Level; retain both raw source rows in CSV.
    matches={}
    for row in details:
        key=(row["BuffID"],row["Level"])
        dest=matches.setdefault(key,{"BuffID":row["BuffID"],"Level":row["Level"],
                                     "Names":[],"remarks":[],"rawSources":[]})
        if row["BuffName"] and row["BuffName"] not in dest["Names"]:dest["Names"].append(row["BuffName"])
        if row["Remark"] and row["Remark"] not in dest["remarks"]:dest["remarks"].append(row["Remark"])
        if row["source_file"] not in dest["rawSources"]:dest["rawSources"].append(row["source_file"])
    spell_rows=[]
    with open(TARGET/"skills_candidates_20261013.csv","r",encoding="utf-8-sig",newline="") as f:
        spell_rows=[r for r in csv.DictReader(f) if r["技能名"]=="撼如雷" and r["SkillID"]=="404"]
    if not spell_rows:raise RuntimeError("Skill 404 missing from existing candidate table")
    spell=next((r for r in spell_rows if r["技能等级"]=="0"),spell_rows[0])
    description=spell["完整效果"]
    links=re.findall(r"<BUFF\s+(\d+)\s+(\d+)\s+([a-z]+)",description)
    report={
      "date_utc":datetime.now(timezone.utc).isoformat(),
      "source":{n:BASE+n for n in FILES},
      "source_commit":"8751fb0474aa5f37c47a99c611ba12736f5028ce",
      "source_date":"2026-10-13",
      "spell":{"name":"撼如雷","SkillID_candidate":"404","Level_candidate":spell["技能等级"],
               "full_desc_as_of_20261013":description,
               "explicit_buff_links":links,
               "mentions_ji_lei":"激雷" in description},
      "candidate_buffs":list(matches.values()),
      "matched_record_count":len(details),
      "source_stats":stats,
      "validation_warning":"ID and duration must be confirmed against 2026-10-29+ client. Buff362 is referenced by spell404 but short-burst effect ID must be verified; raw Count/Interval cannot automatically be read as wallclock seconds."
    }
    (TARGET/"hanrulei_buff_audit_20261013.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"records":len(details),"candidate_buff_ids":sorted(set(x["BuffID"] for x in details)),
                      "buff362":next((x for x in matches.values() if x["BuffID"]=="362"),None),
                      "spell404_direct_links":links,
                      "source_counts":{k:v["count"] for k,v in stats.items()}},ensure_ascii=False))
if __name__=="__main__":
    main()
