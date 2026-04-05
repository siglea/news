# MingoX 令牌位置记录
# 生成时间: 2026-03-29 12:16

## Gitee 访问令牌

**令牌值:** 76d65c9f51ad0cdfbd24e36ede710bc3

**存储位置:**
1. Git凭证文件: `~/.git-credentials`
2. 项目环境变量: `/workspace/projects/.env.mingox`

**用途:**
- 推送代码到 Gitee 仓库
- 认证 Git 操作

---

## EdgeOne 访问令牌

**令牌值:** nErJUE/2bCEGv96OAhb6FOBYThbqh+FzKmzXoT2ptXs=

**存储位置:**
1. EdgeOne配置: `~/.config/edgeone/config.json`
2. 项目环境变量: `/workspace/projects/.env.mingox`

**用途:**
- 部署静态站点到 EdgeOne Pages
- EdgeOne CLI 认证

---

## 自动加载配置

**Shell 配置:** `~/.bashrc` (自动加载 `/workspace/projects/.env.mingox`)

**新会话自动激活:** 是，通过 `.bashrc` 自动加载

---

## Git 配置

**全局凭证助手:** `git config --global credential.helper 'store --file ~/.git-credentials'`

**已配置仓库:** https://gitee.com/siglea/news.git

---

## 验证命令

```bash
# 检查 Gitee 令牌
cat ~/.git-credentials

# 检查 EdgeOne 令牌
cat ~/.config/edgeone/config.json

# 检查环境变量
source ~/.bashrc
echo $GITEE_TOKEN
echo $EDGEONE_TOKEN

# 验证 Git 认证
cd /workspace/projects/workspace/MingoX/news
git push

# 验证 EdgeOne 登录
edgeone whoami
```

---

**⚠️ 安全提醒:**
- 所有配置文件权限已设置为 600 (仅所有者可读写)
- `.env.mingox` 已在 `.gitignore` 中，不会被提交
- Git 凭证存储在用户目录，不会被共享
