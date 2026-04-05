#!/usr/bin/env python3
"""
应急：按「最短 zh 子串优先」+ 全文 en 去重，为 chat_json 生成 llm_annotations.json 初稿。

与 gen_dense_chat_json 的区别：同候选池内按 len(zh) **升序**，优先窄锚点（更贴近「一词」画线）。
仍**不替代** export-chat-bundle → 对话终稿；无匹配句会 skip（须 LLM 补全）。

用法（仓库根）:
  python3 workflow/gen_shortest_zh_chat_json.py <slug>
"""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTIL = ROOT / "util"
sys.path.insert(0, str(UTIL))

import annotate_lib as al
from annotate_merge import en_headword_token_ok, flatten_paragraphs
from md_split import paragraphs_from_markdown

_GD = runpy.run_path(str(ROOT / "workflow" / "gen_dense_chat_json.py"))
_BUFFETT_EXTRA: list[tuple[str, str, str, str, str]] = _GD["_BUFFETT_EXTRA"]

# 科技职场 / 本篇语境：短 zh 优先命中；en 在合并时去重
_WORKPLACE_SHORT: list[tuple[str, str, str, str, str]] = [
    ("提效", "efficiency-gains", "[ɪˈfɪʃnsi ɡeɪnz]", "n.", "提效"),
    ("绩效", "performance-review", "[pəˈfɔːməns rɪˈvjuː]", "n.", "绩效考核"),
    ("考核", "appraisal", "[əˈpreɪzl]", "n.", "考核"),
    ("强制", "coercion", "[kəʊˈɜːʃn]", "n.", "强制"),
    ("隐性", "implicit", "[ɪmˈplɪsɪt]", "adj.", "隐性的"),
    ("Token", "token-metering", "[ˈtəʊkən ˈmiːtərɪŋ]", "n.", "Token 计量"),
    ("Skills", "skills-artifact", "[skɪlz ˈɑːtɪfækt]", "n.", "Skills 资产"),
    ("Agent", "software-agent", "[ˈeɪdʒənt]", "n.", "智能体"),
    ("裁员", "headcount-cut", "[ˈhedkaʊnt kʌt]", "n.", "裁员"),
    ("优化", "rightsizing", "[ˈraɪtsaɪzɪŋ]", "n.", "人员优化"),
    ("提示词", "prompting", "[ˈprɒmptɪŋ]", "n.", "提示词"),
    ("部署", "deployment", "[dɪˈplɔɪmənt]", "n.", "部署"),
    ("审批", "approval-gate", "[əˈpruːvl ɡeɪt]", "n.", "审批"),
    ("事故", "incident", "[ˈɪnsɪdənt]", "n.", "事故"),
    ("额度", "quota", "[ˈkwəʊtə]", "n.", "额度"),
    ("自研", "in-house-build", "[ɪn haʊz bɪld]", "n.", "自研"),
    ("模板", "template", "[ˈtempleɪt]", "n.", "模板"),
    ("维度", "dimension", "[daɪˈmenʃn]", "n.", "维度"),
    ("图表", "charting", "[ˈtʃɑːtɪŋ]", "n.", "图表"),
    ("导出", "exporting", "[ɪkˈspɔːtɪŋ]", "n.", "导出"),
    ("乱码", "mojibake", "[ˈməʊdʒɪbeɪk]", "n.", "乱码"),
    ("调试", "debugging", "[diːˈbʌɡɪŋ]", "n.", "调试"),
    ("半成品", "half-baked", "[hɑːf ˈbeɪkt]", "adj.", "半成品"),
    ("调用链", "call-chain", "[kɔːl tʃeɪn]", "n.", "调用链"),
    ("状态", "statefulness", "[ˈsteɪtfəlnəs]", "n.", "状态处理"),
    ("追踪", "telemetry", "[tɪˈlemɪtri]", "n.", "追踪遥测"),
    ("退化", "atrophy", "[ˈætrəfi]", "n.", "能力退化"),
    ("激进", "aggressive-rollout", "[əˈɡresɪv]", "adj.", "激进推进"),
    ("直属", "line-manager", "[laɪn ˈmænɪdʒə]", "n.", "直属上级"),
    ("盘点", "triage", "[ˈtraɪɑːʒ]", "n.", "盘点梳理"),
    ("文档化", "documentation", "[ˌdɒkjumenˈteɪʃn]", "n.", "文档化"),
    ("端到端", "end-to-end", "[end tuː end]", "adj.", "端到端"),
    ("自费", "out-of-pocket", "[aʊt əv ˈpɒkɪt]", "adj.", "自费"),
    ("焦虑", "angst", "[æŋst]", "n.", "焦虑"),
    ("取代", "displacement", "[dɪˈspleɪsmənt]", "n.", "取代"),
    ("活水", "internal-mobility", "[ɪnˈtɜːnl məʊˈbɪləti]", "n.", "内部活水"),
    ("滥用", "misuse", "[ˌmɪsˈjuːs]", "n.", "滥用"),
    ("回收", "deprovision", "[diːprəˈvɪʒn]", "v.", "收回账号"),
    ("卡顿", "jank", "[dʒæŋk]", "n.", "卡顿"),
    ("运营商", "carrier", "[ˈkæriə]", "n.", "运营商"),
    ("复核", "second-pass-review", "[ˈsekənd pɑːs]", "n.", "复核"),
    ("恶补", "cramming", "[ˈkræmɪŋ]", "n.", "突击补习"),
    ("合规", "compliance", "[kəmˈplaɪəns]", "n.", "合规"),
    ("战略", "strategy", "[ˈstrætədʒi]", "n.", "战略"),
    ("阻力", "pushback", "[ˈpʊʃbæk]", "n.", "阻力"),
    ("草图", "mockup", "[ˈmɒkʌp]", "n.", "草图"),
    ("重塑", "reengineering", "[ˌriːendʒɪˈnɪərɪŋ]", "n.", "重塑"),
    ("路线图", "roadmap", "[ˈrəʊdmæp]", "n.", "路线图"),
    ("倡议", "initiative-pack", "[ɪˈnɪʃətɪv]", "n.", "倡议包"),
    ("监控", "monitoring", "[ˈmɒnɪtərɪŋ]", "n.", "监控"),
    ("立竿见影", "immediate-upside", "[ɪˈmiːdiət]", "adj.", "立竿见影"),
    ("压缩", "compression", "[kəmˈpreʃn]", "n.", "压缩周期"),
    ("原型", "prototype", "[ˈprəʊtətaɪp]", "n.", "原型"),
    ("拆解", "decomposition", "[ˌdiːkɒmpəˈzɪʃn]", "n.", "拆解"),
    ("头脑风暴", "brainstorming", "[ˈbreɪnstɔːmɪŋ]", "n.", "头脑风暴"),
    ("跑偏", "drift-off-spec", "[drɪft]", "n.", "执行跑偏"),
    ("倒逼", "forcing-function", "[ˈfɔːsɪŋ ˈfʌŋkʃn]", "n.", "倒逼机制"),
    ("招聘", "hiring", "[ˈhaɪərɪŋ]", "n.", "招聘"),
    ("支配", "subjection", "[səbˈdʒekʃn]", "n.", "支配"),
    ("标准化", "standardization", "[ˌstændədaɪˈzeɪʃn]", "n.", "标准化"),
    ("吃香", "in-demand", "[ɪn dɪˈmɑːnd]", "adj.", "更吃香"),
    ("自费", "self-funded-tools", "[self ˈfʌndɪd]", "adj.", "自费工具"),
    ("门槛", "floor-threshold", "[flɔː ˈθreʃhəʊld]", "n.", "保底门槛"),
    ("工业革命", "industrial-revolution", "[ɪnˈdʌstriəl]", "n.", "工业革命"),
    ("身位", "positioning", "[pəˈzɪʃnɪŋ]", "n.", "卡位"),
    ("试错", "trial-and-error", "[traɪəl ən ˈerə]", "n.", "试错"),
    ("阵痛", "dislocation", "[ˌdɪsləʊˈkeɪʃn]", "n.", "调整阵痛"),
    ("整合", "integration", "[ˌɪntɪˈɡreɪʃn]", "n.", "整合"),
    ("接入", "onboarding-tool", "[ˈɒnbɔːdɪŋ]", "n.", "接入工具"),
    ("翻倍", "doubling", "[ˈdʌblɪŋ]", "n.", "翻倍"),
    ("受访者", "respondent", "[rɪˈspɒndənt]", "n.", "受访者"),
    ("化名", "pseudonym", "[ˈsuːdənɪm]", "n.", "化名"),
    ("极客", "geek", "[ɡiːk]", "n.", "极客"),
    ("尝鲜", "early-adopter", "[ˈɜːli əˈdɒptə]", "n.", "尝鲜者"),
    ("甜头", "upside-taste", "[ˈʌpsaɪd]", "n.", "甜头"),
    ("浪潮", "surge", "[sɜːdʒ]", "n.", "浪潮"),
    ("从业者", "practitioner", "[prækˈtɪʃnə]", "n.", "从业者"),
    ("翻倍", "doubled-output", "[ˈdʌbld]", "adj.", "翻倍产出"),
    ("氛围", "climate", "[ˈklaɪmət]", "n.", "氛围"),
    ("燃料", "feedstock", "[ˈfedstɒk]", "n.", "燃料"),
    ("齿轮", "cogwheel", "[ˈkɒɡwiːl]", "n.", "齿轮"),
    ("翻篇", "chapter-turn", "[ˈtʃæptə tɜːn]", "n.", "翻篇"),
    ("通知", "notice", "[ˈnəʊtɪs]", "n.", "通知"),
    ("额度", "allotment", "[əˈlɒtmənt]", "n.", "分配额度"),
    ("琢磨", "puzzle-over", "[ˈpʌzl]", "v.", "琢磨"),
    ("崩溃", "meltdown", "[ˈmeltdaʊn]", "n.", "崩溃"),
    ("天真", "naivete", "[naɪˈiːvteɪ]", "n.", "天真"),
    ("删改", "redaction", "[rɪˈdækʃn]", "n.", "删改"),
    ("膨胀", "bloat", "[bləʊt]", "n.", "数据膨胀"),
    ("账本", "reckoning", "[ˈrekənɪŋ]", "n.", "算账"),
    ("陪", "babysit", "[ˈbeɪbɪsɪt]", "v.", "陪着试错"),
    ("负担", "burden", "[ˈbɜːdn]", "n.", "负担"),
    ("绕", "detour", "[ˈdiːtʊə]", "n.", "绕路"),
    ("校验", "validation", "[ˌvælɪˈdeɪʃn]", "n.", "校验"),
    ("分支", "branch-path", "[brɑːntʃ]", "n.", "分支"),
    ("繁琐", "onerous", "[ˈɒnərəs]", "adj.", "繁琐"),
    ("指标", "metric", "[ˈmetrɪk]", "n.", "指标"),
    ("后台", "back-office", "[bæk ˈɒfɪs]", "n.", "后台"),
    ("头疼", "headache", "[ˈhedeɪk]", "n.", "头疼"),
    ("适配", "adaptation", "[ˌædæpˈteɪʃn]", "n.", "适配"),
    ("价值", "valuation-of-work", "[væljuˈeɪʃn]", "n.", "价值判断"),
    ("坑", "pitfall", "[ˈpɪtfɔːl]", "n.", "坑"),
    ("序列", "ladder-rung", "[ˈlædə rʌŋ]", "n.", "职级序列"),
    ("试一试", "pilot-try", "[ˈpaɪlət]", "n.", "试一试"),
    ("产出量", "throughput-count", "[ˈθruːpʊt]", "n.", "产出量"),
    ("管够", "uncapped", "[ʌnˈkæpt]", "adj.", "不限量"),
    ("卷", "rat-race", "[ˈræt reɪs]", "n.", "内卷比拼"),
    ("藏着掖着", "hoarding", "[ˈhɔːdɪŋ]", "n.", "藏着掖着"),
    ("SOP", "SOP-kit", "[es əʊ piː]", "n.", "SOP 化"),
    ("报销", "reimbursement", "[ˌriːɪmˈbɜːsmənt]", "n.", "报销"),
    ("浪费", "squander", "[ˈskwɒndə]", "v.", "浪费"),
    ("专注", "laser-focus", "[ˈleɪzə]", "n.", "专注"),
    ("日志", "logging", "[ˈlɒɡɪŋ]", "n.", "日志"),
    ("规则", "ruleset", "[ˈruːlset]", "n.", "规则集"),
    ("教育", "tutoring", "[ˈtjuːtərɪŋ]", "n.", "调教模型"),
    ("薪资", "comp", "[kɒmp]", "n.", "薪酬包"),
    ("代替", "substitute", "[ˈsʌbstɪtjuːt]", "v.", "代替"),
    ("阻力", "friction", "[ˈfrɪkʃn]", "n.", "阻力"),
    ("草图", "wireframe", "[ˈwaɪəfreɪm]", "n.", "线框"),
    ("语法", "linting", "[ˈlɪntɪŋ]", "n.", "语法检查级"),
    ("清晰", "lucidity", "[luːˈsɪdəti]", "n.", "清晰"),
    ("驾驭", "mastery", "[ˈmɑːstəri]", "n.", "驾驭"),
    ("摩天大楼", "high-rise", "[ˈhaɪ raɪz]", "n.", "摩天楼"),
    ("边界", "guardrail", "[ˈɡɑːdreɪl]", "n.", "边界"),
    ("擦屁股", "firefight", "[ˈfaɪəfaɪt]", "n.", "救火善后"),
    ("繁琐", "taxing", "[ˈtæksɪŋ]", "adj.", "费神"),
    ("心智", "mental-model", "[ˈmentl ˈmɒdl]", "n.", "管理者心智"),
    ("风口", "zeitgeist", "[ˈtsaɪtɡaɪst]", "n.", "时代风口"),
    ("蛋糕", "pie-growth", "[paɪ ɡrəʊθ]", "n.", "市场蛋糕"),
    ("创意", "ideation", "[ˌaɪdiˈeɪʃn]", "n.", "创意"),
    ("车轮", "juggernaut", "[ˈdʒʌɡənɔːt]", "n.", "滚滚车轮"),
    ("缓缓", "inexorably", "[ɪnˈeksərəbli]", "adv.", "不可阻挡地"),
    ("媒体", "outlet", "[ˈaʊtlet]", "n.", "媒体"),
    ("作者", "byline", "[ˈbaɪlaɪn]", "n.", "作者署名"),
    ("刮", "pervade", "[pəˈveɪd]", "v.", "席卷"),
    ("玩具", "plaything", "[ˈpleɪθɪŋ]", "n.", "玩具"),
    ("会员", "membership", "[ˈmembəʃɪp]", "n.", "会员"),
    ("变了", "inflected", "[ɪnˈflektɪd]", "adj.", "形势变了"),
    ("阶段", "phase", "[feɪz]", "n.", "阶段"),
    ("挂钩", "linkage", "[ˈlɪŋkɪdʒ]", "n.", "挂钩"),
    ("模板", "template-row", "[ˈtempleɪt]", "n.", "工作模板"),
    ("聊了聊", "sound-out", "[saʊnd aʊt]", "v.", "聊了聊"),
    ("涵盖", "span", "[spæn]", "v.", "涵盖"),
    ("程序员", "programmer", "[ˈprəʊɡræmə]", "n.", "程序员"),
    ("实习生", "intern", "[ˈɪntɜːn]", "n.", "实习生"),
    ("分子", "holdout-persona", "[ˈhəʊldaʊt]", "n.", "不活跃分子"),
    ("兴奋", "elation", "[ɪˈleɪʃn]", "n.", "兴奋"),
    ("疲惫", "weariness", "[ˈwɪərinəs]", "n.", "疲惫"),
    ("不安", "unease", "[ʌnˈiːz]", "n.", "不安"),
    ("三周", "fortnight-plus", "[ˈfɔːtnaɪt plʌs]", "n.", "三周前语境"),
    ("明白", "dawned", "[dɔːnd]", "v.", "恍然大悟"),
    ("安全", "infosec", "[ˈɪnfəʊsek]", "n.", "数据安全"),
    ("其次", "secondly", "[ˈsekəndli]", "adv.", "其次"),
    ("文案", "copy", "[ˈkɒpi]", "n.", "文案"),
    ("逻辑", "logic-tree", "[ˈlɒdʒɪk]", "n.", "逻辑"),
    ("简单", "trivial", "[ˈtrɪviəl]", "adj.", "简单"),
    ("销售", "sales-side", "[seɪlz]", "n.", "销售侧"),
    ("活儿", "grunt-work", "[ɡrʌnt]", "n.", "体力活"),
    ("字段", "field", "[fiːld]", "n.", "字段"),
    ("对齐", "alignment", "[əˈlaɪnmənt]", "n.", "对齐"),
    ("区域", "geo-slice", "[dʒiːəʊ]", "n.", "地理区域"),
    ("修改", "iteration", "[ˌɪtəˈreɪʃn]", "n.", "修改轮次"),
    ("更新", "refresh", "[rɪˈfreʃ]", "n.", "更新"),
    ("抽卡", "stochastic-draw", "[stəˈkæstɪk]", "n.", "随机抽结果"),
    ("一半", "split-even", "[splɪt]", "n.", "一半一半"),
    ("精力", "bandwidth", "[ˈbændwɪdθ]", "n.", "精力带宽"),
    ("达标", "threshold-hit", "[ˈθreʃhəʊld]", "n.", "达标"),
    ("勤快", "diligent-use", "[ˈdɪlɪdʒənt]", "adj.", "用得勤"),
    ("交流", "compare-notes", "[kəmˈpeə nəʊts]", "v.", "交流心得"),
    ("顺手", "ad-hoc-adopt", "[æd ˈhɒk]", "adj.", "顺手用起来"),
    ("改用", "switchover", "[ˈswɪtʃəʊvə]", "n.", "改用"),
    ("收紧", "tightening", "[ˈtaɪtnɪŋ]", "n.", "收紧"),
    ("恍惚", "disoriented", "[dɪsˈɔːrientɪd]", "adj.", "恍惚"),
    ("钻研", "deep-dive", "[diːp daɪv]", "n.", "钻研"),
    ("负责", "owning", "[ˈəʊnɪŋ]", "v.", "负责盯"),
    ("担心", "misgiving", "[mɪsˈɡɪvɪŋ]", "n.", "担心"),
    ("后端", "backend", "[ˈbækend]", "n.", "后端"),
    ("氛围", "zeitgeist-shift", "[ˈtsaɪtɡaɪst]", "n.", "氛围突变"),
    ("消耗", "burn-rate", "[bɜːn reɪt]", "n.", "消耗速度"),
    ("明确", "explicit", "[ɪkˈsplɪsɪt]", "adj.", "明确"),
    ("标准", "rubric", "[ˈruːbrɪk]", "n.", "考核标准"),
    ("近期", "near-term", "[nɪə tɜːm]", "adj.", "近期"),
    ("跳过", "skipped-stage", "[skɪpt]", "adj.", "环节跳过"),
    ("提升", "ratchet-up", "[ˈrætʃɪt]", "v.", "比例提升"),
    ("全面", "blanket", "[ˈblæŋkɪt]", "adj.", "全面"),
    ("时长", "duration", "[djuˈreɪʃn]", "n.", "时长"),
    ("分享", "drop-in-share", "[drɒp ɪn]", "n.", "丢群里分享"),
    ("好用", "ergonomic", "[ˌɜːɡəˈnɒmɪk]", "adj.", "好用"),
    ("单一", "single-issue", "[ˈsɪŋɡl]", "adj.", "单一问题"),
    ("不稳定", "flaky", "[ˈfleɪki]", "adj.", "不稳定"),
    ("毋庸置疑", "axiomatic", "[ˌæksiəˈmætɪk]", "adj.", "毋庸置疑"),
    ("效率", "efficiency-noun", "[ɪˈfɪʃnsi]", "n.", "效率"),
    ("半年", "half-year", "[hɑːf jɪə]", "n.", "半年"),
    ("开放", "tooling-open", "[ˈtuːlɪŋ]", "n.", "工具开放"),
    ("理解", "read-on-AI", "[riːd ɒn]", "n.", "对 AI 的理解"),
    ("游戏", "steam-wallet", "[stiːm]", "n.", "打游戏比喻"),
    ("越多", "more-is-not-better", "[mɔː]", "adj.", "并非越多越好"),
    ("适配", "fit-for-purpose", "[fɪt]", "adj.", "适配工作"),
    ("岗位", "role", "[rəʊl]", "n.", "岗位"),
    ("明显", "salient", "[ˈseɪliənt]", "adj.", "明显"),
    ("程度", "extent", "[ɪkˈstent]", "n.", "程度"),
    ("影响", "knock-on", "[ˈnɒk ɒn]", "n.", "连锁影响"),
    ("劝", "counsel", "[ˈkaʊnsl]", "v.", "劝说"),
    ("差距", "delta", "[ˈdeltə]", "n.", "差距"),
    ("逼", "nudge", "[nʌdʒ]", "v.", "倒逼你学"),
    ("竞争力", "edge", "[edʒ]", "n.", "竞争力"),
    ("工具", "tooling", "[ˈtuːlɪŋ]", "n.", "工具栈"),
    ("确立", "ratified", "[ˈrætɪfaɪd]", "v.", "正式确立"),
    ("顺利", "bumpy", "[ˈbʌmpi]", "adj.", "并不顺利"),
    ("鼓励", "carrot-policy", "[ˈkærət]", "n.", "鼓励策略"),
    ("无限", "unmetered", "[ʌnˈmiːtəd]", "adj.", "近乎无限"),
    ("明显", "muted", "[ˈmjuːtɪd]", "adj.", "效果不明显"),
    ("排斥", "averse", "[əˈvɜːs]", "adj.", "排斥"),
    ("辅助", "assistive", "[əˈsɪstɪv]", "adj.", "辅助性"),
    ("介入", "interpose", "[ˌɪntəˈpəʊz]", "v.", "介入流程"),
    ("主导", "primacy-risk", "[ˈpraɪməsi]", "n.", "被主导"),
    ("框架", "frame", "[freɪm]", "n.", "战略框架"),
    ("经理", "manager", "[ˈmænɪdʒə]", "n.", "经理"),
    ("提交", "filing", "[ˈfaɪlɪŋ]", "n.", "提交"),
    ("进入", "enter-PIP", "[ˈentə]", "v.", "进入 PIP"),
    ("变化", "inflection", "[ɪnˈflekʃn]", "n.", "变化"),
    ("沟通", "back-and-forth", "[bæk ən ˈfɔːθ]", "n.", "多轮沟通"),
    ("输出", "ship-PRD", "[ʃɪp]", "v.", "输出 PRD"),
    ("说明", "readme-block", "[ˈriːdmiː]", "n.", "说明块"),
    ("重心", "center-of-gravity", "[ˈsentər əv ˈɡrævəti]", "n.", "重心"),
    ("开会", "syncs", "[sɪŋks]", "n.", "对齐会议"),
    ("环节", "touchpoint", "[ˈtʌtʃpɔɪnt]", "n.", "环节"),
    ("落地", "execution", "[ˌeksɪˈkjuːʃn]", "n.", "落地执行"),
    ("时间", "time-sink", "[taɪm sɪŋk]", "n.", "时间消耗"),
    ("残酷", "brutal-tradeoff", "[ˈbruːtl]", "adj.", "残酷"),
    ("董事会", "board", "[bɔːd]", "n.", "董事会"),
    ("停止", "moratorium", "[ˌmɒrəˈtɔːriəm]", "n.", "停止招聘"),
    ("迟早", "inevitable", "[ɪˈnevɪtəbl]", "adj.", "迟早"),
    ("压力", "pressure-cooker", "[ˈpreʃə]", "n.", "压力"),
    ("忙", "swamped", "[swɒmpt]", "adj.", "更忙"),
    ("变长", "elongated", "[iˈlɒŋɡeɪtɪd]", "adj.", "变长"),
    ("原因", "root-cause", "[ruːt kɔːz]", "n.", "原因"),
    ("干活", "grunt", "[ɡrʌnt]", "n.", "干活"),
    ("系统", "stack", "[stæk]", "n.", "系统栈"),
    ("出错", "misgeneration", "[mɪsˌdʒenəˈreɪʃn]", "n.", "生成出错"),
    ("范围", "blast-radius", "[blɑːst ˈreɪdiəs]", "n.", "影响范围"),
    ("看法", "take", "[teɪk]", "n.", "看法"),
    ("负责人", "owner", "[ˈəʊnə]", "n.", "负责人"),
    ("模型", "model-vendor", "[ˈmɒdl]", "n.", "大模型供应商"),
    ("衡量", "measurability", "[ˌmeʒərəˈbɪləti]", "n.", "可衡量性"),
    ("核心", "core-value", "[kɔː]", "n.", "价值核心"),
    ("合理", "defensible", "[dɪˈfensəbl]", "adj.", "合理"),
    ("员工", "individual-contributor", "[ˌɪndɪˈvɪdʒuəl]", "n.", "员工"),
    ("意识", "awareness", "[əˈweənəs]", "n.", "意识"),
    ("缩招", "hiring-pullback", "[ˈhaɪərɪŋ]", "n.", "缩招"),
    ("逻辑", "hiring-logic", "[ˈlɒdʒɪk]", "n.", "招聘逻辑"),
    ("利润", "profit-cover", "[ˈprɒfɪt]", "n.", "利润支撑"),
    ("人才", "talent-bench", "[ˈtælənt]", "n.", "人才储备"),
    ("创业", "startup-cost", "[ˈstɑːtʌp]", "n.", "创业成本"),
    ("创业者", "founder", "[ˈfaʊndə]", "n.", "创业者"),
    ("教育", "edtech-stack", "[ˈedtek]", "n.", "教育系统"),
    ("社会", "macro", "[ˈmækrəʊ]", "n.", "全社会"),
    ("涌现", "emergence", "[ɪˈmɜːdʒəns]", "n.", "涌现"),
    ("必然", "foregone", "[fɔːˈɡɒn]", "adj.", "必然"),
    ("受欢迎", "sought-after", "[ˈsɔːt ˈɑːftə]", "adj.", "更受欢迎"),
    ("淘汰", "sunset", "[ˈsʌnset]", "v.", "淘汰"),
    ("打开", "ajar", "[əˈdʒɑː]", "adj.", "打开一道门缝"),
]


