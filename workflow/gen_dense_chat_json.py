#!/usr/bin/env python3
"""
为 chat_json 生成「能配则配、全文 en 互不重复」的 llm_annotations.json 初稿。

用法（仓库根）:
  python3 workflow/gen_dense_chat_json.py <slug>

逻辑：若存在 `annotate_lexicon_extra.json` 则并入候选（优先于全局词表）；再加 KEYWORDS + 内置扩展；按 zh 长度降序匹配；**无匹配则 skip**。

不替代对话 LLM；用于在不用 synth 稀疏稿时快速铺一批可合并的义项。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTIL = ROOT / "util"
sys.path.insert(0, str(UTIL))

import annotate_lib as al
from annotate_merge import en_headword_token_ok, flatten_paragraphs
from md_split import paragraphs_from_markdown

# 与 util/keyword_lexicon 的 en 冲突しないよう、本篇专用且尽量可读的补充（巴菲特访谈域）
_BUFFETT_EXTRA: list[tuple[str, str, str, str, str]] = [
    ("伯克希尔·哈撒韦", "Berkshire-Hathaway", "[ˈbɜːkʃaɪə ˈhæθəweɪ]", "n.", "伯克希尔·哈撒韦公司"),
    ("股东大会", "shareholder-meeting", "[ˈʃeəˌhəʊldə ˈmiːtɪŋ]", "n.", "股东大会"),
    ("慈善午宴", "charity-luncheon", "[ˈtʃærəti ˈlʌntʃən]", "n.", "慈善午宴"),
    ("深度采访", "in-depth-interview", "[ɪn depθ ˈɪntəvjuː]", "n.", "深度访谈"),
    ("地缘冲突", "geopolitical-friction", "[ˌdʒiːəʊpəˈlɪtɪkl ˈfrɪkʃn]", "n.", "地缘摩擦"),
    ("剧烈波动", "whipsaw-volatility", "[ˈwɪpsɔː ˌvɒləˈtɪləti]", "n.", "剧烈波动"),
    ("公众视野", "public-sphere", "[ˈpʌblɪk sfɪə]", "n.", "公众视野"),
    ("叙事", "narrative-frame", "[ˈnærətɪv freɪm]", "n.", "叙事框架"),
    ("抄底", "bottom-fishing", "[ˈbɒtəm ˈfɪʃɪŋ]", "n.", "抄底心态"),
    ("标普500指数", "SPX-index", "[es piː eks ˈɪndeks]", "n.", "标普500"),
    ("互联网泡沫", "dotcom-bubble", "[ˈdɒtkɒm ˈbʌbl]", "n.", "互联网泡沫"),
    ("金融危机", "financial-crisis", "[faɪˈnænʃl ˈkraɪsɪs]", "n.", "金融危机"),
    ("短期国债", "T-bills", "[tiː bɪlz]", "n.", "短期国库券"),
    ("西方石油公司", "Occidental", "[ˌɒksɪˈdentl]", "n.", "西方石油（公司名）"),
    ("美国运通", "AmEx", "[æm eks]", "n.", "美国运通"),
    ("可口可乐", "Coca-Cola", "[ˈkəʊkə ˈkəʊlə]", "n.", "可口可乐"),
    ("转换成本", "switching-cost", "[ˈswɪtʃɪŋ kɒst]", "n.", "转换成本"),
    ("护城河", "economic-moat", "[ˌiːkəˈnɒmɪk məʊt]", "n.", "经济护城河"),
    ("资产负债表", "balance-sheet", "[ˈbæləns ʃiːt]", "n.", "资产负债表"),
    ("沙拉油丑闻", "salad-oil-scandal", "[ˈsæləd ɔɪl ˈskændl]", "n.", "色拉油丑闻"),
    ("挤兑", "bank-run", "[bæŋk rʌn]", "n.", "挤兑"),
    ("无担保", "unsecured", "[ˌʌnsɪˈkjʊəd]", "adj.", "无担保的"),
    ("多米诺骨牌", "domino-effect", "[ˈdɒmɪnəʊ ɪˈfekt]", "n.", "多米诺效应"),
    ("摩根大通", "JPMorgan", "[dʒeɪ piː ˈmɔːɡən]", "n.", "摩根大通"),
    ("美联储", "Fed", "[fed]", "n.", "美联储"),
    ("银行系统", "banking-system", "[ˈbæŋkɪŋ ˈsɪstəm]", "n.", "银行体系"),
    ("内卷", "involution", "[ˌɪnvəˈluːʃn]", "n.", "内卷"),
    ("大模型", "foundation-model", "[faʊnˈdeɪʃn ˈmɒdl]", "n.", "基础大模型"),
    ("落地", "commercialization", "[kəˌmɜːʃəlaɪˈzeɪʃn]", "n.", "商业化落地"),
    ("颠覆", "disrupt", "[dɪsˈrʌpt]", "v.", "颠覆"),
    ("空前", "unprecedented", "[ʌnˈpresɪdentɪd]", "adj.", "空前的"),
    ("断言", "contend", "[kənˈtend]", "v.", "断言、主张"),
    ("迷茫", "disorientation", "[dɪsˌɔːriənˈteɪʃn]", "n.", "迷茫"),
    ("惊喜", "windfall-surprise", "[ˈwɪndfɔːl səˈpraɪz]", "n.", "意外之喜"),
    ("淡出", "recede", "[rɪˈsiːd]", "v.", "淡出"),
    ("信息量", "information-density", "[ˌɪnfəˈmeɪʃn ˈdensəti]", "n.", "信息密度"),
    ("提炼", "distill", "[dɪˈstɪl]", "v.", "提炼"),
    ("预测分析", "prognostication", "[prɒɡˌnɒstɪˈkeɪʃn]", "n.", "预测研判"),
    ("风口", "zeitgeist-niche", "[ˈtsaɪtɡaɪst nɪtʃ]", "n.", "风口（时代机会）"),
    ("神经", "psyche", "[ˈsaɪki]", "n.", "心理神经"),
    ("船长", "skipper", "[ˈskɪpə]", "n.", "船长"),
    ("随机", "stochastic", "[stəˈkæstɪk]", "adj.", "随机的"),
    ("躺平", "opt-out", "[ɒpt aʊt]", "n.", "退出内卷"),
    ("持有者", "buy-and-holder", "[baɪ ən ˈhəʊldə]", "n.", "长期持有者"),
    ("部署", "deploy-capital", "[dɪˈplɔɪ ˈkæpɪtl]", "v.", "配置资金"),
    ("吸引力", "appeal", "[əˈpiːl]", "n.", "吸引力"),
    ("恐慌性", "capitulation", "[kəˌpɪtjʊˈleɪʃn]", "n.", "恐慌抛售"),
    ("认知", "conviction", "[kənˈvɪkʃn]", "n.", "确信、认知"),
    ("信条", "creed", "[kriːd]", "n.", "信条"),
    ("消费品", "consumer-staples", "[kənˈsjuːmə ˈsteɪplz]", "n.", "必需消费品"),
    ("制程", "process-node", "[ˈprəʊsəʊs nəʊd]", "n.", "制程节点"),
    ("算法", "algorithmic", "[ˌælɡəˈrɪðmɪk]", "adj.", "算法的"),
    ("生态", "walled-garden", "[wɔːld ˈɡɑːdn]", "n.", "封闭生态"),
    ("忠诚", "stickiness", "[ˈstɪkinəs]", "n.", "用户粘性"),
    ("草率", "perfunctory", "[pəˈfʌŋktəri]", "adj.", "草率的"),
    ("溢价", "premium-pricing", "[ˈpriːmiəm ˈpraɪsɪŋ]", "n.", "溢价"),
    ("下重注", "size-up", "[saɪz ʌp]", "v.", "加大仓位"),
    ("能力圈", "circle-of-competence", "[ˈsɜːkl əv ˈkɒmpɪtəns]", "n.", "能力圈"),
    ("边界", "guardrails", "[ˈɡɑːdreɪlz]", "n.", "边界护栏"),
    ("非理性", "irrationality", "[ɪˌræʃəˈnæləti]", "n.", "非理性"),
    ("核威胁", "nuclear-proliferation-risk", "[ˈnjuːkliə prəˌlɪfəˈreɪʃn rɪsk]", "n.", "核扩散风险"),
    ("傲慢", "hubris", "[ˈhjuːbrɪs]", "n.", "傲慢"),
    ("敬畏", "reverence", "[ˈrevərəns]", "n.", "敬畏"),
    ("不确定性", "uncertainty", "[ʌnˈsɜːtnti]", "n.", "不确定性"),
    ("早鸟价", "early-bird-rate", "[ˈɜːli bɜːd reɪt]", "n.", "早鸟票价"),
    ("内布拉斯加", "Nebraska", "[nəˈbræskə]", "n.", "内布拉斯加州"),
    ("家具城", "furniture-mart", "[ˈfɜːnɪtʃə mɑːt]", "n.", "家具卖场"),
    ("精英", "cognoscenti", "[ˌkɒnjəʊˈʃenti]", "n.", "精英圈层"),
    ("爱泼斯坦", "Epstein-case", "[ˈepstaɪn keɪs]", "n.", "爱泼斯坦案"),
    ("核武器", "nuclear-arsenal", "[ˈnjuːkliər ˈɑːsənl]", "n.", "核武库"),
    ("Youtube", "YouTube", "[ˈjuːtjuːb]", "n.", "YouTube"),
    ("CNBC", "CNBC", "[ˌsiː en biː ˈsiː]", "n.", "CNBC"),
    ("CEO", "CEO", "[ˌsiː iː ˈəʊ]", "n.", "首席执行官"),
    ("道指", "Dow", "[daʊ]", "n.", "道琼斯指数"),
    ("纳指", "Nasdaq", "[ˈnæzdæk]", "n.", "纳斯达克"),
    ("原油", "crude-oil", "[kruːd ɔɪl]", "n.", "原油"),
    ("股市", "equities", "[ˈekwətiz]", "n.", "股票资产"),
    ("专家", "punditry", "[ˈpʌndɪtri]", "n.", "专家言论"),
    ("潮水", "deluge", "[ˈdeljuːdʒ]", "n.", "潮水般"),
    ("焦虑", "angst", "[æŋst]", "n.", "焦虑"),
    ("采访", "sit-down", "[ˈsɪt daʊn]", "n.", "专访"),
    ("退休", "step-down", "[step daʊn]", "n.", "卸任"),
    ("出场", "swan-song", "[swɒn sɒŋ]", "n.", "告别演出"),
    ("出山", "comeback", "[ˈkʌmbæk]", "n.", "复出"),
    ("重启", "relaunch", "[riːˈlɔːntʃ]", "v.", "重启"),
    ("骗你", "hoodwink", "[ˈhʊdwɪŋk]", "v.", "欺骗"),
    ("明天", "morrow-outlook", "[ˈmɒrəʊ ˈaʊtlʊk]", "n.", "明日走向"),
    ("涨跌", "ebb-and-flow", "[eb ən fləʊ]", "n.", "涨跌起伏"),
    ("贪婪", "avarice", "[ˈævərɪs]", "n.", "贪婪"),
    ("恐惧", "trepidation", "[ˌtrepɪˈdeɪʃn]", "n.", "恐惧"),
    ("精算", "actuarial", "[ˌæktʃuˈeəriəl]", "adj.", "精算式的"),
    ("洞察", "insight", "[ˈɪnsaɪt]", "n.", "洞察"),
    ("同行", "cohort", "[ˈkəʊhɔːt]", "n.", "同行伙伴"),
    ("子弹", "dry-powder", "[draɪ ˈpaʊdə]", "n.", "现金弹药"),
    ("后路", "backstop", "[ˈbækstɒp]", "n.", "安全垫"),
    ("本质", "essence", "[ˈesns]", "n.", "本质"),
    ("落地之年", "inflection-year", "[ɪnˈflekʃn jɪə]", "n.", "拐点之年"),
    ("票务", "ticketing", "[ˈtɪkɪtɪŋ]", "n.", "票务"),
    ("剧场", "auditorium", "[ˌɔːdɪˈtɔːriəm]", "n.", "剧场"),
    ("回放", "replay", "[riːˈpleɪ]", "n.", "录像回放"),
    ("直播", "livestream", "[ˈlaɪvstriːm]", "n.", "直播"),
    ("完整文章", "full-article", "[fʊl ˈɑːtɪkl]", "n.", "全文"),
    ("点击阅读", "read-more", "[riːd mɔː]", "n.", "点击阅读"),
    ("购票", "ticketing-link", "[ˈtɪkɪtɪŋ lɪŋk]", "n.", "购票链接"),
    ("团队", "contingent", "[kənˈtɪndʒənt]", "n.", "团队一行"),
    ("不见不散", "rendezvous", "[ˈrɒndɪvuː]", "n.", "约定见面"),
    ("时代", "epoch", "[ˈiːpɒk]", "n.", "时代"),
    ("工具", "modality", "[məʊˈdæləti]", "n.", "工具形态"),
    ("行动", "course-of-action", "[kɔːs əv ˈækʃn]", "n.", "行动路径"),
    ("智慧", "sapience", "[ˈseɪpiəns]", "n.", "智慧"),
    ("假装", "feign", "[feɪn]", "v.", "假装"),
    ("值得", "worthwhile", "[ˌwɜːθˈwaɪl]", "adj.", "值得的"),
    ("复杂", "knotty", "[ˈnɒti]", "adj.", "复杂的"),
    ("淘汰", "obsolesce", "[ˌɒbsəˈles]", "v.", "被淘汰"),
    ("错过", "forgo", "[fɔːˈɡəʊ]", "v.", "错过"),
    ("确定性", "surefootedness", "[ˈʃʊəfʊtɪdnəs]", "n.", "踏实确定性"),
    ("有效", "efficacious", "[ˌefɪˈkeɪʃəs]", "adj.", "有效的"),
    ("漫长", "interminable", "[ɪnˈtɜːmɪnəbl]", "adj.", "漫长的"),
    ("变革", "tectonic-shift", "[tekˈtɒnɪk ʃɪft]", "n.", "结构性变革"),
    ("革命", "upheaval", "[ʌpˈhiːvl]", "n.", "剧变"),
    ("工作", "toil", "[tɔɪl]", "n.", "劳作"),
    ("努力", "strive", "[straɪv]", "n.", "努力"),
    ("世界", "macrocosm", "[ˈmækrəʊkɒzəm]", "n.", "宏观世界"),
    ("速度", "velocity", "[vəˈlɒsəti]", "n.", "速度"),
    ("冲突", "conflagration", "[ˌkɒnfləˈɡreɪʃn]", "n.", "冲突战火"),
    ("涨了", "uptick", "[ˈʌptɪk]", "n.", "上涨"),
    ("跌了", "drawdown", "[ˈdrɔːdaʊn]", "n.", "回撤"),
    ("情绪", "sentiment", "[ˈsentɪmənt]", "n.", "情绪"),
    ("普遍", "pervasive", "[pəˈveɪsɪv]", "adj.", "普遍的"),
    ("怎么办", "what-next", "[wɒt nekst]", "n.", "下一步怎么办"),
    ("前几天", "recently", "[ˈriːsntli]", "adv.", "近日"),
    ("罕见", "uncharacteristic", "[ˌʌnˌkærəktəˈrɪstɪk]", "adj.", "一反常态"),
    ("宣布", "pronouncement", "[prəˈnaʊnsmənt]", "n.", "宣布"),
    ("传奇", "lore", "[lɔː]", "n.", "传奇"),
    ("老人家", "nonagenarian", "[ˌnɒnəˈdʒeəriən]", "n.", "高龄长者"),
    ("慈善", "philanthropy", "[fɪˈlænθrəpi]", "n.", "慈善"),
    ("访谈", "colloquy", "[ˈkɒləkwi]", "n.", "对谈"),
    ("聊着", "meander", "[miˈændə]", "v.", "漫谈"),
    ("试着", "essay", "[ˈeseɪ]", "v.", "尝试"),
    ("收获", "takeaways", "[ˈteɪkəweɪz]", "n.", "收获要点"),
    ("图片", "still-image", "[stɪl ˈɪmɪdʒ]", "n.", "配图"),
    ("关于", "primer-on", "[ˈpraɪmər ɒn]", "n.", "关于…的导读"),
    ("有人", "interlocutor", "[ˌɪntəˈlɒkjətə]", "n.", "某人"),
    ("未来", "foresight", "[ˈfɔːsaɪt]", "n.", "预见"),
    ("每天", "quotidian", "[kwɒˈtɪdiən]", "adj.", "日复一日的"),
    ("看到", "behold", "[bɪˈhəʊld]", "v.", "看到"),
    ("无数", "myriad", "[ˈmɪriəd]", "adj.", "无数"),
    ("反复", "iteratively", "[ˈɪtərətɪvli]", "adv.", "反复地"),
    ("拍打", "pummel", "[ˈpʌml]", "v.", "拍打"),
    ("认为", "posit", "[ˈpɒzɪt]", "v.", "认为"),
    ("接下来", "going-forward", "[ˈɡəʊɪŋ ˈfɔːwəd]", "n.", "接下来"),
    ("吃饭", "livelihood", "[ˈlaɪvlɪhʊd]", "n.", "谋生"),
    ("合理", "tenable", "[ˈtenəbl]", "adj.", "站得住脚的"),
    ("能力", "aptitude", "[ˈæptɪtjuːd]", "n.", "能力"),
    ("灵魂", "psyche-layer", "[ˈsaɪki leɪə]", "n.", "灵魂层面"),
    ("组成", "constitute", "[ˈkɒnstɪtjuːt]", "v.", "构成"),
    ("新闻发布会", "presser", "[ˈpresə]", "n.", "新闻发布会"),
    ("金矿", "lode", "[ləʊd]", "n.", "矿脉"),
    ("大多数", "preponderance", "[prɪˈpɒndərəns]", "n.", "大多数"),
    ("能力", "knack", "[næk]", "n.", "诀窍"),
    ("躺平", "demur", "[dɪˈmɜː]", "v.", "却步"),
    ("判断", "adjudicate", "[əˈdʒuːdɪkeɪt]", "v.", "判断"),
    ("生意", "franchise", "[ˈfræntʃaɪz]", "n.", "生意本体"),
    ("今天", "as-of-now", "[æz əv naʊ]", "n.", "截至当下"),
    ("概念", "notion", "[ˈnəʊʃn]", "n.", "概念"),
    ("季度", "quarterly", "[ˈkwɔːtəli]", "adj.", "季度的"),
    ("表现", "showing", "[ˈʃəʊɪŋ]", "n.", "表现"),
    ("恐惧", "angst-cycle", "[æŋst ˈsaɪkl]", "n.", "恐惧周期"),
    ("兴趣", "appetency", "[ˈæpɪtənsi]", "n.", "兴趣"),
    ("真正", "veritable", "[ˈverɪtəbl]", "adj.", "真正的"),
    ("捡", "scavenge", "[ˈskævɪndʒ]", "v.", "捡拾"),
    ("地震", "temblor", "[ˈtemblɔː]", "n.", "地震"),
    ("金店老板", "bullion-dealer", "[ˈbʊliən ˈdiːlə]", "n.", "金店老板"),
    ("折扣", "markdown", "[ˈmɑːkdaʊn]", "n.", "打折"),
    ("层面", "stratum", "[ˈstrɑːtəm]", "n.", "层面"),
    ("价格波动", "mark-to-market", "[mɑːk tə ˈmɑːkɪt]", "n.", "盯市波动"),
    ("投资银行", "IB-outreach", "[aɪ biː ˈaʊtriːtʃ]", "n.", "投行推销"),
    ("干脆", "brusque", "[brʊsk]", "adj.", "干脆"),
    ("拒绝", "rebuff", "[rɪˈbʌf]", "v.", "拒绝"),
    ("持有", "holdout", "[ˈhəʊldaʊt]", "n.", "长期持有"),
    ("例子", "vignette", "[vɪnˈjet]", "n.", "小例子"),
    ("心态", "mindset", "[ˈmaɪndset]", "n.", "心态"),
    ("含义", "purport", "[pəˈpɔːt]", "n.", "含义"),
    ("冲", "charge-in", "[tʃɑːdʒ ɪn]", "v.", "冲进去"),
    ("垃圾堆", "scrapheap", "[ˈskræphiːp]", "n.", "垃圾堆"),
    ("洞察", "perspicacity", "[ˌpɜːspɪˈkæsəti]", "n.", "洞察力"),
    ("勇气", "fortitude", "[ˈfɔːtɪtjuːd]", "n.", "勇气"),
    ("增长", "accretion", "[əˈkriːʃn]", "n.", "积累增长"),
    ("首要", "primacy", "[ˈpraɪməsi]", "n.", "首要性"),
    ("生存", "survivalism", "[səˈvaɪvəlɪzəm]", "n.", "生存优先"),
    ("进攻", "offense", "[ˈɒfens]", "n.", "进攻"),
    ("防守", "defense", "[dɪˈfens]", "n.", "防守"),
    ("现金", "liquidity-pile", "[lɪˈkwɪdəti paɪl]", "n.", "现金堆"),
    ("准备", "readiness", "[ˈredinəs]", "n.", "准备"),
    ("稳定", "homeostasis", "[ˌhɒmiəʊˈsteɪsɪs]", "n.", "稳态"),
    ("危机", "calamity", "[kəˈlæməti]", "n.", "危机"),
    ("就业", "payrolls", "[ˈpeɪrəʊlz]", "n.", "就业"),
    ("强大", "formidable", "[ˈfɔːmɪdəbl]", "adj.", "强大"),
    ("脆弱", "fragility", "[frəˈdʒɪləti]", "n.", "脆弱性"),
    ("高度互联", "interconnectedness", "[ˌɪntəkəˈnektɪdnəs]", "n.", "互联度"),
    ("信任", "fiduciary-trust", "[fɪˈdjuːʃəri trʌst]", "n.", "信任"),
    ("积木", "jenga-tower", "[ˈdʒeŋɡə ˈtaʊə]", "n.", "积木塔"),
    ("业务规模", "throughput", "[ˈθruːpʊt]", "n.", "业务吞吐量"),
    ("强大", "muscle", "[ˈmʌsl]", "n.", "实力"),
    ("高效", "efficiency-edge", "[ɪˈfɪʃnsi edʒ]", "n.", "效率优势"),
    ("崩溃", "implosion", "[ɪmˈpləʊʒn]", "n.", "内爆式崩溃"),
    ("原则", "precept", "[ˈpriːsept]", "n.", "原则"),
    ("巨量", "war-chest", "[wɔː tʃest]", "n.", "资金储备"),
    ("谨慎", "circumspection", "[ˌsɜːkəmˈspekʃn]", "n.", "谨慎"),
    ("长期债券", "long-bonds", "[lɒŋ bɒndz]", "n.", "长期债券"),
    ("赚钱", "alpha", "[ˈælfə]", "n.", "超额收益"),
    ("活着", "going-concern", "[ˈɡəʊɪŋ kənˈsɜːn]", "n.", "持续经营"),
    ("趋势", "vector", "[ˈvektə]", "n.", "趋势向量"),
    ("入局", "late-entry", "[leɪt ˈentri]", "n.", "晚入场"),
    ("游戏", "gameboard", "[ˈɡeɪmbɔːd]", "n.", "棋局"),
    ("一辈子", "lifetime", "[ˈlaɪftaɪm]", "n.", "一辈子"),
    ("打破", "breach", "[briːtʃ]", "v.", "打破"),
    ("定义", "taxonomy", "[tækˈsɒnəmi]", "n.", "分类定义"),
    ("研究", "due-diligence", "[djuː ˈdɪlɪdʒəns]", "n.", "尽职研究"),
    ("照片", "photo-roll", "[ˈfəʊtəʊ rəʊl]", "n.", "相册"),
    ("联系人", "rolodex", "[ˈrəʊlədeks]", "n.", "通讯录"),
    ("习惯", "habituated", "[həˈbɪtʃueɪtɪd]", "adj.", "养成习惯的"),
    ("必需品", "staple-good", "[ˈsteɪpl ɡʊd]", "n.", "必需品"),
    ("丑闻", "imbroglio", "[ɪmˈbrəʊliəʊ]", "n.", "丑闻纠葛"),
    ("仓单", "warehouse-receipt", "[ˈweəhaʊs rɪˈsiːt]", "n.", "仓单"),
    ("背书", "backstop-credit", "[ˈbækstɒp ˈkredɪt]", "n.", "信用背书"),
    ("完蛋", "write-off", "[ˈraɪt ɒf]", "n.", "一笔勾销"),
    ("损失", "impairment", "[ɪmˈpeəmənt]", "n.", "减值"),
    ("果断", "decisiveness", "[dɪˈsaɪsɪvnəs]", "n.", "果断"),
    ("依据", "lodestar", "[ˈləʊdstɑː]", "n.", "依据北极星"),
    ("听说", "hearsay", "[ˈhɪəseɪ]", "n.", "道听途说"),
    ("懂", "grok", "[ɡrɒk]", "v.", "真正理解"),
    ("高手", "adept", "[əˈdept]", "n.", "高手"),
    ("出手", "foray", "[ˈfɒreɪ]", "n.", "出手"),
    ("提及", "broach", "[brəʊtʃ]", "v.", "提及"),
    ("领域", "domain", "[dəˈmeɪn]", "n.", "领域"),
    ("底层", "substrate", "[ˈsʌbstreɪt]", "n.", "底层"),
    ("量化", "quant", "[kwɒnt]", "n.", "量化"),
    ("神秘", "occult", "[ˈɒkʌlt]", "adj.", "神秘难测"),
    ("扰动", "perturbation", "[ˌpɜːtəˈbeɪʃn]", "n.", "扰动"),
    ("坚韧", "resilience", "[rɪˈzɪliəns]", "n.", "韧性"),
    ("瞬间", "blink", "[blɪŋk]", "n.", "瞬息"),
    ("崩塌", "cascade", "[kæˈskeɪd]", "n.", "连锁崩塌"),
    ("圈层", "stratum-elite", "[ˈstrɑːtəm ɪˈliːt]", "n.", "精英圈层"),
    ("弱点", "Achilles-heel", "[əˌkɪliːz ˈhiːl]", "n.", "致命弱点"),
    ("震惊", "stupefaction", "[ˌstjuːpɪˈfækʃn]", "n.", "震惊"),
    ("寿命", "tenure", "[ˈtenjə]", "n.", "存续期"),
    ("核武器", "deterrent", "[dɪˈterənt]", "n.", "威慑武器"),
    ("领导人", "steward", "[ˈstjuːəd]", "n.", "掌舵人"),
    ("行为", "conduct", "[ˈkɒndʌkt]", "n.", "行为"),
    ("驱动", "animus", "[ˈænɪməs]", "n.", "驱动力"),
    ("傲慢", "superbia", "[suːˈpɜːbiə]", "n.", "傲慢（拉丁语源）"),
    ("控制", "risk-governance", "[rɪsk ˈɡʌvənəns]", "n.", "风险控制"),
    ("完美", "airtight", "[ˈeətaɪt]", "adj.", "天衣无缝"),
    ("评估", "appraise", "[əˈpreɪz]", "v.", "评估"),
    ("项目", "initiative", "[ɪˈnɪʃətɪv]", "n.", "项目"),
    ("爆发", "eruption", "[ɪˈrʌpʃn]", "n.", "爆发"),
    ("选择", "elect", "[ɪˈlekt]", "v.", "选择"),
    ("总结", "recap", "[ˈriːkæp]", "n.", "总结"),
    ("个人", "individual", "[ˌɪndɪˈvɪdʒuəl]", "n.", "个人"),
    ("行动", "praxis", "[ˈpræksɪs]", "n.", "实践行动"),
    ("假装", "posture", "[ˈpɒstʃə]", "v.", "装腔"),
    ("东西", "desideratum", "[dɪˌzɪdəˈreɪtəm]", "n.", "所欲之物"),
    ("信息", "signal-noise", "[ˈsɪɡnəl nɔɪz]", "n.", "信息噪声"),
    ("风口", "meme-cycle", "[miːm ˈsaɪkl]", "n.", "风口周期"),
    ("淘汰", "displace", "[dɪˈspleɪs]", "v.", "取代淘汰"),
    ("创造", "value-creation", "[ˈvæljuː kriˈeɪʃn]", "n.", "创造价值"),
    ("底层", "bedrock", "[ˈbedrɒk]", "n.", "底层基石"),
    ("学习", "internalize", "[ɪnˈtɜːnəlaɪz]", "v.", "内化学习"),
    ("充满", "fraught", "[frɔːt]", "adj.", "充满…的"),
    ("不确定性", "indeterminacy", "[ˌɪndɪˈtɜːmɪnəsi]", "n.", "不可判定性"),
    ("然后", "thereupon", "[ˌðeərˈpɒn]", "adv.", "随后"),
    ("漫长", "long-arc", "[lɒŋ ɑːk]", "n.", "长周期"),
    ("见证", "witness", "[ˈwɪtnəs]", "v.", "见证"),
    ("落地", "fielding", "[ˈfiːldɪŋ]", "n.", "落地部署"),
    ("案例", "caselet", "[ˈkeɪslət]", "n.", "小案例"),
    ("年度演讲", "keynote", "[ˈkiːnəʊt]", "n.", "主题演讲"),
    ("主题", "motif", "[məʊˈtiːf]", "n.", "主题"),
]

_EXTRA_JSON_NAME = "annotate_lexicon_extra.json"


def _load_extra_entries(draft: Path) -> list[tuple[str, str, str, str, str]]:
    p = draft / _EXTRA_JSON_NAME
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries")
    if not isinstance(raw, list):
        return []
    out: list[tuple[str, str, str, str, str]] = []
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        zh = str(row.get("zh", "")).strip()
        en = str(row.get("en", "")).strip()
        ipa = str(row.get("ipa", "")).strip()
        pos = str(row.get("pos", "")).strip()
        gloss = str(row.get("gloss", "")).strip()
        if not zh or not en or not ipa or not pos or not gloss:
            raise ValueError(f"{p}: entries[{i}] missing zh/en/ipa/pos/gloss")
        if not en_headword_token_ok(en):
            raise ValueError(f"{p}: entries[{i}] invalid en={en!r}")
        out.append((zh, en, ipa, pos, gloss))
    return out


def _merge_candidates(draft: Path) -> list[tuple[str, str, str, str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str, str, str, str]] = []
    # 同目录 extra 优先于全局词表（按 en 去重时保留先出现的行）
    for row in _load_extra_entries(draft) + list(al.KEYWORDS) + _BUFFETT_EXTRA:
        k = row[1].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(row)
    out.sort(key=lambda x: len(x[0]), reverse=True)
    return out


def run(slug: str) -> None:
    draft = ROOT / "content" / "drafts" / slug
    src = draft / "01-source.md"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    paras = paragraphs_from_markdown(src.read_text(encoding="utf-8"))
    all_sents, _ = flatten_paragraphs(paras)
    candidates = _merge_candidates(draft)
    used_en: set[str] = set()
    annotations: list[dict] = []

    for i, sent in enumerate(all_sents):
        body, _ = al.sentence_body_and_punct(sent)
        if not body.strip():
            annotations.append({"i": i, "skip": True})
            continue
        picked = None
        for zh, en, ipa, pos, gloss in candidates:
            if en.lower() in used_en:
                continue
            if zh in body:
                picked = (zh, en, ipa, pos, gloss)
                break
        if not picked:
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
    print("wrote", out_path, f"annotated {n_ok}/{len(annotations)} sentences (dense generator)")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_dense_chat_json.py <slug>")
    run(sys.argv[1])


if __name__ == "__main__":
    main()
