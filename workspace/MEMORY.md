# MEMORY.md - Long-term Memory

## MX Deploy (MingoX 部署流程)

**触发指令:** `MX deploy` 或 `MX <url>`

**项目位置:** `/workspace/projects/workspace/MingoX/news`

**部署流程:**
1. 检查 git 状态，提交未提交的更改
2. 推送到 Gitee: `git push origin master`
3. 部署到 EdgeOne Pages:
   ```bash
   export EDGEONE_TOKEN="nErJUE/2bCEGv96OAhb6FOBYThbqh+FzKmzXoT2ptXs="
   cd MingoX/news && edgeone pages deploy -n mingox -t "$EDGEONE_TOKEN"
   ```

**令牌位置:** `/workspace/projects/.env.mingox`

**站点链接:**
- EdgeOne: https://mingox-dzlbtybw.edgeone.cool（**必须带 token 参数**，私有访问）
- Gitee Pages: https://siglea.gitee.io/news

**注意事项:**
- `.edgeone/` 目录是构建产物，已在 git 中移除，不需要提交
- 如果 git push 有冲突，先 pull --rebase 解决
- EdgeOne 部署优先级高于 Gitee（更快）
- **⚠️ EdgeOne 项目访问权限必须设为「需要身份验证」（私有），分享链接时必须完整复制 CLI 输出的带 token URL**

**完整文档:** `MINGOX_COMPLETE_REPORT.md`

---

## MingoX 内容创作助手 (2026-04-01 升级)

**位置:** `/workspace/projects/workspace/MingoX/news/scripts/`

### 新增工具脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `check-content.sh` | 内容合规检查 | `./scripts/check-content.sh` |
| `create-post.sh` | 生成文章模板 | `./scripts/create-post.sh -t "标题" -e "English" -d 2026-04-01` |
| `update-index.sh` | 更新首页列表 | `./scripts/update-index.sh -f posts/xxx.html -s "摘要"` |
| `deploy.sh` | 一键部署 | `./scripts/deploy.sh` |

### 能力升级

**1. 自动化内容检查**
- 相邻 word-block 违规检测
- HTML 结构完整性检查
- 词汇表与正文一致性检查

**2. 文章创建辅助**
- 自动生成符合规范的 HTML 模板
- 预置词汇标注格式示例
- 外源稿来源说明模板

**3. 首页管理**
- 自动提取文章元数据
- 生成规范的列表项 HTML
- 自动插入到正确位置

**4. 一键部署**
- 整合检查 -> 提交 -> 推送 -> 部署全流程
- 自动检测 EdgeOne Token
- 彩色输出部署状态

### 内容规范要点

**词汇标注格式:**
```html
<span class="word-block"><span class="english-word">word</span><span class="word-info">[音标] 词性. 释义</span></span>
```

**严禁标注的词汇:**
- 简单日常词: yes, good, big, get, make, close, drop, go, see, take
- 高中常见词: price, risk, trade, market, meeting, policy, data, window
- chain 不单独标注（用 logistics 替代）

**密度要求:**
- 每句（以。！？；断句）至少1处 word-block
- 相邻 word-block 之间必须有中文/标点间隔
- 词汇表与正文标注一一对应

**参考范文:**
- 政经外交: `posts/2026-03-29-china-g7-europe-market.html`
- 财经市场: `posts/2026-03-29-gold-price-analysis.html`
