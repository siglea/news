# Learn English by News

通过新闻学习英语词汇的项目。

## 约定

### 1. 输入
- 主人提供文章或链接（中英文新闻）

### 2. 处理流程
- 提取英文单词（单个核心词，避免简单常见词）
- 格式：中文为主 + 英文单词嵌入
- 每个英文单词标注：词性 + 含义 + 时态

### 3. 输出格式
```
最近一周，**inflation**（n.通胀）持续走高
```

### 4. 文件命名
- 格式：`news-YYYY-MM-DD-主题名.html`
- 示例：`news-2026-03-28-us-stock.html`

### 5. 更新首页
- 在 `index.html` 中添加新文章的链接
- 按日期倒序排列

### 6. Git 流程
1. 修改/创建 HTML 文件
2. 更新 index.html
3. Git add, commit, push
4. EdgeOne 部署

## 项目信息
- Gitee 仓库：https://gitee.com/siglea/news
- EdgeOne 项目：mynews
- 访问地址：https://mynews-cyeblzku.edgeone.cool
