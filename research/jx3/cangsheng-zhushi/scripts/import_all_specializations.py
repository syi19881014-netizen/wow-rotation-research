#!/usr/bin/env python3
"""2026-10-30 JX3 cross-specialization research importer.

The dataset is a versioned candidate library, not a verified castable API database.
No undocumented GCD values or buffs are inferred from skill-name equality.
"""
import csv
import io
import json
import pathlib
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "all-specializations"
OUTPUT.mkdir(parents=True, exist_ok=True)

TALENT_COMMIT = "c8a6f9b1508e3d743ad14249315c4963273f1a9b"
SKILL_COMMIT = "8751fb0474aa5f37c47a99c611ba12736f5028ce"
BASE = "https://raw.githubusercontent.com/JX3BOX/jx3box-talent"
URLS = {
 "talents": f"{BASE}/{TALENT_COMMIT}/output/std/v20261030.json",
 "skills": f"{BASE}/{SKILL_COMMIT}/raw/skill.txt",
 "skill_props": f"{BASE}/{SKILL_COMMIT}/raw/skills.tab",
 "buffs": f"{BASE}/{SKILL_COMMIT}/raw/buff.txt",
 "buff_props": f"{BASE}/{SKILL_COMMIT}/raw/buff.tab",
}
SCHOOLS = {
 "傲血战意":"天策","铁牢律":"天策",
 "太虚剑意":"纯阳","紫霞功":"纯阳",
 "离经易道":"万花","花间游":"万花",
 "易筋经":"少林","洗髓经":"少林",
 "问水诀":"藏剑",
 "焚影圣诀":"明教","明尊琉璃体":"明教",
 "毒经":"五毒","补天诀":"五毒",
 "冰心诀":"七秀","云裳心经":"七秀",
 "天罗诡道":"唐门","惊羽诀":"唐门",
 "笑尘诀":"丐帮","铁骨衣":"苍云","分山劲":"苍云",
 "莫问":"长歌","相知":"长歌","北傲诀":"霸刀",
 "凌海诀":"蓬莱","隐龙诀":"凌雪阁",
 "太玄经":"衍天宗","灵素":"北天药宗","无方":"北天药宗",
 "孤锋诀":"刀宗","山海心诀":"万灵山庄",
 "周天功":"段氏","幽罗引":"无相楼",
}
PVP_KEYS = {
 "控制":("击倒","眩晕","定身","锁足","封轻功","沉默","缴械","控制效果","禁轻功","击退","打断"),
 "免控解控":("免控","免疫控制","解除控制","解除自身控制","受控状态下施展","不受控制"),
 "减疗":("减疗","治疗成效降低","受到治疗降低","疗伤成效降低","治疗吸收","重创"),
 "防守":("减伤","受到伤害降低","抵御","护盾","吸收盾","无敌","免疫伤害","回复气血","恢复气血"),
 "位移追击":("冲刺","距离提高","移动速度","移速","轻功","骑乘","交换位置","拉拽"),
 "爆发":("伤害提高","会心","破防","攻击力提高","额外造成","无视防御","斩杀","暴击"),
 "资源/调息":("调息","充能","恢复能量","增加能量","战意","内力","资源","怒气","重置"),
 "驱散":("驱散","卸除有益","清除增益","解除不利"),
}
SPELL_MENTION = re.compile(r'[“"「『]([^”"」』]{1,18})[”"」』]')
LINK_BUFF = re.compile(r"<BUFF\s+(\d+)\s+(\d+)\s+([A-Za-z]+)", re.I)
LINK_SUB = re.compile(r"<SUB\s+(\d+)\s+(\d+)", re.I)
BAD_REMARK = ("NPC","npc","BOSS","boss","小怪","守卫","技能事件","子技能","测试","关卡","副本","首领","怪物")
BAD_DESC = ("测试技能",)
MAIN_PREFIX = re.compile(r"^\(\d+\)\s*")

def get_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":"jx3-20261030-research-collector/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read()

def fetch_tab(key):
    raw=get_bytes(URLS[key])
    decoded=None
    used=None
    for enc in ("utf-8-sig","gb18030","gbk"):
        try:
            decoded=raw.decode(enc)
            used=enc
            break
        except UnicodeDecodeError: pass
    if decoded is None:raise ValueError(f"Unable to decode {key}")
    data=list(csv.DictReader(io.StringIO(decoded),delimiter="\t",quoting=csv.QUOTE_NONE))
    return data,used,len(raw)

def clean(v):
    return str(v or "").strip().replace("\x00","")

