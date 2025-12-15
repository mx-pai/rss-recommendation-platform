# RSS 智能内容聚合推荐平台 - 项目现状报告

## 📊 项目概览

**项目名称**: RSS Recommendation Platform
**技术栈**: FastAPI + PostgreSQL + Redis + Playwright + OpenAI
**最后更新**: 2025年10月15日
**Python版本**: 3.13+

---

## 🏗️ 已实现功能

### ✅ 1. 用户认证系统
- **模型**: `User` (用户表)
- **功能**:
  - 用户注册/登录 (JWT Token)
  - 密码加密 (bcrypt)
  - 用户隔离 (每个用户独立数据)
  - 级联删除 (删除用户时同步删除其内容源和文章)

**路由**: `app/routers/auth.py`
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户信息

---

### ✅ 2. 内容源管理
- **模型**: `ContentSource` (内容源表)
- **功能**:
  - 支持多种源类型: RSS、手动抓取、API
  - 源配置管理 (抓取频率、选择器等)
  - 用户隔离 (每个用户管理自己的源)

**路由**: `app/routers/sources.py`
- `POST /sources` - 创建内容源
- `GET /sources` - 获取所有内容源
- `GET /sources/{id}` - 获取单个内容源
- `PUT /sources/{id}` - 更新内容源
- `DELETE /sources/{id}` - 删除内容源
- `POST /sources/{id}/fetch` - 手动触发抓取

**支持的源类型**:
- `rss`: RSS订阅源 (自动抓取全文)
- `manual`: 单个网页抓取
- `api`: API接口 (待实现)

---

### ✅ 3. 文章管理系统
- **模型**: `Article` (文章表)
- **功能**:
  - 文章存储与去重 (基于URL)
  - 全文内容抓取 (Playwright)
  - AI富化 (摘要、关键词、分类)
  - 图片提取
  - 字数统计
  - 阅读状态管理

**路由**: `app/routers/articles.py`
- `GET /articles` - 获取文章列表 (支持分页、筛选)
- `GET /articles/{id}` - 获取文章详情
- `PUT /articles/{id}` - 更新文章
- `DELETE /articles/{id}` - 删除文章
- `PATCH /articles/{id}/read` - 标记已读/未读

**文章字段**:
- 基础: title, content, url, author, published_at
- AI富化: summary, keywords, category
- 元数据: images, word_count, is_read
- 关联: source_id, user_id

---

### ✅ 4. 智能抓取服务

#### 4.1 RSS抓取 (`RSSCrawler`)
- 使用 `feedparser` 解析RSS Feed
- 提取: 标题、链接、作者、发布时间、描述
- 自动调用全文抓取获取完整内容

#### 4.2 网页抓取 (`ModernWebCrawler`)
- **技术**: Playwright (无头浏览器)
- **功能**:
  - 动态网页渲染
  - 智能选择器匹配
  - 图片提取
  - 反爬虫规避
  - 内容清洗

**选择器策略**:
```python
# 标题选择器
h1, .title, .article-title, .post-title, .entry-title, etc.

# 内容选择器
article, .article-content, .post-content, .entry-content,
.content, .main-content, .article-body, main, etc.

# 作者选择器
.author, .by-author, .author-name, .post-author, etc.
```

#### 4.3 抓取服务 (`FetchService`)
- RSS全文抓取: 先获取RSS列表 → 逐个抓取全文
- 网页抓取: 直接抓取单个网页
- 智能去重: 检查URL是否已存在
- 字段回填: 已存在文章自动补充缺失字段
- 批量抓取: 支持抓取所有活跃源

---

### ✅ 5. AI 服务 (`AIService`)
- **技术**: OpenAI GPT-4
- **功能**:
  - 文章摘要生成 (50-200字)
  - 关键词提取 (3-5个)
  - 文章分类
  - 内容质量评估

**触发方式**:
- 手动抓取时传参 `use_ai=true`
- 异步任务触发 (待实现)

---

## 🚧 待实现功能 (TODO)

根据之前的TODO列表,以下功能尚未实现:

### 1. 文章标签与稍后读 (`todo-tags-bookmark`)
- [ ] 标签模型 (Tag)
- [ ] 文章-标签多对多关系
- [ ] 稍后读标记字段
- [ ] 相关API接口

### 2. PostgreSQL 全文检索 (`todo-tsvector-reco`)
- [ ] 接入 tsvector 全文索引
- [ ] 搜索API (标题+内容)
- [ ] 简单推荐算法 (相似文章)

### 3. 定时任务调度 (`todo-scheduler`)
- [ ] APScheduler 集成
- [ ] 按 `fetch_frequency` 定时抓取
- [ ] 任务状态监控

### 4. 测试覆盖 (`todo-tests`)
- [ ] pytest 测试框架
- [ ] 关键API单元测试
- [ ] 集成测试

### 5. 可观测性 (`todo-observability`)
- [ ] Sentry 错误监控
- [ ] 结构化日志 (JSON格式)
- [ ] 性能监控

