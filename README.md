# 🚀 RSS智能内容聚合推荐平台

> 基于 FastAPI + PostgreSQL + OpenAI 的个性化 RSS 订阅与推荐系统

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心功能

- 🔐 **用户认证系统** - JWT Token认证，安全可靠
- 📰 **多源内容抓取** - 支持RSS订阅、网页抓取
- 🤖 **AI智能富化** - 自动生成摘要、提取关键词、智能分类
- 📊 **文章管理** - 阅读状态、标签管理、搜索筛选
- ⏰ **定时任务** - 自动定时抓取更新内容
- 🎯 **个性化推荐** - 基于用户偏好的内容推荐

## 🛠️ 技术栈

### 后端框架

- **FastAPI** 0.116+ - 现代、快速的Web框架
- **SQLAlchemy** 2.0+ - ORM数据库操作
- **Alembic** - 数据库迁移工具
- **Pydantic** - 数据验证

### 数据库

- **PostgreSQL** 17 - 主数据库（支持全文检索）
- **Redis** 7 - 缓存与任务队列

### 爬虫技术

- **Playwright** - 无头浏览器，处理动态网页
- **feedparser** - RSS解析
- **BeautifulSoup** - HTML解析
- **httpx** - 异步HTTP客户端

### AI集成

- **OpenAI GPT-4** - 文章分析、摘要生成

### 任务调度

- **APScheduler** - 定时任务调度
- **Celery** - 异步任务队列

## 🚀 快速开始

### 前置要求

- Python 3.13+
- Docker & Docker Compose
- Git

### 安装步骤

1. **克隆项目**

```bash
git clone <your-repo-url>
cd rss-recommendation-platform
```

2. **安装依赖**

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .

# 安装 Playwright 浏览器
playwright install chromium
```

3. **配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要配置：

```env
# 数据库配置
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_NAME=rss_platform
DB_HOST=localhost
DB_PORT=54321

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# 应用
APP_NAME=RSS Recommendation Platform
DEBUG=True
```

4. **启动数据库服务**

```bash
docker-compose up -d
```

5. **数据库迁移**

```bash
alembic upgrade head
```

6. **运行应用**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **访问API文档**

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## 📖 API使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**响应示例**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. 创建RSS源

```bash
curl -X POST "http://localhost:8000/sources" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "阮一峰的网络日志",
    "url": "https://www.ruanyifeng.com/blog/",
    "type": "rss",
    "rss_url": "https://www.ruanyifeng.com/blog/atom.xml",
    "category": "技术",
    "fetch_frequency": 60
  }'
```

### 4. 抓取内容

```bash
# 抓取单个源
curl -X POST "http://localhost:8000/sources/1/fetch" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 使用AI富化 (生成摘要、关键词、分类)
curl -X POST "http://localhost:8000/sources/1/fetch?use_ai=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 获取文章列表

```bash
curl -X GET "http://localhost:8000/articles?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. 标记文章已读

```bash
curl -X PATCH "http://localhost:8000/articles/1/read" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📂 项目结构

```
rss-recommendation-platform/
├── alembic/                 # 数据库迁移
│   └── versions/           # 迁移版本文件
├── app/
│   ├── core/               # 核心配置
│   │   ├── config.py       # 应用配置
│   │   ├── database.py     # 数据库连接
│   │   └── security.py     # 安全工具 (JWT, 密码)
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── content_source.py  # 内容源模型
│   │   └── article.py      # 文章模型
│   ├── routers/            # API路由
│   │   ├── auth.py         # 认证路由
│   │   ├── sources.py      # 内容源路由
│   │   └── articles.py     # 文章路由
│   ├── schemas/            # Pydantic Schemas
│   ├── services/           # 业务逻辑
│   │   ├── crawler.py      # 爬虫服务
│   │   ├── fetch_service.py   # 抓取服务
│   │   └── ai_service.py   # AI服务
│   ├── tasks/              # 异步任务
│   └── main.py             # FastAPI应用入口
├── tests/                  # 测试文件
├── docker-compose.yml      # Docker编排
├── pyproject.toml          # 项目依赖
└── README.md               # 项目文档
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 查看测试覆盖率
pytest tests/ --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_auth.py -v
```

## 🐳 Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重建镜像
docker-compose up -d --build
```

## 🔧 开发工具

### 代码格式化

```bash
# 使用 black 格式化
black app/ tests/

# 使用 isort 整理导入
isort app/ tests/

# 使用 flake8 检查代码
flake8 app/ --max-line-length=88
```

### 数据库迁移

```bash
# 创建新的迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📊 数据库关系

```
User (用户)
  ↓ 1:N (级联删除)
ContentSource (内容源)
  ↓ 1:N (级联删除)
Article (文章)
```

- 每个用户拥有多个内容源
- 每个内容源产生多篇文章
- 删除用户时，自动删除其所有内容源和文章
- 所有查询都进行用户隔离

## 🎯 核心特性说明

### 智能抓取

- **RSS抓取**: 自动解析RSS Feed，获取文章列表
- **全文抓取**: 使用Playwright获取完整文章内容
- **智能选择器**: 自动识别标题、内容、作者、日期
- **反爬虫规避**: 模拟真实浏览器行为

### AI富化

- **摘要生成**: 自动生成50-200字文章摘要
- **关键词提取**: 提取3-5个核心关键词
- **智能分类**: 自动将文章分类（技术、新闻、生活等）
- **异步处理**: 不阻塞主流程，提升用户体验

### 用户隔离

- 每个用户独立管理自己的内容源和文章
- 严格的权限控制，确保数据安全
- 支持多用户并发使用

## ⚠️ 注意事项

1. **OpenAI API**: 需要有效的API Key，注意控制调用频率和成本
2. **Playwright**: 首次运行需要下载浏览器，约300MB
3. **数据库端口**: 默认PostgreSQL映射到54321避免冲突
4. **环境变量**: 请勿将`.env`文件提交到Git仓库

## 🚧 待实现功能

- [ ] 全文搜索 (PostgreSQL tsvector)
- [ ] 文章标签系统
- [ ] 阅读统计与分析
- [ ] 邮件订阅推送
- [ ] 移动端适配
- [ ] 性能监控与日志

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 License

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 作者: mx-pai
- 项目链接: [GitHub Repository](https://github.com/mx-pai/rss-recommendation-platform)

---

**⭐ 如果这个项目对你有帮助，请给一个星标支持！**
