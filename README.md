# 大连金普新区学区地图

## 项目结构

```
Map/
├── frontend/          # Vue 3 前端项目
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Map.vue    # 地图展示页
│   │   │   └── Admin.vue  # 后台管理页
│   │   ├── api/           # API 接口
│   │   ├── router/        # 路由配置
│   │   └── types/         # TypeScript 类型
│   └── package.json
│
└── backend/           # FastAPI 后端项目
    ├── main.py        # 入口文件
    ├── models.py      # 数据模型
    ├── schemas.py     # Pydantic 模型
    ├── database.py    # 数据库配置
    └── routers/       # API 路由
```

## 快速开始

### 1. 申请高德地图 API Key

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册账号并登录
3. 进入控制台 → 应用管理 → 创建新应用
4. 添加 Key，服务平台选择「Web端」
5. 复制生成的 Key

### 2. 配置前端

修改 `frontend/src/pages/Map.vue` 和 `frontend/src/pages/Admin.vue` 中的：

```typescript
const AMAP_KEY = 'YOUR_AMAP_KEY'  // 替换为你的高德地图 Key
```

### 3. 安装依赖

**后端：**
```bash
cd backend
pip install -r requirements.txt
```

**前端：**
```bash
cd frontend
npm install
```

### 4. 启动服务

**启动后端：**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端：**
```bash
cd frontend
npm run dev
```

### 5. 访问应用

- 地图页面：http://localhost:3000
- 后台管理：http://localhost:3000/admin
- API 文档：http://localhost:8000/docs

## 部署到服务器

### 1. 构建前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录。

### 2. 配置 Nginx

```nginx
server {
    listen 80;
    server_name map.liuqingyun.top;

    # 前端静态文件
    location / {
        root /path/to/Map/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 后端生产环境启动

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

或使用 systemd 管理服务：

```ini
# /etc/systemd/system/school-map.service
[Unit]
Description=School District Map API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Map/backend
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable school-map
sudo systemctl start school-map
```

## 功能说明

### 地图页面 (/)

- 显示大连金普新区地图
- 展示各小学学区边界（彩色多边形）
- 点击学区查看学校详细信息
- 右侧学校列表快速定位

### 后台管理 (/admin)

- 学校管理：添加、编辑、删除学校
- 学区绘制：在地图上手动绘制学区边界
- 支持修改学区颜色

## 数据存储

使用 SQLite 数据库，文件位于 `backend/schools.db`

### 数据表结构

**schools 表：**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 学校名称 |
| address | TEXT | 学校地址 |
| phone | TEXT | 联系电话 |
| description | TEXT | 学校简介 |
| color | TEXT | 学区颜色 |

**districts 表：**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| school_id | INTEGER | 关联学校 |
| coordinates | TEXT | 边界坐标 JSON |