def _merge_candidates_short_first() -> list[tuple[str, str, str, str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str, str, str, str]] = []
    for row in _WORKPLACE_SHORT + list(al.KEYWORDS) + _BUFFETT_EXTRA:
        k = row[1].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(row)
    out.sort(key=lambda x: len(x[0]))
    return out


def run(slug: str) -> None:
    draft = ROOT / "content" / "drafts" / slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    paras = paragraphs_from_markdown(src.read_text(encoding="utf-8"))
    all_sents, _ = flatten_paragraphs(paras)
    candidates = _merge_candidates_short_first()
    used_en: set[str] = set()
    annotations: list[dict] = []
    misses: list[int] = []

    for i, sent in enumerate(all_sents):
        body, _ = al.sentence_body_and_punct(sent)
        if not body.strip():
            annotations.append({"i": i, "skip": True})
            continue
        picked = None
        for zh, en, ipa, pos, gloss in candidates:
            if en.lower() in used_en:
                continue
            if len(zh) < 2:
                continue
            if zh not in body:
                continue
            picked = (zh, en, ipa, pos, gloss)
            break
        if not picked:
            misses.append(i)
            annotations.append({"i": i, "skip": True})
            continue
        zh, en, ipa, pos, gloss = picked
        if not en_headword_token_ok(en):
            raise ValueError(f"bad en {en!r} at i={i}")
        if not ipa.startswith("["):
            ipa = f"[{ipa.strip('[]')}]"
        used_en.add(en.lower())
        annotations.append(
            {"i": i, "zh": zh, "en": en, "ipa": ipa, "pos": pos, "gloss": gloss}
        )

    out = {"version": 1, "annotations": annotations}
    out_path = draft / "llm_annotations.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_ok = sum(1 for a in annotations if not a.get("skip"))
    print("wrote", out_path, f"annotated {n_ok}/{len(annotations)} (shortest-zh generator)")
    if misses:
        print("miss sentence indices (need LLM):", misses[:40], "..." if len(misses) > 40 else "")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_shortest_zh_chat_json.py <slug>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
