# MingoX 内容助手

协助 MingoX 项目创建符合规范的双语内容。

## 能力范围

### 1. 文章创建
- 根据主题创建中英双语文章
- 自动添加词汇标注（`word-block` 格式）
- 生成符合规范的词汇表
- 确保词汇密度（每句至少1处标注）

### 2. 质量检查
- 检查相邻 `word-block` 违规
- 验证词汇表与正文一致性
- 检查 HTML 结构合规性

### 3. 发布流程
- 更新 `index.html` 列表
- 部署到 Gitee Pages
- 部署到 EdgeOne Pages

## 使用方式

### 创建新文章
```
创建一篇关于 [主题] 的文章
```

### 检查文章合规性
```
检查 posts/YYYY-MM-DD-title.html 的规范性
```

### 部署网站
```
MX deploy
```

## 内容规范速查

### 词汇标注格式
```html
<span class="word-block"><span class="english-word">word</span><span class="word-info">[音标] 词性. 释义</span></span>
```

### 标题格式
```html
<h1>[emoji] 中文标题<br><small class="title-en">English Title</small></h1>
```

### 标签规范
- 内容形式：📝 文字、🖼️ 图片、🎙️ 播客、📹 视频
- 语言类型：🌐 多语言、🇨🇳 中文、🇬🇧 英文
- 主题标签：财经、科技、文化、观点

## 不识别词汇清单（严格执行）

### 第1类：非常简单的日常高频词
yes, good, big, get, make, close, drop, go, see, take 等

### 第2类：高中英语课程标准常见词
price, risk, trade, market, meeting, international, demand, flow, cancel, cost, gold, policy, chain, window, data, typical, emotion, giant, refuse, summit, domestic 等

### 供应链表述
优先用 **logistics** 等学科/行业上位词，**不要**单独标注 **chain**
