#!/usr/bin/env python3
"""
Shared library: KEYWORDS, paragraph annotation, vocab extraction, post HTML shell.
句内无 KEYWORDS 命中时不插入 word-block（宁缺毋滥）。
Used by util/annotate-wechat-plain.py (微信 profile) and workflow/ (MD 草稿流水线).
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

# (substring in sentence body, english, ipa, pos, gloss) — pick_keyword uses longest match + leftmost tie-break; english one token (no spaces)
KEYWORDS: list[tuple[str, str, str, str, str]] = sorted(
    [
        ("国内政治秩序", "domestic-order", "[dəˈmestɪk ˈɔːdə]", "n.", "国内政治秩序"),
        ("地缘政治秩序", "geopolitical-order", "[ˌdʒiːəʊpəˈlɪtɪkl ˈɔːdə]", "n.", "地缘政治秩序"),
        ("世界储备货币", "world-reserve-currency", "[wɜːld rɪˈzɜːv ˈkʌrənsi]", "n.", "世界/全球储备货币（如美元）"),
        ("偿债支出", "debt-service", "[det ˈsɜːvɪs]", "n.", "偿债支出（本息偿付负担）"),
        ("供需失衡", "disequilibrium", "[ˌdɪsiːkwɪˈlɪbriəm]", "n.", "失衡"),
        ("地缘政治", "geopolitics", "[ˌdʒiːəʊpəˈlɪtɪks]", "n.", "地缘政治"),
        ("政治极化", "polarization", "[ˌpəʊləraɪˈzeɪʃn]", "n.", "政治极化"),
        ("民粹主义", "populism", "[ˈpɒpjəlɪzəm]", "n.", "民粹主义"),
        ("专制统治", "autocracy", "[ɔːˈtɒkrəsi]", "n.", "专制统治"),
        ("政治秩序", "political-order", "[pəˈlɪtɪkl ˈɔːdə]", "n.", "政治秩序"),
        ("货币秩序", "monetary-order", "[ˈmʌnɪtri ˈɔːdə]", "n.", "货币秩序"),
        ("货币体系", "monetary-system", "[ˈmʌnɪtri ˈsɪstəm]", "n.", "货币体系"),
        ("资本市场", "capital-markets", "[ˈkæpɪtl ˈmɑːkɪts]", "n.", "资本市场"),
        ("财政窟窿", "fiscal-gap", "[ˈfɪskl ɡæp]", "n.", "财政缺口（窟窿）"),
        ("储备货币", "currency", "[ˈkʌrənsi]", "n.", "储备货币（央行持有的外币资产）"),
        ("大周期", "mega-cycle", "[ˈmeɡə saɪkl]", "n.", "大周期"),
        ("秩序崩溃", "order-breakdown", "[ˈɔːdə ˈbreɪkdaʊn]", "n.", "秩序崩溃、瓦解"),
        ("黄金暴涨", "gold-surge", "[ɡəʊld sɜːdʒ]", "n.", "黄金价格暴涨"),
        ("地缘博弈", "geopolitical-rivalry", "[ˌdʒiːəʊpəˈlɪtɪkl ˈraɪvlri]", "n.", "地缘战略博弈"),
        ("周期透镜", "cyclical-lens", "[ˈsaɪklɪkl lenz]", "n.", "周期透镜（观察框架）"),
        ("国内政治", "politics", "[ˈpɒlɪtɪks]", "n.", "国内政治"),
        ("动态变化", "dynamic-change", "[daɪˈnæmɪk tʃeɪndʒ]", "n.", "动态变化"),
        ("多边体系", "multilateralism", "[ˌmʌltɪˈlætərəlɪzəm]", "n.", "多边体系/多边主义"),
        ("强制执行", "enforcement", "[ɪnˈfɔːsmənt]", "n.", "执行机制"),
        ("财富差距", "wealth-gap", "[welθ ɡæp]", "n.", "贫富差距"),
        ("民主制度", "democracy", "[dɪˈmɒkrəsi]", "n.", "民主制度"),
        ("司法系统", "judiciary", "[dʒuːˈdɪʃəri]", "n.", "司法体系"),
        ("最高法院", "Court", "[kɔːt]", "n.", "最高法院"),
        ("自然灾害", "disasters", "[dɪˈzɑːstəz]", "n.", "自然灾害"),
        ("科技战", "tech-war", "[tek wɔː]", "n.", "科技战、科技竞争"),
        ("美元贬值", "dollar-devaluation", "[ˈdɒlə ˌdiːvæljuˈeɪʃn]", "n.", "美元贬值"),
        ("债务循环", "debt-cycle", "[det ˈsaɪkl]", "n.", "债务周期"),
        ("债务", "debt", "[det]", "n.", "债务（负债规模）"),
        ("印钞", "printing", "[ˈprɪntɪŋ]", "n.", "印钞"),
        ("借贷", "borrowing", "[ˈbɒrəʊɪŋ]", "n.", "借贷"),
        ("信用", "credit", "[ˈkredɪt]", "n.", "信用"),
        ("生产力", "productivity", "[ˌprɒdʌkˈtɪvəti]", "n.", "生产率"),
        ("崩溃机制", "collapse", "[kəˈlæps]", "n.", "崩溃机制"),
        ("崩溃", "implosion", "[ɪmˈpləʊʒn]", "n.", "内爆式崩溃"),
        ("秩序", "order", "[ˈɔːdə]", "n.", "秩序"),
        ("体系", "system", "[ˈsɪstəm]", "n.", "体系"),
        ("极化", "polarization", "[ˌpəʊləraɪˈzeɪʃn]", "n.", "极化"),
        ("动荡", "turbulence", "[ˈtɜːbjələns]", "n.", "动荡"),
        ("资产", "assets", "[ˈæsets]", "n.", "资产"),
        ("机遇", "upside", "[ˈʌpsaɪd]", "n.", "上行空间"),
        ("症状", "symptom", "[ˈsɪmptəm]", "n.", "症状"),
        ("逻辑", "logic", "[ˈlɒdʒɪk]", "n.", "逻辑"),
        ("力量", "forces", "[ˈfɔːsɪz]", "n.", "力量"),
        ("机制", "mechanism", "[ˈmekənɪzəm]", "n.", "机制"),
        ("动态", "dynamics", "[daɪˈnæmɪks]", "n.", "动态"),
        ("运作", "operation", "[ˌɒpəˈreɪʃn]", "n.", "运作"),
        ("运转", "operation", "[ˌɒpəˈreɪʃn]", "n.", "运转"),
        ("风险", "peril", "[ˈperəl]", "n.", "风险"),
        ("失衡", "imbalance", "[ɪmˈbæləns]", "n.", "失衡"),
        ("演变", "evolution", "[ˌiːvəˈluːʃn]", "n.", "演变"),
        ("妥协", "compromise", "[ˈkɒmprəmaɪz]", "n.", "妥协"),
        ("僵局", "deadlock", "[ˈdedlɒk]", "n.", "僵局"),
        ("繁荣", "prosperity", "[prɒˈsperəti]", "n.", "繁荣"),
        ("战争", "warfare", "[ˈwɔːfeə]", "n.", "战争"),
        ("发明", "invention", "[ɪnˈvenʃn]", "n.", "发明"),
        ("干旱", "drought", "[draʊt]", "n.", "干旱"),
        ("洪水", "flooding", "[ˈflʌdɪŋ]", "n.", "洪水"),
        ("疫情", "pandemic", "[pænˈdemɪk]", "n.", "大流行病"),
        ("储备", "stockpile", "[ˈstɒkpaɪl]", "n.", "储备"),
        ("关税", "tariff", "[ˈtærɪf]", "n.", "关税"),
        ("制裁", "sanctions", "[ˈsæŋkʃnz]", "n.", "制裁"),
        ("供应链", "supply-chain", "[səˈplaɪ tʃeɪn]", "n.", "供应链"),
        ("全方位的品牌出海解决方案", "go-global-solution", "[ɡəʊ ˈɡləʊbl səˈluːʃn]", "n.", "品牌出海一揽子方案"),
        ("品牌出海解决方案", "brand-go-global-solution", "[brænd ɡəʊ ˈɡləʊbl səˈluːʃn]", "n.", "品牌出海方案"),
        ("国内国际双循环", "dual-circulation", "[djuːəl ˌsɜːkjʊˈleɪʃn]", "n.", "国内国际双循环"),
        ("产业转型升级", "industrial-upgrade", "[ɪnˈdʌstriəl ˈʌpɡreɪd]", "n.", "产业转型升级"),
        ("全球定价权", "global-pricing-power", "[ˈɡləʊbl ˈpraɪsɪŋ ˈpaʊə]", "n.", "全球定价权"),
        ("可持续增长", "sustainable-growth", "[səˈsteɪnəbl ɡrəʊθ]", "n.", "可持续增长"),
        ("财报电话会", "earnings-call", "[ˈɜːnɪŋz kɔːl]", "n.", "财报电话会"),
        ("新发展格局", "new-development-paradigm", "[njuː dɪˈveləpmənt ˈpærədaɪm]", "n.", "新发展格局"),
        ("国内大循环", "domestic-loop", "[dəˈmestɪk luːp]", "n.", "国内大循环"),
        ("战略性布局", "strategic-layout", "[strəˈtiːdʒɪk ˈlaɪaʊt]", "n.", "战略性布局"),
        ("流量红利", "traffic-dividend", "[ˈtræfɪk ˈdɪvɪdənd]", "n.", "流量红利"),
        ("平台生态", "platform-ecosystem", "[ˈplætfɔːm ˈiːkəʊsɪstəm]", "n.", "平台生态"),
        ("半托管", "semi-consignment", "[ˈsemi kənˈsaɪnmənt]", "n.", "半托管（平台模式）"),
        ("全托管", "full-consignment", "[fʊl kənˈsaɪnmənt]", "n.", "全托管（平台履约）"),
        ("产业带", "industrial-belt", "[ɪnˈdʌstriəl belt]", "n.", "产业带"),
        ("中国制造", "made-in-China", "[meɪd ɪn ˈtʃaɪnə]", "n.", "中国制造"),
        ("代工厂", "contract-factory", "[ˈkɒntrækt ˈfæktəri]", "n.", "代工厂"),
        ("价值链", "value-chain", "[ˈvæljuː tʃeɪn]", "n.", "价值链"),
        ("基础设施", "infrastructure", "[ˈɪnfrəstrʌktʃə]", "n.", "基础设施"),
        ("品牌出海", "brand-go-global", "[brænd ɡəʊ ˈɡləʊbl]", "n.", "品牌出海"),
        ("数字化", "digitalization", "[ˌdɪdʒɪtəlaɪˈzeɪʃn]", "n.", "数字化"),
        ("净利润", "net-profit", "[net ˈprɒfɪt]", "n.", "净利润"),
        ("财报", "earnings-report", "[ˈɜːnɪŋz rɪˈpɔːt]", "n.", "财报"),
        ("营收", "revenue", "[ˈrevənjuː]", "n.", "营收"),
        ("赋能", "empowerment", "[ɪmˈpaʊəmənt]", "n.", "赋能"),
        ("跃迁", "step-change", "[step tʃeɪndʒ]", "n.", "跃迁、阶跃"),
        ("跨境", "cross-border", "[krɒs ˈbɔːdə]", "adj.", "跨境"),
        ("合规", "compliance", "[kəmˈplaɪəns]", "n.", "合规"),
        ("代工", "OEM", "[ˌəʊ iː ˈem]", "n.", "代工（OEM）"),
        ("商家", "merchant", "[ˈmɜːtʃənt]", "n.", "商家"),
        ("电商", "e-commerce", "[ˈiː kɒmɜːs]", "n.", "电子商务"),
        ("通胀", "inflation", "[ɪnˈfleɪʃn]", "n.", "通胀"),
        ("利率", "rates", "[reɪts]", "n.", "利率"),
        ("财政", "fiscal", "[ˈfɪskl]", "adj.", "财政的"),
        ("货币", "monetary", "[ˈmʌnɪtri]", "adj.", "货币的"),
        ("霸权", "hegemony", "[hɪˈɡeməni]", "n.", "霸权"),
        ("海峡", "strait", "[streɪt]", "n.", "海峡"),
        ("霍尔木兹", "Hormuz", "[hɔːˈmuːz]", "n.", "霍尔木兹（地名）"),
        ("内战", "strife", "[straɪf]", "n.", "内乱"),
        ("魏玛", "Weimar", "[ˈvaɪmɑː]", "n.", "魏玛"),
        ("元老院", "Senate", "[ˈsenɪt]", "n.", "元老院"),
        ("理想国", "Republic", "[rɪˈpʌblɪk]", "n.", "《理想国》"),
        ("联合国", "UN", "[ˌjuː ˈen]", "n.", "联合国"),
        ("世贸组织", "WTO", "[ˌdʌbəljuː tiː ˈəʊ]", "n.", "世贸组织"),
        ("国际法院", "tribunal", "[traɪˈbjuːnl]", "n.", "国际法院"),
        ("AI", "AI", "[ˌeɪ ˈaɪ]", "n.", "人工智能"),
        ("技术", "technology", "[tekˈnɒlədʒi]", "n.", "技术"),
        ("奇迹", "miracle", "[ˈmɪrəkl]", "n.", "奇迹"),
        ("压力", "headwinds", "[ˈhedwɪndz]", "n.", "逆风"),
        ("阶段", "phase", "[feɪz]", "n.", "阶段"),
        ("诊断", "diagnosis", "[ˌdaɪəɡˈnəʊsɪs]", "n.", "诊断"),
        ("预演", "precursor", "[priːˈkɜːsə]", "n.", "先兆"),
        ("万能药", "panacea", "[ˌpænəˈsiːə]", "n.", "万灵药"),
        ("普通人", "layperson", "[ˈleɪpɜːsn]", "n.", "普通人"),
        ("配置", "allocation", "[ˌæləˈkeɪʃn]", "n.", "配置"),
        ("多元化", "diversification", "[daɪˌvɜːsɪfɪˈkeɪʃn]", "n.", "分散化"),
        ("黄金", "bullion", "[ˈbʊliən]", "n.", "贵金属条块"),
        ("美元", "greenback", "[ˈɡriːnbæk]", "n.", "美元（口语）"),
        ("桥水", "Bridgewater", "[ˈbrɪdʒwɔːtə]", "n.", "桥水基金"),
        ("达利欧", "Dalio", "[ˈdɑːliəʊ]", "n.", "达利欧"),
        ("华尔街见闻", "Wallstreetcn", "[wɔːl striːt siː en]", "n.", "华尔街见闻"),
        ("底线思维", "Dixiansiwei", "[ˌdiːʃiːənˈsɪweɪ]", "n.", "底线思维（媒体名）"),
        ("笔记侠", "Bijixia", "[biː dʒiː ʃiːə]", "n.", "笔记侠（公号名）"),
        ("独立观点", "independent", "[ˌɪndɪˈpendənt]", "adj.", "独立观点"),
        ("立场", "stance", "[stæns]", "n.", "立场"),
        ("韵脚", "rhyme", "[raɪm]", "n.", "韵脚"),
    ],
    key=lambda x: len(x[0]),
    reverse=True,
)

DEFAULT_SOURCE_ACCOUNT = "笔记侠"
DEFAULT_OMIT_SECTIONS_NOTE = (
    "文末带 * 的一句话及参考文献标题以原文为准；本站已省略原推送中的课程推广与矩阵号推荐段落。"
)
DEFAULT_RISK_BLURB = "本文为第三方观点汇编与宏观评论摘录，不构成任何投资建议。"
DEFAULT_RISK_BLURB_SECONDARY = "任何决策请咨询持牌专业人士并以官方披露文件为准。"
VERBATIM_FOOTER_RISK_SECONDARY = (
    "英文标注仅供学习，释义为编者据语境所给，与原文作者用语未必一一对应。"
)

_POST_SOURCE_FOOTER_OUTER = (
    'style="margin:1.5rem 0;padding:1.25rem;border:2px solid #b91c1c;'
    "background:#fef2f2;border-radius:8px;font-size:0.95rem;line-height:1.65;"
    '"'
)
_POST_SOURCE_FOOTER_RISK_BOX = (
    'style="border-left:4px solid #667eea;padding:0.75rem 1rem;margin-top:1rem;'
    "background:#f8f9ff;font-size:0.9rem;line-height:1.6;"
    '"'
)


def post_source_footer_html(
    *,
    footer_template: str,
    url: str,
    source_account: str,
    omit_sections_note: str,
    risk_blurb: str,
    risk_blurb_secondary: str,
    source_author_display: str = "",
    footer_derivative_mp_unknown: bool = False,
) -> str:
    """外源稿「来源与版权」块；与 posts/2026-04-01-private-fund-ai-hiring-threshold.html 等版式对齐。"""
    sa_plain = source_account.strip()
    sa = html.escape(sa_plain or "微信公众号")
    omit_esc = html.escape(omit_sections_note)
    risk_esc = html.escape(risk_blurb)
    risk2_esc = html.escape(risk_blurb_secondary)
    url_esc = html.escape(url, quote=True)
    url_vis = html.escape(url)
    title_p = (
        '<p style="margin:0 0 0.65rem 0;font-weight:700;color:#991b1b;font-size:1.05rem;">'
        "来源与版权</p>"
    )

    if footer_template == "derivative":
        if footer_derivative_mp_unknown or not sa_plain:
            intro = (
                "<p style=\"margin:0 0 0.65rem 0;\">本条为 MingoX 对第三方公开推文的衍生整理与双语重写，"
                "事实脉络与要点梳理来自下方<strong>原文固定链接</strong>所指向的微信公众号文章；"
                "账号名称与作者署名以微信页面展示为准。</p>"
            )
        else:
            auth = source_author_display.strip()
            auth_frag = (
                f"、界面显示作者为<strong>「{html.escape(auth)}」</strong>" if auth else ""
            )
            intro = (
                f"<p style=\"margin:0 0 0.65rem 0;\">本条为 MingoX 对第三方公开推文的衍生整理与双语重写，"
                f"事实脉络与部分论点梳理自微信公众号<strong>「{sa}」</strong>刊载{auth_frag}的文章。</p>"
            )
        return f"""
                <div class="post-source-footer" {_POST_SOURCE_FOOTER_OUTER}>
                    {title_p}
                    {intro}
                    <p style="margin:0 0 0.65rem 0;"><strong>原文固定链接：</strong><a href="{url_esc}" rel="noopener noreferrer" target="_blank">{url_vis}</a></p>
                    <p style="margin:0 0 0.65rem 0;">著作权与转载规则以微信帐号、原作者及腾讯平台公示为准；商业性转载、摘编或再发布须自行取得权利人许可。本站不代为授权，亦不主张对原文的任何权利。</p>
                    <p style="margin:0 0 0.65rem 0;">以上为 MingoX 对公开报道要点的文摘扩写，供双语阅读与词汇学习；如需引用原文论点或段落，请以微信原文为准并遵守平台与权利人的合规要求。</p>
                    <div {_POST_SOURCE_FOOTER_RISK_BOX}>
                        <p style="margin:0 0 0.5rem 0;"><strong>风险提示：</strong>{risk_esc}</p>
                        <p style="margin:0;">{risk2_esc}</p>
                    </div>
                </div>
