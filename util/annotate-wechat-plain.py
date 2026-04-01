#!/usr/bin/env python3
"""
Read WeChat js_content.html paragraphs; keep Chinese verbatim, append one word-block per sentence (。！？；).
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

# (substring in sentence body, english, ipa, pos, gloss) — longer keys first
KEYWORDS: list[tuple[str, str, str, str, str]] = sorted(
    [
        ("世界储备货币", "reserve currency", "[rɪˈzɜːv ˈkʌrənsi]", "n.", "储备货币"),
        ("偿债支出", "debt service", "[det ˈsɜːvɪs]", "n.", "偿债支出"),
        ("供需失衡", "disequilibrium", "[ˌdɪsiːkwɪˈlɪbriəm]", "n.", "失衡"),
        ("地缘政治", "geopolitics", "[ˌdʒiːəʊpəˈlɪtɪks]", "n.", "地缘政治"),
        ("政治极化", "polarization", "[ˌpəʊləraɪˈzeɪʃn]", "n.", "政治极化"),
        ("民粹主义", "populism", "[ˈpɒpjəlɪzəm]", "n.", "民粹主义"),
        ("专制统治", "autocracy", "[ɔːˈtɒkrəsi]", "n.", "专制统治"),
        ("货币秩序", "monetary order", "[ˈmʌnɪtri ˈɔːdə]", "n.", "货币秩序"),
        ("货币体系", "monetary system", "[ˈmʌnɪtri ˈsɪstəm]", "n.", "货币体系"),
        ("资本市场", "capital markets", "[ˈkæpɪtl ˈmɑːkɪts]", "n.", "资本市场"),
        ("财政窟窿", "fiscal hole", "[ˈfɪskl həʊl]", "n.", "财政缺口"),
        ("储备货币", "reserve currency", "[rɪˈzɜːv ˈkʌrənsi]", "n.", "储备货币"),
        ("大周期", "mega-cycle", "[ˈmeɡə saɪkl]", "n.", "大周期"),
        ("秩序崩溃", "breakdown of order", "[ˈbreɪkdaʊn]", "n.", "秩序崩解"),
        ("黄金暴涨", "bullion rally", "[ˈbʊliən ˈræli]", "n.", "金价急涨"),
        ("地缘博弈", "geostrategic contest", "[ˌdʒiːəʊstrəˈtiːdʒɪk ˈkɒntest]", "n.", "地缘博弈"),
        ("周期透镜", "cyclical lens", "[ˈsaɪklɪkl lenz]", "n.", "周期视角"),
        ("国内政治", "domestic politics", "[dəˈmestɪk ˈpɒlɪtɪks]", "n.", "国内政治"),
        ("多边体系", "multilateral system", "[ˌmʌltɪˈlætərəl ˈsɪstəm]", "n.", "多边体系"),
        ("强制执行", "enforcement", "[ɪnˈfɔːsmənt]", "n.", "执行机制"),
        ("财富差距", "wealth gap", "[welθ ɡæp]", "n.", "贫富差距"),
        ("民主制度", "democratic institutions", "[ˌdeməˈkrætɪk ɪnstɪˈtjuːʃnz]", "n.", "民主制度"),
        ("司法系统", "judiciary", "[dʒuːˈdɪʃəri]", "n.", "司法体系"),
        ("最高法院", "Supreme Court", "[suˈpriːm kɔːt]", "n.", "最高法院"),
        ("自然灾害", "natural disasters", "[ˈnætʃrəl dɪˈzɑːstəz]", "n.", "自然灾害"),
        ("科技战", "tech war", "[tek wɔː]", "n.", "科技竞争"),
        ("美元贬值", "dollar devaluation", "[ˈdɒlə ˌdiːvæljuˈeɪʃn]", "n.", "美元贬值"),
        ("债务循环", "debt cycle", "[det ˈsaɪkl]", "n.", "债务周期"),
        ("债务", "indebtedness", "[ɪnˈdetɪdnəs]", "n.", "负债程度"),
        ("印钞", "money printing", "[ˈmʌni ˈprɪntɪŋ]", "n.", "印钞"),
        ("借贷", "borrowing", "[ˈbɒrəʊɪŋ]", "n.", "借贷"),
        ("信用", "credit", "[ˈkredɪt]", "n.", "信用"),
        ("生产力", "productivity", "[ˌprɒdʌkˈtɪvəti]", "n.", "生产率"),
        ("崩溃机制", "collapse mechanism", "[kəˈlæps ˈmekənɪzəm]", "n.", "崩溃机制"),
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
        ("供应链", "supply lines", "[səˈplaɪ laɪnz]", "n.", "供应线"),
        ("通胀", "inflation", "[ɪnˈfleɪʃn]", "n.", "通胀"),
        ("利率", "interest rates", "[ˈɪntrəst reɪts]", "n.", "利率"),
        ("财政", "fiscal", "[ˈfɪskl]", "adj.", "财政的"),
        ("货币", "monetary", "[ˈmʌnɪtri]", "adj.", "货币的"),
        ("霸权", "hegemony", "[hɪˈɡeməni]", "n.", "霸权"),
        ("海峡", "strait", "[streɪt]", "n.", "海峡"),
        ("霍尔木兹", "Hormuz", "[hɔːˈmuːz]", "n.", "霍尔木兹（地名）"),
        ("内战", "civil strife", "[ˈsɪvl straɪf]", "n.", "内乱"),
        ("魏玛", "Weimar", "[ˈvaɪmɑː]", "n.", "魏玛"),
        ("元老院", "the Senate", "[ðə ˈsenɪt]", "n.", "元老院"),
        ("理想国", "Republic", "[rɪˈpʌblɪk]", "n.", "《理想国》"),
        ("联合国", "United Nations", "[juːˈnaɪtɪd ˈneɪʃnz]", "n.", "联合国"),
        ("世贸组织", "WTO", "[ˌdʌbəljuː tiː ˈəʊ]", "n.", "世贸组织"),
        ("国际法院", "World Court", "[wɜːld kɔːt]", "n.", "国际法院"),
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
        ("底线思维", "Di xian si wei", "[dɪ ʃiːən sɪ weɪ]", "n.", "底线思维（媒体名）"),
        ("笔记侠", "Bi Ji Xia", "[biː dʒiː ʃiːə]", "n.", "笔记侠（公号名）"),
        ("独立观点", "independent view", "[ˌɪndɪˈpendənt vjuː]", "n.", "独立观点"),
        ("立场", "stance", "[stæns]", "n.", "立场"),
        ("韵脚", "rhyme", "[raɪm]", "n.", "韵脚"),
    ],
    key=lambda x: len(x[0]),
    reverse=True,
)

FALLBACK = [
    ("paradigm", "[ˈpærədaɪm]", "n.", "范式"),
    ("dynamics", "[daɪˈnæmɪks]", "n.", "动态"),
    ("inflection", "[ɪnˈflekʃn]", "n.", "拐点"),
    ("cleavage", "[ˈkliːvɪdʒ]", "n.", "裂痕"),
    ("entropy", "[ˈentrəpi]", "n.", "熵增、失序"),
    ("contingency", "[kənˈtɪndʒənsi]", "n.", "变数"),
    ("vortex", "[ˈvɔːteks]", "n.", "漩涡"),
    ("catalyst", "[ˈkætəlɪst]", "n.", "催化剂"),
    ("overhang", "[ˈəʊvəhæŋ]", "n.", "悬顶压力"),
    ("fracture", "[ˈfræktʃə]", "n.", "断裂"),
]


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


def pick_keyword(body: str) -> tuple[str, str, str, str] | None:
    for zh, en, ipa, pos, gloss in KEYWORDS:
        if zh in body:
            return en, ipa, pos, gloss
    return None


def annotate_sentence(sent: str, fb_i: list[int]) -> str:
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
        i = fb_i[0] % len(FALLBACK)
        fb_i[0] += 1
        en, ipa, pos, gloss = FALLBACK[i]
    else:
        en, ipa, pos, gloss = kw
    block = (
        f'<span class="word-block"><span class="english-word">{html.escape(en)}</span>'
        f'<span class="word-info">{html.escape(ipa)} {html.escape(pos)} {html.escape(gloss)}</span></span>'
    )
    safe_body = html.escape(body)
    return safe_body + block + html.escape(punct) if punct else safe_body + block


def annotate_paragraph(para: str) -> str:
    sents = split_sentences(para.replace("\r", ""))
    if not sents:
        return f"<p>{html.escape(para)}</p>"
    fb_i = [0]
    parts = [annotate_sentence(s, fb_i) for s in sents]
    inner = "".join(parts)
    return f"<p>{inner}</p>"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "util" / ".crawl-output" / "wechat-IO6QRr6h-js_content.html"
    html_in = src.read_text(encoding="utf-8")
    chunks = extract_ps(html_in)
    # 正文：至「不代表笔记侠立场」止，去掉文末卖课与推荐
    end = 95
    for i, c in enumerate(chunks):
        if "不代表笔记侠立场" in c:
            end = i + 1
            break
    body_chunks = chunks[:end]

    paras_html = "\n\n".join(annotate_paragraph(c) for c in body_chunks)

    # Collect vocab in order of first appearance in generated body
    seen: set[str] = set()
    vocab_rows: list[tuple[str, str, str, str]] = []
    # Re-scan generated HTML for english-word
    for m in re.finditer(
        r'<span class="english-word">([^<]+)</span><span class="word-info">(\[[^\]]+\])\s+(\S+)\s+([^<]+)</span>',
        paras_html,
    ):
        en, ipa, pos, gloss = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        key = en.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        vocab_rows.append((en.strip(), ipa, pos, gloss))

    tbody = "\n".join(
        f"                        <tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{html.escape(d)}</td></tr>"
        for a, b, c, d in vocab_rows
    )

    title_zh = "达利欧重磅预警：美国，走向衰落"
    title_en = "Dalio's Warning: America in Decline"
    url = "https://mp.weixin.qq.com/s/IO6QRr6hFJc5iKpFRhVw_A"

    out = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{title_zh} | {title_en} | MingoX</title>
    <meta name="description" content="瑞·达利欧宏观长文：美国「大周期」第五阶段与五大力量；正文保留微信原文，仅作词汇标注；附来源链接。">
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
                    <h1>📈 {title_zh}<br><small class="title-en">{title_en}</small></h1>

{paras_html}
                </article>

                <div class="post-source-footer" style="margin:1.5rem 0;padding:1.25rem;border:2px solid #b91c1c;background:#fef2f2;border-radius:8px;font-size:0.95rem;line-height:1.65;">
                    <p style="margin:0 0 0.65rem 0;font-weight:700;color:#991b1b;font-size:1.05rem;">来源与版权</p>
                    <p style="margin:0 0 0.65rem 0;">正文汉字与标点尽量保持微信公众号「笔记侠」所刊原文一致，本站仅添加用于语言学习的英文词汇标注（<code>word-block</code>），不构成对原文的改写或编辑。</p>
                    <p style="margin:0 0 0.65rem 0;"><strong>原文固定链接：</strong><a href="{url}" rel="noopener noreferrer" target="_blank">{url}</a></p>
                    <p style="margin:0 0 0.65rem 0;">著作权归原作者及微信公众平台所有；商业转载、摘编须自行取得权利人许可。</p>
                    <p style="margin:0 0 0.65rem 0;">文末带 * 的一句话及参考文献标题以原文为准；本站已省略原推送中的课程推广与矩阵号推荐段落。</p>
                    <div style="border-left:4px solid #667eea;padding:0.75rem 1rem;margin-top:1rem;background:#f8f9ff;font-size:0.9rem;line-height:1.6;">
                        <p style="margin:0 0 0.5rem 0;"><strong>风险提示：</strong>本文为第三方观点汇编与宏观评论摘录，不构成任何投资建议。</p>
                        <p style="margin:0;">英文标注仅供学习，释义为编者据语境所给，与原文作者用语未必一一对应。</p>
                    </div>
                </div>

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
    out_path = root / "posts" / "2026-04-02-dalio-warning-america-decline.html"
    out_path.write_text(out, encoding="utf-8")
    print("wrote", out_path, "paragraphs", len(body_chunks), "vocab", len(vocab_rows))


if __name__ == "__main__":
    main()
