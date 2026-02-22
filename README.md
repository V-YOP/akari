第一次尝试vide coding吧，大部分业务都是让deepseek-reasoner写的。

起因是想要一个有前端的，本地的计划任务调度应用。以前写了一个非常简单的命令行的，但用起来比较复杂。

注意默认配置在`backend/app/config.py`，修改它或者

下面全是AI生成的。按照下面的部署的教程把前端拷到`backend/static`后，就可以只起后端去使用这个应用了。

---


*[English Documentation](README_en.md) | [中文文档](README.md)*

# Akari 任务调度器

一个具有 Web 界面的本地任务调度应用，用于定义、测试和监控计划任务。

## 功能特性

- **任务调度**: 支持 Cron 表达式和基于间隔时间的调度
- **任务执行**: 执行任意命令行程序及其参数
- **日志记录**: 捕获和查看标准输出、标准错误、退出码和执行详情
- **Web 界面**: 现代化的 Vue.js 前端，支持亮/暗主题
- **国际化**: 支持英文和中文界面
- **REST API**: 完整的 API 文档，便于其他客户端集成
- **本地数据库**: 使用 SQLite 数据库进行数据持久化
- **无需认证**: 本地使用简单，无需认证开销

## 项目结构

```
akari/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 端点
│   │   ├── core/     # 配置和事件处理
│   │   ├── db/       # 数据库连接
│   │   ├── models/   # 数据模型
│   │   └── scheduler/# 任务调度逻辑
│   ├── requirements.txt
│   └── main.py       # 应用入口点
└── frontend/         # Vue.js 前端
    ├── src/
    │   ├── components/
    │   ├── views/    # 页面组件
    │   ├── stores/   # Pinia 状态管理
    │   ├── locales/  # 国际化翻译
    │   └── styles/   # 全局样式
    ├── package.json
    └── vite.config.js
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- SQLite3 (Python 已包含)

### 后端设置

1. 进入后端目录:
   ```bash
   cd akari/backend
   ```

2. 创建虚拟环境 (推荐但可选):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Unix/MacOS:
   source venv/bin/activate
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 启动后端服务器:
   ```bash
   python main.py
   ```
   服务器将在 `http://localhost:8000` 启动
   - API 文档: `http://localhost:8000/api/docs`
   - 备用文档: `http://localhost:8000/api/redoc`

### 前端设置

1. 打开新终端，进入前端目录:
   ```bash
   cd akari/frontend
   ```

2. 安装依赖:
   ```bash
   npm install
   ```

3. 启动开发服务器:
   ```bash
   npm run dev
   ```
   前端将在 `http://localhost:3000` 启动

4. 在浏览器访问 `http://localhost:3000`

## 使用方法

### 创建任务

1. 在任务列表页面点击 "新建任务"
2. 填写任务详情:
   - **名称**: 任务的描述性名称
   - **命令**: 可执行文件的完整路径或 PATH 中的命令
   - **参数**: 可选命令行参数
   - **调度类型**: 选择 Cron 或间隔时间
   - **调度详情**: Cron 表达式或间隔秒数
   - **超时时间**: 最长执行时间
   - **最大并发数**: 限制同时执行的数量
   - **启用**: 启用/禁用任务

### 任务示例

1. **每5分钟执行的 Python 脚本**:
   - 命令: `python`
   - 参数: `C:\scripts\backup.py`
   - 调度类型: Cron
   - Cron 表达式: `*/5 * * * *`

2. **每30秒执行的 Shell 脚本**:
   - 命令: `bash`
   - 参数: `/home/user/scripts/monitor.sh`
   - 调度类型: 间隔时间
   - 间隔: `30`（秒）

3. **一次性测试执行**:
   - 创建任意调度的任务
   - 在任务编辑页面点击 "测试执行"

### 查看日志

- 导航到 "日志" 页面查看执行历史
- 按任务、状态或搜索文本筛选日志
- 查看包括 stdout/stderr 的详细日志
- 清除旧日志或删除特定条目

## 生产部署

本教程指导您将前端构建到后端静态目录，实现单服务部署（只需启动后端即可使用完整应用）。