def save_csv(path, headers, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def labels(text):
    return [k for k,words in PVP_KEYS.items() if any(w in text for w in words)]

def parse_talent(name,tree):
    school=SCHOOLS[name]
    all_rows=[]
    refs=defaultdict(set)
    for tier in range(1,10):
        part=tree[str(tier)]
        follow=clean(part.get("_follow"))
        if follow:
            assert str(follow)=="7",f"Unexpected {name} tier {tier} follow {follow}"
            continue
        for pos,rec in part.items():
            if pos.startswith("_"):continue
            text=clean(rec.get("desc"))
            rid=clean(rec.get("id"))
            assert rid and clean(rec.get("name")),f"Empty talent {name} {tier}"
            inferred=labels(text)
            item={
               "门派":school,"心法":name,"所在重数":tier,"选项位置":pos,
               "适用重数":("7|8|9" if tier==7 else str(tier)),
               "奇穴名称":rec["name"],"奇穴ID":rid,"图标ID":rec.get("icon",""),
               "is_skill原始标签":rec.get("is_skill",""),
               "主动性结论":"仅当季第三方标签，主动/被动及技能替换仍须实机核验",
               "完整效果":text,"PVP关键词分类":"|".join(inferred),
               "原始meta":clean(rec.get("meta")),"原始extend":clean(rec.get("extend")),
               "原始color":rec.get("color",""),
               "GCD触发":"未知","独立CD":"未知",
               "来源版本":"JX3BOX旗舰端 v20261030",
               "当季实机核验":"尚未核验",
            }
            all_rows.append(item)
            for n in SPELL_MENTION.findall(text):
                n=n.strip()
                if n and not any(s in n for s in "，。、：；（）[]{}<>"):
                    refs[n].add(f"第{tier}重·{rec['name']}")
            if rec.get("is_skill")==1:
                refs[clean(rec["name"])].add(f"第{tier}重·主动候选:{rec['name']}")
    return all_rows,refs

def classify_skill(record,school,talent_ids,mentions):
    name=clean(record.get("Name"))
    sid=clean(record.get("SkillID"))
    rawrem=clean(record.get("Remark"))
    remark=MAIN_PREFIX.sub("",rawrem)
    desc=clean(record.get("Desc"))
    bad=any(t in remark for t in BAD_REMARK) or any(t in desc for t in BAD_DESC)
    # Exact "school-name" is the strongest candidate for castable player spells.
    exact=(remark==f"{school}-{name}" or remark==f"{school}_{name}")
    schoolprefix=(remark.startswith(f"{school}-") or remark.startswith(f"{school}_"))
    active_id=sid in talent_ids
    name_ref=name in mentions
    score=(70 if exact else 30 if schoolprefix else 0)+(55 if active_id else 0)+(12 if name_ref else 0)
    if clean(record.get("HelpDesc")):score+=12
    if desc:score+=3
    if bad:score-=90
    if not (schoolprefix or active_id or name_ref):return None
    if score<10:return None
    if bad:return None
    # Note: "skill ID in talent table" is NOT proof of castability.
    kind=("主技能高优先候选" if exact else
          "奇穴主动候选" if active_id else
          "门派关联技能候选" if schoolprefix else
          "奇穴说明提及的同名技能候选")
    return score,kind

def main():
    talents=json.loads(get_bytes(URLS["talents"]).decode("utf-8"))
    observed=[k for k in talents if k!="其它"]
    if set(observed)!=set(SCHOOLS):
        raise ValueError(f"Unexpected heart set: missing {set(SCHOOLS)-set(observed)}, new {set(observed)-set(SCHOOLS)}")
    skills,enc_skill,bytes_skill=fetch_tab("skills")
    props,enc_prop,bytes_prop=fetch_tab("skill_props")
    buffs,enc_buff,bytes_buff=fetch_tab("buffs")
    buff_props,enc_buff_prop,bytes_buff_prop=fetch_tab("buff_props")
    skill_by_name=defaultdict(list)
    skill_by_id=defaultdict(list)
    for x in skills:
        name=clean(x.get("Name"))
        if name:skill_by_name[name].append(x)
        sid=clean(x.get("SkillID"))
        if sid:skill_by_id[sid].append(x)
    prop_by_id={}
    for x in props:
        sid=clean(x.get("SkillID"))
        if sid and sid not in prop_by_id:prop_by_id[sid]=x
    buff_name=defaultdict(list)
    buff_by_id=defaultdict(list)
    for x in buffs:
        bid=clean(x.get("BuffID"))
        if bid:buff_by_id[bid].append(x)
        if clean(x.get("Name")):buff_name[clean(x["Name"])].append(x)
    buff_prop_by_id=defaultdict(list)
    for x in buff_props:
        bid=clean(x.get("ID"))
        if bid:buff_prop_by_id[bid].append(x)
    report=[]
    all_talents=[]
    pvp_rows=[]
    buff_row_count=0
    candidate_row_count=0
    for heart in observed:
        school=SCHOOLS[heart]
        outdir=OUTPUT/heart
        outdir.mkdir(parents=True,exist_ok=True)
        talent_rows,mentioned=parse_talent(heart,talents[heart])
        assert len(talent_rows)==36, f"{heart}: unexpected talents {len(talent_rows)}"
        all_talents.extend(talent_rows)
        talent_ids={x["奇穴ID"] for x in talent_rows}
        candidate_names=set(mentioned)
        direct_names=set()
        # Mark original "school-" and "school_" player skill candidates, even
        # if unrelated to current talent descriptions. Both specs may share these.
        for r in skills:
            remark=MAIN_PREFIX.sub("",clean(r.get("Remark")))
            if (remark.startswith(f"{school}-") or remark.startswith(f"{school}_")):
                if not any(word in remark for word in BAD_REMARK):
                    direct_names.add(clean(r.get("Name")))
        candidate_names.update(direct_names)
        cand=[]
        for name in sorted(candidate_names):
            for r in skill_by_name.get(name,[]):
                ranked=classify_skill(r,school,talent_ids,mentioned)
                if not ranked:continue
                score,kind=ranked
                sid=clean(r.get("SkillID"))
                props_row=prop_by_id.get(sid,{})
                cand.append({
                 "门派":school,"心法":heart,"技能名":name,"候选SkillID":sid,
                 "原始Level":clean(r.get("Level")),"候选类型":kind,"数据匹配分数":score,
                 "原始Remark":clean(r.get("Remark")),"完整技能描述":clean(r.get("Desc")),
                 "HelpDesc":clean(r.get("HelpDesc")),"SpecialDesc":clean(r.get("SpecialDesc")),
                 "相关当前奇穴":" | ".join(sorted(mentioned.get(name,set()))),
                 "raw_CastMode":clean(props_row.get("CastMode")),
                 "raw_IsPassiveSkill":clean(props_row.get("IsPassiveSkill")),
                 "raw_IsChannelSkill":clean(props_row.get("IsChannelSkill")),
                 "raw_SkillCastFlag":clean(props_row.get("SkillCastFlag")),
                 "raw_KungfuMountID":clean(props_row.get("KungfuMountID")),
                 "GCD触发":"未知","独立冷却毫秒":"","正式服能否施放":"未验证",
                 "来源快照":"2026-10-13技能原始表；候选数据"
                })
        cand.sort(key=lambda r:(r["技能名"],-r["数据匹配分数"],r["候选SkillID"],r["原始Level"]))
        # No silent truncation: multiple levels, replacements and candidates retained.
        buff_links=[]
        buff_seen=set()
        for r in cand:
            for bid,blevel,context in LINK_BUFF.findall(r["完整技能描述"]):
                key=(r["候选SkillID"],r["原始Level"],bid,blevel)
                if key in buff_seen:continue
                buff_seen.add(key)
                raw_details=buff_by_id.get(bid,[])
                matches=[x for x in raw_details if clean(x.get("Level"))==blevel]
                if not matches:matches=raw_details[:1]
                raw_name=clean(matches[0].get("Name")) if matches else ""
                raw_desc=clean(matches[0].get("Desc")) if matches else ""
                tab_rows=[b for b in buff_prop_by_id.get(bid,[]) if clean(b.get("Level"))==blevel]
                buff_tab=tab_rows[0] if tab_rows else {}
                buff_links.append({
                 "门派":school,"心法":heart,"来源候选技能":r["技能名"],
                 "来源候选SkillID":r["候选SkillID"],"来源技能等级":r["原始Level"],
                 "被引用BuffID":bid,"引用Buff等级":blevel,
                 "引用类型":context,"Buff名称(原表)":raw_name,
                 "Buff描述(原表)":raw_desc,
                 "raw_Count":clean(buff_tab.get("Count")),
                 "raw_Interval":clean(buff_tab.get("Interval")),
                 "raw_AppendType":clean(buff_tab.get("AppendType")),
                 "raw_BuffType":clean(buff_tab.get("BuffType")),
                 "raw_DetachType":clean(buff_tab.get("DetachType")),
                 "Buff用途判断":"仅引用关系；不代表当前技能必定实际施加此Buff",
                 "正式服核验":"未验证",
                 "来源快照":"2026-10-13"
                })
        signals=[{
          "门派":school,"心法":heart,"第几重":r["所在重数"],"适用重数":r["适用重数"],
          "奇穴":r["奇穴名称"],"奇穴ID":r["奇穴ID"],
          "PVP关键词标签":r["PVP关键词分类"],
          "主动标记":r["is_skill原始标签"],
          "描述":r["完整效果"],
          "解读限制":"仅关键字分类，不能由否定句或PVE条件直接推定PVP效果；未实测",
          "来源":"2026-10-30当季第三方奇穴快照"
        } for r in talent_rows if r["PVP关键词分类"]]
        save_csv(outdir/"talents_20261030.csv",list(talent_rows[0]),talent_rows)
        skill_headers=[
          "门派","心法","技能名","候选SkillID","原始Level","候选类型",
          "数据匹配分数","原始Remark","完整技能描述","HelpDesc","SpecialDesc",
          "相关当前奇穴","raw_CastMode","raw_IsPassiveSkill","raw_IsChannelSkill",
          "raw_SkillCastFlag","raw_KungfuMountID","GCD触发","独立冷却毫秒",
          "正式服能否施放","来源快照"
        ]
        save_csv(outdir/"skills_candidates_20261013.csv",skill_headers,cand)
        buff_headers=[
         "门派","心法","来源候选技能","来源候选SkillID","来源技能等级",
         "被引用BuffID","引用Buff等级","引用类型","Buff名称(原表)",
         "Buff描述(原表)","raw_Count","raw_Interval","raw_AppendType",
         "raw_BuffType","raw_DetachType","Buff用途判断","正式服核验","来源快照"
        ]
        save_csv(outdir/"buff_links_20261013.csv",buff_headers,buff_links)
        signal_headers=[
         "门派","心法","第几重","适用重数","奇穴","奇穴ID","PVP关键词标签",
         "主动标记","描述","解读限制","来源"
        ]
        save_csv(outdir/"pvp_signals_20261030.csv",signal_headers,signals)
        report.append({
         "门派":school,"心法":heart,
         "奇穴唯一选项":len(talent_rows),
         "奇穴重数":9,"第七至九重共用池":"是",
         "当季is_skill=1条数":sum(x["is_skill原始标签"]==1 for x in talent_rows),
         "近版技能候选记录":len(cand),
         "近版技能候选名称数":len({x["技能名"] for x in cand}),
         "原始BUFF引用记录数":len(buff_links),
         "有PVP关键词的奇穴选项数":len(signals),
         "正式服技能/ID/GCD核验":"未完成",
         "来源":"JX3BOX 2026-10-30奇穴 / 2026-10-13技能与Buff"
        })
        candidate_row_count+=len(cand)
        buff_row_count+=len(buff_links)
        pvp_rows.extend(signals)
    save_csv(OUTPUT/"INDEX_20261030.csv",list(report[0]),report)
    save_csv(OUTPUT/"TALENTS_ALL_20261030.csv",list(all_talents[0]),all_talents)
    save_csv(OUTPUT/"PVP_SIGNALS_ALL_20261030.csv",list(pvp_rows[0]),pvp_rows)
    summary={
     "built_utc":datetime.now(timezone.utc).isoformat(),
     "snapshot_versions":{"talents":"2026-10-30","skills":"2026-10-13","buffs":"2026-10-13"},
     "source_commits":{"talents":TALENT_COMMIT,"skills_and_buffs":SKILL_COMMIT},
     "sources":URLS,
     "heart_count":len(observed),"non_tiance_hearts":sum(SCHOOLS[x]!="天策" for x in observed),
     "school_count":len(set(SCHOOLS.values())),
     "unique_talents":len(all_talents),"talent_selection_rows_explanation":"9 tiers per heart; 7/8/9 use same 12-option pool; 36 unique options each",
     "skill_candidate_rows":candidate_row_count,"explicit_buff_link_rows":buff_row_count,
     "pvp_keyword_signal_rows":len(pvp_rows),
     "raw_sizes_bytes":{"skill":bytes_skill,"skill_props":bytes_prop,"buff":bytes_buff,"buff_props":bytes_buff_prop},
     "encodings":{"skill":enc_skill,"skill_props":enc_prop,"buff":enc_buff,"buff_props":enc_buff_prop},
     "critical_limitations":[
      "Real-time 2026-10-29+ class full ability lists are NOT verified. Skill records from 2026-10-13.",
      "Some names match NPC/child/replacement spells. Castability and GCD must be verified separately.",
      "Buff references are links found in candidate skill descriptions, NOT confirmed applied buffs.",
      "PVP keyword tags are for searching; no quantitative PvP rotation conclusions.",
      "Missing ability in current talent text does NOT mean absence in game.",
      "The '其它' empty generic specialization is intentionally excluded."
     ]
    }
    (OUTPUT/"IMPORT_REPORT_20261030.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
