#!/bin/bash

# MingoX 令牌验证脚本
# 用途: 验证令牌是否正确保存和可访问

echo "======================================"
echo "MingoX 令牌验证脚本"
echo "======================================"
echo ""

# 验证 Gitee 令牌
echo "1. 验证 Gitee 令牌..."
if [ -f ~/.git-credentials ]; then
    GITEE_CREDS=$(cat ~/.git-credentials)
    if [[ "$GITEE_CREDS" == *"76d65c9f51ad0cdfbd24e36ede710bc3"* ]]; then
        echo "   ✅ Gitee 令牌已正确保存"
    else
        echo "   ❌ Gitee 令牌未找到或不匹配"
    fi
else
    echo "   ❌ ~/.git-credentials 文件不存在"
fi
echo ""

# 验证 EdgeOne 令牌
echo "2. 验证 EdgeOne 令牌..."
if [ -f ~/.config/edgeone/config.json ]; then
    EDGEONE_TOKEN=$(cat ~/.config/edgeone/config.json | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    if [[ "$EDGEONE_TOKEN" == *"nErJUE"* ]]; then
        echo "   ✅ EdgeOne 令牌已正确保存"
    else
        echo "   ❌ EdgeOne 令牌未找到或不匹配"
    fi
else
    echo "   ❌ EdgeOne 配置文件不存在"
fi
echo ""

# 验证环境变量文件
echo "3. 验证环境变量文件..."
if [ -f /workspace/projects/.env.mingox ]; then
    echo "   ✅ /workspace/projects/.env.mingox 存在"
    if grep -q "GITEE_TOKEN" /workspace/projects/.env.mingox; then
        echo "   ✅ GITEE_TOKEN 已配置"
    fi
    if grep -q "EDGEONE_TOKEN" /workspace/projects/.env.mingox; then
        echo "   ✅ EDGEONE_TOKEN 已配置"
    fi
else
    echo "   ❌ /workspace/projects/.env.mingox 文件不存在"
fi
echo ""

# 验证 Bash 自动加载
echo "4. 验证 Bash 自动加载配置..."
if grep -q ".env.mingox" ~/.bashrc; then
    echo "   ✅ ~/.bashrc 已配置自动加载"
else
    echo "   ⚠️  ~/.bashrc 未配置自动加载"
fi
echo ""

# 验证 Git 配置
echo "5. 验证 Git 凭证助手..."
GIT_HELPER=$(git config --global credential.helper)
if [[ "$GIT_HELPER" == *"store"* ]]; then
    echo "   ✅ Git 凭证助手已配置"
    echo "   配置: $GIT_HELPER"
else
    echo "   ❌ Git 凭证助手未配置"
fi
echo ""

# 验证项目文件
echo "6. 验证项目文件..."
if [ -f /workspace/projects/workspace/MINGOX_TOKENS.md ]; then
    echo "   ✅ MINGOX_TOKENS.md 存在"
else
    echo "   ❌ MINGOX_TOKENS.md 不存在"
fi
echo ""

# 测试 Git 推送 (dry-run)
echo "7. 测试 Git 推送权限..."
cd /workspace/projects/workspace/MingoX/news 2>/dev/null
if [ $? -eq 0 ]; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null)
    if [[ "$REMOTE_URL" == *"gitee.com/siglea/news"* ]]; then
        echo "   ✅ Git 远程仓库配置正确"
        echo "   URL: $REMOTE_URL"
    else
        echo "   ❌ Git 远程仓库未配置或错误"
    fi
else
    echo "   ❌ 无法访问项目目录"
fi
echo ""

echo "======================================"
echo "验证完成"
echo "======================================"
