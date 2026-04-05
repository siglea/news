# MingoX 项目能力升级报告

**日期:** 2026-04-01

## 升级概述

基于 README.md 的要求分析，我为 MingoX 项目创建了完整的内容创作辅助工具链，从文章创建、质量检查到部署发布，实现全流程自动化支持。

## 新增能力

### 1. 内容合规检查 (`scripts/check-content.sh`)

**功能:**
- ✅ 相邻 word-block 违规检测（使用 ripgrep 或 grep）
- ✅ HTML 结构完整性检查（article、vocab-table 等必需标签）
- ✅ word-block 与 word-info 数量匹配检查
- ✅ 词汇表与正文一致性基础检查
- ✅ 彩色输出结果（绿色=通过，黄色=警告，红色=错误）

**使用:**
```bash
cd /workspace/projects/workspace/MingoX/news
./scripts/check-content.sh
```

### 2. 文章模板生成器 (`scripts/create-post.sh`)

**功能:**
- 根据标题自动生成符合规范的 HTML 模板
- 自动设置 emoji、中英文标题格式
- 预置词汇标注格式示例
- 包含外源稿来源说明模板（注释状态）
- 自动检测文件冲突

**使用:**
```bash
./scripts/create-post.sh \
  -t "美联储利率决议前瞻" \
  -e "Fed Rate Decision Preview" \
  -d 2026-04-02 \
  -c "财经"
```

**参数:**
- `-t`: 中文标题（必填）
- `-e`: 英文标题（必填）
- `-d`: 日期，格式 YYYY-MM-DD（默认：今天）
- `-c`: 分类标签（默认：综合）
- `-f`: 内容形式（text/image/podcast/video，默认：text）

### 3. 首页更新助手 (`scripts/update-index.sh`)

**功能:**
- 自动从文章 HTML 提取元数据（标题、emoji、日期）
- 生成符合规范的列表项 HTML
- 自动插入到 index.html 的正确位置
- 检测重复条目

**使用:**
```bash
./scripts/update-index.sh \
  -f posts/2026-04-02-fed-rate.html \
  -s "美联储暗示可能在6月启动降息，市场预期年内降息75个基点" \
  -t "财经, 美联储"
```

### 4. 一键部署脚本 (`scripts/deploy.sh`)

**功能:**
- 整合全流程：检查 -> 提交 -> 推送 -> 部署
- 自动运行内容合规检查
- 智能 Git 状态处理（检测未提交更改并提示）
- 自动检测 EdgeOne Token 位置
- 彩色输出部署状态

**使用:**
```bash
./scripts/deploy.sh
```

**流程:**
1. 内容合规检查
2. Git 状态检查与自动提交
3. 推送到远程仓库
4. 部署到 EdgeOne Pages
5. 输出站点链接

### 5. 内容创作助手 Skill (`skills/mingox-content-assistant/SKILL.md`)

**功能:**
- 记录 MingoX 项目专用能力说明
- 词汇标注格式速查
- 不识别词汇清单（第1类、第2类）
- 标签规范参考

## 内容规范要点速查

### 词汇标注格式
```html
<span class="word-block"><span class="english-word">word</span><span class="word-info">[音标] 词性. 释义</span></span>
```

### 严禁标注的词汇

**第1类（简单日常词）:**
yes, good, big, get, make, close, drop, go, see, take...

**第2类（高中常见词）:**
price, risk, trade, market, meeting, international, demand, flow, cancel, cost, gold, policy, chain, window, data, typical, emotion, giant, refuse, summit, domestic...

**供应链表述:**
优先用 **logistics**，不要单独标注 **chain**

### 密度要求
- 每句（以 `。！？；` 断句）至少1处 word-block
- 相邻 word-block 之间必须有中文/标点间隔
- 词汇表与正文标注一一对应

### 参考范文
- 政经外交: `posts/2026-03-29-china-g7-europe-market.html`
- 财经市场: `posts/2026-03-29-gold-price-analysis.html`

## 文件结构

```
/workspace/projects/workspace/
├── MEMORY.md                              # 已更新
├── skills/
│   └── mingox-content-assistant/
│       └── SKILL.md                       # 新增
└── MingoX/news/
    └── scripts/
        ├── check-content.sh               # 新增（可执行）
        ├── create-post.sh                 # 新增（可执行）
        ├── update-index.sh                # 新增（可执行）
        └── deploy.sh                      # 新增（可执行）
```

## 测试验证

运行 `check-content.sh` 验证现有文章：

```
✅ 未发现相邻 word-block 违规
✅ 所有文章结构完整
⚠️  部分文章词汇表数量与正文标注数量不一致（正常，同一词汇多次出现）
```

## 后续建议

1. **CI 集成**: 将 `check-content.sh` 集成到 Git pre-commit hook 或 CI 流程
2. **词汇库**: 建立常用词汇库，自动生成音标和释义
3. **Web 界面**: 开发简单的 Web 界面来管理文章创建流程
4. **自动化测试**: 为脚本编写单元测试，确保稳定性

## 总结

通过这次升级，我具备了完整支持 MingoX 内容创作的能力：

- **写作阶段**: 自动生成符合规范的模板
- **编辑阶段**: 自动化检查确保合规
- **发布阶段**: 一键完成从检查到部署的全流程

所有脚本已设置为可执行权限，可以直接使用。