### 6. Docker部署 (`todo-deploy`)
- [ ] Docker镜像优化
- [ ] docker-compose 完善
- [ ] 公网demo部署

### 7. AI富化优化 (`todo-ai-enrichment`) - **进行中**
- [ ] AI富化异步化 (Celery任务)
- [ ] 限流机制 (避免API费用过高)
- [ ] AI开关配置
- [ ] `/articles/{id}/enrich` 手动富化接口
- [ ] APScheduler 定时富化

---

## 📁 项目结构

```
rss-recommendation-platform/
├── alembic/                  # 数据库迁移
│   ├── versions/
│   │   └── 2ec61f38a5be_add_user_isolation_and_cascade_delete.py
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── core/                 # 核心配置
│   │   ├── config.py         # 应用配置
│   │   ├── database.py       # 数据库连接
│   │   └── security.py       # 安全工具 (JWT, 密码)
│   ├── models/               # 数据模型
│   │   ├── user.py           # 用户模型
│   │   ├── content_source.py # 内容源模型
│   │   └── article.py        # 文章模型
│   ├── routers/              # 路由/API
│   │   ├── auth.py           # 认证路由
│   │   ├── sources.py        # 内容源路由
│   │   └── articles.py       # 文章路由
│   ├── services/             # 业务逻辑
│   │   ├── crawler.py        # 爬虫服务
│   │   ├── fetch_service.py  # 抓取服务
│   │   └── ai_service.py     # AI服务
│   ├── tasks/                # 异步任务 (待完善)
│   └── main.py               # FastAPI应用
├── tests/                    # 测试 (待完善)
├── docker-compose.yml        # Docker编排
├── Dockerfile                # Docker镜像
├── pyproject.toml            # 依赖管理 (uv)
└── README.md                 # 项目文档

```

---

## 🛠️ 技术选型

### 后端框架
- **FastAPI**: 现代、快速的Web框架
- **SQLAlchemy**: ORM数据库操作
- **Alembic**: 数据库迁移工具
- **Pydantic**: 数据验证

### 数据库
- **PostgreSQL**: 主数据库 (支持全文检索)
- **Redis**: 缓存 (已配置,未充分使用)

### 抓取技术
- **Playwright**: 无头浏览器 (动态网页)
- **feedparser**: RSS解析
- **BeautifulSoup**: HTML解析
- **httpx**: 异步HTTP客户端

### AI集成
- **OpenAI GPT-4**: 文章分析与摘要

### 任务调度
- **APScheduler**: 定时任务 (待接入)
- **Celery**: 异步任务队列 (待接入)

---

## 🔧 环境配置

### 必需环境变量 (.env)
```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/rss_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# 应用
APP_NAME=RSS Recommendation Platform
DEBUG=True
```

---

## 📊 数据库关系

```
User (用户)
  ↓ 1:N
ContentSource (内容源)
  ↓ 1:N
Article (文章)

关系特点:
- User → ContentSource: 级联删除
- User → Article: 级联删除
- ContentSource → Article: 级联删除
- 用户隔离: 所有查询需要 user_id 过滤
```

---

## 🐛 已知问题

### 1. 抓取问题
**现象**: 部分网站抓取失败,内容提取为空

**可能原因**:
- 选择器不匹配网站结构
- 反爬虫机制阻止
- 页面加载超时
- JavaScript渲染未完成

**待修复**: 需要更智能的选择器策略或回退机制

### 2. AI富化未异步化
**现象**: AI调用阻塞HTTP请求

**影响**: 用户体验差,可能超时

**解决方案**: 使用Celery异步任务队列

### 3. 缺少定时任务
**现象**: 需要手动触发抓取

**影响**: 无法自动更新内容

**解决方案**: APScheduler定时任务

---

## 🚀 快速启动

### 1. 安装依赖
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入配置
```

### 3. 数据库迁移
```bash
alembic upgrade head
```

### 4. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📝 API使用示例

### 1. 用户注册
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 用户登录
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### 3. 创建RSS源
```bash
curl -X POST "http://localhost:8000/sources" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "阮一峰博客",
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

# 使用AI富化
curl -X POST "http://localhost:8000/sources/1/fetch?use_ai=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 获取文章列表
```bash
curl -X GET "http://localhost:8000/articles?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 下一步计划

1. **优先级高**:
   - 修复抓取失败问题 (改进选择器策略)
   - 实现AI富化异步化 (Celery)
   - 接入APScheduler定时任务

2. **优先级中**:
   - 实现全文搜索 (PostgreSQL tsvector)
   - 添加标签与稍后读功能
   - 完善测试覆盖

3. **优先级低**:
   - 接入Sentry监控
   - Docker部署优化
   - 公网demo部署

---

## 📞 联系方式

如有问题,请查看:
- API文档: http://localhost:8000/docs
- 项目仓库: (待补充)

---

**最后更新**: 2025-10-15
**维护者**: mx2004