"""

    return f"""
                <div class="post-source-footer" {_POST_SOURCE_FOOTER_OUTER}>
                    {title_p}
                    <p style="margin:0 0 0.65rem 0;">正文汉字与标点尽量保持微信公众号「{sa}」所刊原文一致，本站仅添加用于语言学习的英文词汇标注（<code>word-block</code>），不构成对原文的改写或编辑。</p>
                    <p style="margin:0 0 0.65rem 0;"><strong>原文固定链接：</strong><a href="{url_esc}" rel="noopener noreferrer" target="_blank">{url_vis}</a></p>
                    <p style="margin:0 0 0.65rem 0;">著作权归原作者及微信公众平台所有；商业转载、摘编须自行取得权利人许可。</p>
                    <p style="margin:0 0 0.65rem 0;">{omit_esc}</p>
                    <div {_POST_SOURCE_FOOTER_RISK_BOX}>
                        <p style="margin:0 0 0.5rem 0;"><strong>风险提示：</strong>{risk_esc}</p>
                        <p style="margin:0;">{risk2_esc}</p>
                    </div>
                </div>
"""


def extract_ps(html: str) -> list[str]:
    class PExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.chunks: list[str] = []
            self._buf: list[str] = []
            self._in_skip = False
            self._skip_depth = 0

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag in ("script", "style"):
                self._in_skip = True
                self._skip_depth += 1
            if self._in_skip:
                return
            if tag == "br":
                self._buf.append("\n")
            if tag == "p":
                self._buf = []

        def handle_endtag(self, tag: str) -> None:
            if self._in_skip:
                if tag in ("script", "style"):
                    self._skip_depth -= 1
                    if self._skip_depth <= 0:
                        self._in_skip = False
                        self._skip_depth = 0
                return
            if tag == "p":
                t = "".join(self._buf).strip()
                if t and len(t) > 10:
                    self.chunks.append(t)
                self._buf = []

        def handle_data(self, data: str) -> None:
            if not self._in_skip:
                self._buf.append(data)

    p = PExtractor()
    p.feed(html)
    return p.chunks


# 微信编辑器常见文末运营句，尽量不并进正文 MD
_WECHAT_LEAF_SKIP_SUBSTR = (
    "点赞关注",
    "热点视频推荐",
    "成为会员",
    "巴伦中文网",
    "星标",
    "我知道你",
    "在看哦",
    "钛媒体视频号",
    "第一时间收到推送",
)


def extract_wechat_plain_paragraphs(html: str) -> list[str]:
    """
    按 DOM 顺序收集 #js_content 内所有可见文本（含非 span-leaf 的姓名高亮等），
    再按句末标点切段并打包成若干段，避免只抽 leaf 时断句、丢字。
    """

    class _TextCollector(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []
            self._skip_depth = 0

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag in ("script", "style"):
                self._skip_depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style") and self._skip_depth > 0:
                self._skip_depth -= 1

        def handle_data(self, data: str) -> None:
            if self._skip_depth == 0:
                self.parts.append(data)

    tc = _TextCollector()
    tc.feed(html)
    raw = "".join(tc.parts)
    raw = re.sub(r"\s+", " ", raw).strip()
    if not raw:
        return []

    sentences: list[str] = []
    buf: list[str] = []
    for ch in raw:
        buf.append(ch)
        if ch in "。！？；":
            s = "".join(buf).strip()
            if s:
                sentences.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        sentences.append(tail)

    paras: list[str] = []
    acc: list[str] = []
    acc_len = 0
    for s in sentences:
        s = re.sub(r"^[▎▶◆●\s]+", "", s.strip())
        if any(x in s for x in _WECHAT_LEAF_SKIP_SUBSTR):
            continue
        if "#这事钛大了" in s or (s.startswith("#") and len(s) > 30):
            continue
        acc.append(s)
        acc_len += len(s)
        if acc_len >= 220:
            paras.append("".join(acc))
            acc = []
            acc_len = 0
    if acc:
        paras.append("".join(acc))

    return [p.strip() for p in paras if len(p.strip()) > 40]


def extract_wechat_span_leaf_paragraphs(html: str) -> list[str]:
    """
    许多公众号正文写在 <section> + <span leaf> 里，纯 extract_ps 只会捡到文末 <p> 广告。
    从 span leaf 抽文本并按句长合并为段落，供 01-source.md 使用。
    """
    h = re.sub(r"(?is)<br\s*/?>", "\n", html)
    pieces: list[str] = []
    for m in re.finditer(r"<span\s+leaf[^>]*>([\s\S]*?)</span>", h, flags=re.I):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        t = inner.replace("\xa0", " ").strip()
        if len(t) < 8:
            continue
        if "#这事钛大了" in t or (t.startswith("#") and len(t) > 35):
            continue
        if any(s in t[:24] for s in _WECHAT_LEAF_SKIP_SUBSTR):
            continue
        pieces.append(t)

    # 不按句硬合并：微信里相邻 leaf 未必同段，合并易把 CEO 引言与后文粘成一句
    return [p.strip() for p in pieces if len(p.strip()) > 12]


def split_sentences(text: str) -> list[str]:
    """Split on 。！？； keep delimiter on sentence."""
    if not text.strip():
        return []
    out: list[str] = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch in "。！？；":
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


def pick_keyword(body: str) -> tuple[str, str, str, str, str] | None:
    """Return (zh_span, en, ipa, pos, gloss): longest zh in body; tie-break by leftmost find."""
    best: tuple[int, int, str, str, str, str, str] | None = None
    for zh, en, ipa, pos, gloss in KEYWORDS:
        idx = body.find(zh)
        if idx < 0:
            continue
        cand = (-len(zh), idx, zh, en, ipa, pos, gloss)
        if best is None or cand < best:
            best = cand
    if best is None:
        return None
    _, _, zh, en, ipa, pos, gloss = best
    return zh, en, ipa, pos, gloss


def annotate_sentence(sent: str) -> str:
    sent = sent.strip()
    if not sent:
        return ""
    m = re.search(r"([。！？；])$", sent)
    punct = m.group(1) if m else ""
    body = sent[:-1] if m else sent
    body = body.strip()
    if not body:
        return sent
    kw = pick_keyword(body)
    if kw is None:
        return html.escape(body) + (html.escape(punct) if punct else "")
    zh_m, en, ipa, pos, gloss = kw
    if " " in en:
        raise ValueError(f"english-word must be one token: {en!r}")
    block = (
        f'<span class="word-block"><span class="english-word">{html.escape(en)}</span>'
        f'<span class="word-info">{html.escape(ipa)} {html.escape(pos)} {html.escape(gloss)}</span></span>'
    )
    if zh_m:
        idx = body.find(zh_m)
        if idx < 0:
            safe_body = html.escape(body)
            return safe_body + block + html.escape(punct) if punct else safe_body + block
        before, mid, after = body[:idx], body[idx : idx + len(zh_m)], body[idx + len(zh_m) :]
        inner = (
            html.escape(before)
            + f'<span class="word-anchor">{html.escape(mid)}</span>'
            + block
            + html.escape(after)
        )
    else:
        inner = html.escape(body) + block
    return inner + html.escape(punct) if punct else inner


def annotate_paragraph(para: str) -> str:
    sents = split_sentences(para.replace("\r", ""))
    if not sents:
        return f"<p>{html.escape(para)}</p>"
    parts = [annotate_sentence(s) for s in sents]
    inner = "".join(parts)
    return f"<p>{inner}</p>"


def slice_body_chunks(
    chunks: list[str],
    end_marker: str | None,
    paragraph_cap: int | None,
) -> list[str]:
    """Truncate crawl paragraphs: prefer marker in text; else optional cap (safety)."""
    if end_marker:
        for i, c in enumerate(chunks):
            if end_marker in c:
                return chunks[: i + 1]
    if paragraph_cap is not None:
        return chunks[:paragraph_cap]
    return chunks


def extract_vocab_rows(paras_html: str) -> list[tuple[str, str, str, str]]:
    seen: set[str] = set()
    rows: list[tuple[str, str, str, str]] = []
    for m in re.finditer(
        r'<span class="english-word">([^<]+)</span><span class="word-info">(\[[^\]]+\])\s+(\S+)\s+([^<]+)</span>',
        paras_html,
    ):
        en, ipa, pos, gloss = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        key = en.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append((en.strip(), ipa, pos, gloss))
    return rows


def vocab_tbody_html(paras_html: str) -> str:
    return "\n".join(
        f"                        <tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{html.escape(d)}</td></tr>"
        for a, b, c, d in extract_vocab_rows(paras_html)
    )


def build_post_html(
    *,
    paras_html: str,
    tbody: str,
    title_zh: str,
    title_en: str,
    url: str,
    meta_description: str,
    source_account: str = DEFAULT_SOURCE_ACCOUNT,
    omit_sections_note: str = DEFAULT_OMIT_SECTIONS_NOTE,
    risk_blurb: str = DEFAULT_RISK_BLURB,
    title_emoji: str = "📈",
    include_source_footer: bool = True,
    footer_template: str = "verbatim",
    source_author_display: str = "",
    footer_derivative_mp_unknown: bool = False,
    risk_blurb_secondary: str | None = None,
) -> str:
    tzh, ten = html.escape(title_zh), html.escape(title_en)
    rb2 = risk_blurb_secondary
    if rb2 is None:
        rb2 = (
            VERBATIM_FOOTER_RISK_SECONDARY
            if footer_template == "verbatim"
            else DEFAULT_RISK_BLURB_SECONDARY
        )
    footer_block = ""
    if include_source_footer:
        footer_block = post_source_footer_html(
            footer_template=footer_template,
            url=url,
            source_account=source_account,
            omit_sections_note=omit_sections_note,
            risk_blurb=risk_blurb,
            risk_blurb_secondary=rb2,
            source_author_display=source_author_display,
            footer_derivative_mp_unknown=footer_derivative_mp_unknown,
        )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{tzh} | {ten} | MingoX</title>
    <meta name="description" content="{html.escape(meta_description, quote=True)}">
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="../" class="logo">🎙️ MingoX</a>
            <div class="nav-links">
                <a href="../">首页</a>
                <a href="../about.html">关于</a>
            </div>
        </div>
    </nav>

    <main class="main-content">
        <div class="container">
            <div class="card">
                <article class="post-content">
                    <h1>{html.escape(title_emoji)} {tzh}<br><small class="title-en">{ten}</small></h1>

{paras_html}
                </article>
{footer_block}
                <div class="subtitle">📖 重点词汇</div>
                <div class="vocab-table-wrap">
                <table class="vocab-table">
                    <thead>
                        <tr><th>词汇</th><th>音标</th><th>词性</th><th>释义</th></tr>
                    </thead>
                    <tbody>
{tbody}
                    </tbody>
                </table>
                </div>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <a href="../" style="color: #667eea; text-decoration: none;">← 返回首页</a>
                </div>
            </div>
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 MingoX | Multimedia Post in Mixed Languages | Powered by Gitee Pages</p>
        </div>
    </footer>

    <script src="../js/main.js"></script>
</body>
</html>
"""
