#!/usr/bin/env python3
"""
Shared library: WeChat/HTML 正文抽取、成稿页 HTML 壳、词汇表反扫（仅当正文含 word-block 时）。

`mingox build`：若草稿目录存在 `llm_annotations.json`，经 `annotate_merge` 注入 `word-block`；否则段落仅为转义 `<p>`。
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

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


def article_source_banner_html(*, include_source_footer: bool, source_account: str) -> str:
    """在 h1 与首段之间插入一句「出处提示」（`post-source-banner`）。

    完整著作权说明、原文链接与风险提示仍在 `post_source_footer_html` 生成的
    `post-source-footer` 中，且位于 `</article>` 之后（见 docs/EDITORIAL.md「外源素材与版权声明」）。
    文首横幅仅解决「读者扫一眼正文不见转载说明」的体验问题，**不替代**文末版权块。
    """
    acc = (source_account or "").strip()
    if not include_source_footer or not acc:
        return ""
    esc = html.escape(acc)
    return (
        '<p class="post-source-banner" style="font-size:0.9rem;color:#444;margin:0 0 1.15rem 0;'
        "border-left:3px solid #b91c1c;padding-left:0.75rem;line-height:1.55;\">"
        f"<strong>出处提示：</strong>本文来自微信公众号「{esc}」。"
        "<strong>完整著作权说明、风险提示与原文固定链接</strong>见文末「来源与版权」版块。</p>\n\n"
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
                    <p style="margin:0 0 0.65rem 0;">以上为 MingoX 对公开报道要点的文摘扩写，供双语阅读；如需引用原文论点或段落，请以微信原文为准并遵守平台与权利人的合规要求。</p>
                    <div {_POST_SOURCE_FOOTER_RISK_BOX}>
                        <p style="margin:0 0 0.5rem 0;"><strong>风险提示：</strong>{risk_esc}</p>
                        <p style="margin:0;">{risk2_esc}</p>
                    </div>
                </div>
"""

    return f"""
                <div class="post-source-footer" {_POST_SOURCE_FOOTER_OUTER}>
                    {title_p}
                    <p style="margin:0 0 0.65rem 0;">正文汉字与标点尽量保持微信公众号「{sa}」所刊原文一致；本站可添加用于语言学习的英文词汇标注（<code>word-block</code>），不构成对原文的改写或编辑。</p>
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


def split_sentences(text: str) -> list[str]:
    """按 。！？； 切句，标点在句末保留。"""
    if not text.strip():
        return []
    out: list[str] = []
    buf: list[str] = []
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


def sentence_body_and_punct(sent: str) -> tuple[str, str]:
    sent = sent.strip()
    m = re.search(r"([。！？；])$", sent)
    punct = m.group(1) if m else ""
    body = sent[:-1] if m else sent
    return body.strip(), punct


def escape_plain_sentence(sent: str) -> str:
    sent = sent.strip()
    if not sent:
        return ""
    body, punct = sentence_body_and_punct(sent)
    if not body:
        return html.escape(sent)
    return html.escape(body) + (html.escape(punct) if punct else "")


_QUOTE_PULL_PAIRS: tuple[tuple[str, str], ...] = (("「", "」"), ("『", "』"))


def _closing_bracket_before_english(before_zh: str, after_zh: str) -> tuple[str, str]:
    if not after_zh:
        return "", after_zh
    left = before_zh.rstrip()
    first = after_zh[0]
    for open_ch, close_ch in _QUOTE_PULL_PAIRS:
        if first == close_ch and left.endswith(open_ch):
            return close_ch, after_zh[1:]
    return "", after_zh


def render_annotated_sentence(
    sent: str,
    zh_m: str,
    en: str,
    ipa: str,
    pos: str,
    gloss: str,
    *,
    underline: str | None = None,
) -> str:
    sent = sent.strip()
    if not sent:
        return ""
    body, punct = sentence_body_and_punct(sent)
    if not body:
        return html.escape(sent)
    if " " in en.strip():
        raise ValueError(f"english-word must be one token: {en!r}")
    if zh_m not in body:
        return escape_plain_sentence(sent)
    ul_raw = (underline or "").strip()
    ul = ul_raw if ul_raw else zh_m
    if ul not in zh_m:
        raise ValueError(f"underline must be substring of zh: {underline!r} not in {zh_m!r}")
    u_off = zh_m.index(ul)
    block = (
        f'<span class="word-block"><span class="english-word">{html.escape(en)}</span>'
        f'<span class="word-info">{html.escape(ipa)} {html.escape(pos)} {html.escape(gloss)}</span></span>'
    )
    idx = body.find(zh_m)
    before = body[:idx]
    mid_full = body[idx : idx + len(zh_m)]
    after = body[idx + len(zh_m) :]
    pre = mid_full[:u_off]
    mid_u = mid_full[u_off : u_off + len(ul)]
    post = mid_full[u_off + len(ul) :]
    closing_before_en = ""
    tail_after_zh = after
    if not post:
        closing_before_en, tail_after_zh = _closing_bracket_before_english(before + pre, after)
    inner = (
        html.escape(before)
        + html.escape(pre)
        + '<span class="word-annot">'
        + f'<span class="word-anchor">{html.escape(mid_u)}</span>'
        + html.escape(closing_before_en)
        + block
        + "</span>"
        + html.escape(post)
        + html.escape(tail_after_zh)
    )
    return inner + html.escape(punct) if punct else inner


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
    banner = article_source_banner_html(
        include_source_footer=include_source_footer,
        source_account=source_account,
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
{banner}{paras_html}
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
