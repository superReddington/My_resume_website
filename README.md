# 个人简历站 + 智能问答助手

同一仓库、同一台阿里云轻量：Nginx 提供简历页，FastAPI 提供问答和 PDF 知识库。

```
frontend/   简历网站（React + Vite）
backend/    助手 API（FastAPI + LangGraph + PostgreSQL/pgvector）
nginx/      反代配置
```

## 本地开发

终端一：

```bash
cd backend
docker compose up -d db
copy .env.example .env   # Windows
# 填入 DEEPSEEK_API_KEY
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

终端二：

```bash
cd frontend
pnpm install
pnpm dev
```

- 简历页：http://localhost:5173
- 知识库管理：http://localhost:8000/admin

## 生产部署（阿里云）

服务器上使用仓库根目录的 `docker-compose.yml`。GitHub 推送到 `main` 后，若已配置 Secrets，会自动构建前端并同步到 `/opt/resume`。

需要在 GitHub 仓库 Settings → Secrets 添加：

- `SSH_HOST`：服务器公网 IP
- `SSH_USER`：`root`
- `SSH_PRIVATE_KEY`：部署用私钥

在服务器 `/opt/resume/.env` 放置 `DEEPSEEK_API_KEY`、`ADMIN_TOKEN`、`POSTGRES_PASSWORD`，不要提交到 Git。

过渡期若 Vercel 仍在构建，把 Vercel 项目的 Root Directory 设为 `frontend`。
