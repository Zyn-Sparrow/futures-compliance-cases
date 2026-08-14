# 期货合规案例库 - 自动更新系统

每周五自动从中期协官网爬取最新纪律处分案例，更新并部署到 Netlify 网站。

## 工作原理

```
GitHub Actions (每周五 10:00 北京时间)
    ↓
Python 爬虫 → 中期协官网 API → 获取新案例
    ↓
案例处理 → 提取违规要点/处罚结果/摘要/关键词/分类
    ↓
合并到已有案例库 (cases.json)
    ↓
生成网站 HTML (从模板 + 数据)
    ↓
Netlify API 部署 (保持 URL 不变)
    ↓
Git 提交更新后的案例数据
```

**核心优势：完全免费，不消耗任何 AI 积分。** GitHub Actions 公开仓库无限免费分钟数，Netlify 免费套餐足够使用。

## 项目结构

```
futures-compliance-cases/
├── data/
│   └── cases.json              # 案例数据库 (JSON 格式)
├── template/
│   └── index_template.html     # 网站模板 (含 __CASES_DATA__ 占位符)
├── scripts/
│   ├── crawl_cfachina.py       # 中期协官网爬虫
│   ├── process_cases.py        # 案例处理 (提取结构化字段)
│   ├── generate_site.py        # 网站生成
│   ├── deploy_netlify.py       # Netlify 部署
│   └── run_update.py           # 主编排脚本
├── .github/workflows/
│   └── weekly-update.yml       # GitHub Actions 工作流
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 部署指南（一次性设置，约 20 分钟）

### 第一步：注册 GitHub 账号

1. 访问 https://github.com 注册账号（免费）
2. 登录后点击右上角 `+` → `New repository`
3. 仓库名称填 `futures-compliance-cases`
4. 选择 **Public**（公开仓库，Actions 免费无限使用）
5. 勾选 `Add a README file`
6. 点击 `Create repository`

### 第二步：上传项目文件

将本目录下的所有文件上传到 GitHub 仓库：

**方法 A（推荐）：使用 GitHub 网页上传**
1. 在仓库页面点击 `Add file` → `Upload files`
2. 将以下文件/文件夹拖入：
   - `data/` 文件夹（含 cases.json）
   - `template/` 文件夹（含 index_template.html）
   - `scripts/` 文件夹（含所有 .py 文件）
   - `.github/` 文件夹（含 workflows/weekly-update.yml）
   - `requirements.txt`
   - `README.md`
3. 点击 `Commit changes`

**方法 B：使用 Git 命令行**
```bash
git clone https://github.com/你的用户名/futures-compliance-cases.git
# 将文件复制到仓库目录
git add .
git commit -m "初始提交：期货合规案例库自动更新系统"
git push
```

### 第三步：获取 Netlify 凭据

你的网站 `https://wonderful-cassata-a9ca01.netlify.app` 已经在 Netlify 上。需要获取两个信息：

**1. 获取 Site ID：**
1. 登录 https://app.netlify.com
2. 点击你的网站 `wonderful-cassata-a9ca01`
3. 点击 `Site settings` → `General`
4. 找到 `Site ID`（格式类似 `a9ca01xx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）
5. 复制保存

**2. 创建 Personal Access Token：**
1. 访问 https://app.netlify.com/user/applications#personal-access-tokens
2. 点击 `New access token`
3. 描述填 `GitHub Actions 自动部署`
4. 点击 `Generate token`
5. **立即复制** token（只显示一次！）

### 第四步：配置 GitHub Secrets

1. 回到 GitHub 仓库页面
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`，添加两个：

| Name | Value |
|------|-------|
| `NETLIFY_SITE_ID` | 第三步获取的 Site ID |
| `NETLIFY_AUTH_TOKEN` | 第三步获取的 Token |

### 第五步：验证自动化

1. 在 GitHub 仓库页面点击 `Actions` 标签
2. 左侧选择 `每周合规案例自动更新`
3. 点击 `Run workflow` → `Run workflow` 手动触发一次测试
4. 等待运行完成（约 2-3 分钟），查看日志确认：
   - 爬虫成功获取新案例
   - 网站生成成功
   - Netlify 部署成功
5. 访问 `https://wonderful-cassata-a9ca01.netlify.app` 确认网站已更新

**设置完成！** 之后每周五北京时间 10:00 自动运行，无需任何手动操作。

## 自动化时间

- **触发时间**：每周五 北京时间 10:00
- **Cron 表达式**：`0 2 * * 5`（UTC 时间周五 02:00 = 北京时间 10:00）
- **运行时长**：约 2-3 分钟
- **也可手动触发**：GitHub → Actions → Run workflow

## 数据源

### 当前支持
- **中期协官网** (`cfachina.org`)：纪律处分决定，通过官方 API 获取，稳定可靠

### 未来可扩展
- 微信公众号（合规内控视野、合规小新、一德合规监察、壹口合规、合规小兵等）
  - 推荐方案：WeWe RSS（基于微信读书接口，免费）
  - 需要定期刷新 Cookie，详见 `scripts/crawl_wechat.py`（待实现）

## 本地运行

如需在本地手动运行更新：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行完整更新流程
python scripts/run_update.py

# 或分步运行
python scripts/crawl_cfachina.py    # 仅爬虫
python scripts/generate_site.py     # 仅生成网站
python scripts/deploy_netlify.py    # 仅部署
```

部署需要设置环境变量：
```bash
export NETLIFY_SITE_ID="你的Site ID"
export NETLIFY_AUTH_TOKEN="你的Token"
```

## 常见问题

**Q: 网站链接会变吗？**
A: 不会。部署通过 Netlify API 直接更新已有站点，URL 保持不变。

**Q: 会消耗 AI 积分吗？**
A: 不会。整个流程在 GitHub Actions 上运行，完全免费。AI 积分仅在初始搭建时消耗。

**Q: 如果某次爬虫失败怎么办？**
A: GitHub Actions 会记录失败日志，下次运行时会自动重试。也可手动触发。

**Q: 如何添加非中期协的案例？**
A: 直接编辑 `data/cases.json`，按相同格式添加案例，然后手动运行生成和部署。

**Q: 案例分类和关键词是如何生成的？**
A: 通过规则匹配自动生成（基于关键词词典和文本模式匹配），质量略低于人工/AI生成，但完全免费。