### 部署步骤

以下步骤将前端构建产物复制到后端静态目录，实现一体化部署：

#### 方法一：分步部署

1. **构建前端应用**
   ```bash
   # 进入前端目录
   cd akari/frontend

   # 安装依赖（如果尚未安装）
   npm install

   # 构建生产版本
   # npm run build
   # 不能用 npm run build，因为 ts 有一些error没有处理过不了vue-tsc的编译，但应该不影响业务
   npx vite build
   ```
   构建完成后，产物位于 `akari/frontend/dist` 目录。

2. **准备后端静态目录**
   ```bash
   # 返回项目根目录
   cd ..

   # 清理后端 static 目录（确保目录存在）
   # Windows:
   if exist backend\static\index.html del backend\static\* 2>nul
   # Unix/MacOS:
   rm -rf backend/static/* 2>/dev/null

   # 复制前端构建产物到后端静态目录
   # Windows:
   xcopy /E /I frontend\dist\* backend\static\
   # Unix/MacOS:
   cp -r frontend/dist/* backend/static/
   ```

3. **启动后端服务**
   ```bash
   cd backend
   python main.py
   ```

#### 方法二：一键部署脚本

创建 `deploy.sh`（Unix/MacOS）或 `deploy.bat`（Windows）脚本：

**deploy.sh**
```bash
#!/bin/bash
cd akari/frontend
npm install
npm run build
cd ..
rm -rf backend/static/*
cp -r frontend/dist/* backend/static/
echo "部署完成！请运行: cd backend && python main.py"
```

**deploy.bat**
```batch
@echo off
cd akari\frontend
npm install
npm run build
cd ..
if exist backend\static\index.html del backend\static\* 2>nul
xcopy /E /I frontend\dist\* backend\static\
echo 部署完成！请运行: cd backend && python main.py
```

### 验证部署
- 访问 `http://localhost:8000` 查看 Web 界面
- 访问 `http://localhost:8000/api/docs` 查看 API 文档
- 所有前端资源将由后端 FastAPI 静态文件服务提供

### 注意事项
- 确保后端 `static` 目录存在（项目已包含空目录）
- 构建后，前端 API 请求将发送到同一域名的 `/api` 路径
- 如需自定义端口或主机，请编辑 `akari/backend/app/config.py` 或设置环境变量

## API 参考

后端在 `http://localhost:8000` 提供 RESTful API

### 关键端点

- `GET /tasks` - 分页列出任务
- `POST /tasks` - 创建新任务
- `GET /tasks/{id}` - 获取任务详情
- `PUT /tasks/{id}` - 更新任务
- `DELETE /tasks/{id}` - 删除任务
- `POST /tasks/{id}/execute` - 手动执行任务
- `GET /tasks/{id}/logs` - 获取任务执行日志
- `GET /logs` - 获取所有执行日志
- `DELETE /logs` - 按筛选条件清除日志

完整 API 详情请查看 `/docs` 的交互式文档。

## 配置

### 后端配置

编辑 `akari/backend/app/config.py` 或创建 `.env` 文件:

```env
DB_URL=sqlite:///akari.db
DEBUG=true
LOG_LEVEL=INFO
SCHEDULER_MAX_WORKERS=10
```

### 前端配置

编辑 `akari/frontend/vite.config.js` 更改代理设置或端口。

## 开发

### 添加新功能

1. **新 API 端点**:
   - 在 `app/api/` 中添加路由
   - 如有需要更新模型
   - 使用 Swagger UI 测试

2. **前端页面**:
   - 在 `src/views/` 中创建 Vue 组件
   - 在 `src/router/index.ts` 中添加路由
   - 在 `src/locales/` 中添加翻译

3. **数据库变更**:
   - 在 `app/models/` 中更新模型
   - 使用 aerich 进行迁移 (待办: 添加迁移设置)

### 测试

运行后端测试:
```bash
cd backend
pytest
```

运行前端测试:
```bash
cd frontend
npm test
```

## 许可证

MIT 许可证 - 详见 LICENSE 文件 (待添加)
