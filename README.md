# AIBCC — AI Building Compliance Copilot

協助審查建築圖說是否符合法規的系統。目前為 S0 基礎建設階段，詳見：

- [S0 完成事項報告](docs/2026-07-19-s0-完成事項報告.md)
- [系統設計文件（現況版）](docs/2026-07-19-系統設計文件.md)

## 系統需求

- Docker / Docker Compose

本地開發一律使用 Docker Compose，不需要在本機安裝 Python 或建立 venv。

## 本地開發環境啟動方式

```bash
make dev   # docker compose up -d --build，啟動 backend + db + model-service
make log   # 追蹤 backend 日誌（docker compose logs -f backend）
```

`make dev` 為背景啟動（`-d`），每次執行都會依 `backend/Dockerfile` 重新檢查是否需要 rebuild（程式碼掛載於容器內，多數修改不需重新 build 即可生效）。

啟動後可用瀏覽器開啟：

- API：http://localhost:8000
- OpenAPI 文件：http://localhost:8000/docs
- Postgres：`localhost:5432`（帳密見 `docker-compose.yml` / `.env.example`）

停止服務請直接執行：

```bash
docker compose down
```

其他不常用的操作（進入資料庫 shell、單獨重建 image 等）亦直接使用原生 `docker compose` 指令即可，例如：

```bash
docker compose exec db psql -U aibcc -d aibcc
docker compose build backend
```

## 環境變數

複製 `.env.example` 為 `.env` 並依需求調整：

```bash
cp .env.example .env
```

| 變數 | 預設值 | 說明 |
|---|---|---|
| `DATABASE_URL` | `postgresql://aibcc:aibcc@localhost:5432/aibcc` | Postgres 連線字串（Docker Compose 內會自動改為 `db` 這個 service name） |
| `DEBUG` | `false` | 除錯模式開關（保留） |

## CI

GitHub Actions（`.github/workflows/ci.yml`）於每次 push / PR 執行 `Lint`、`Test`、`Docker Build` 三項檢查，`main` 分支已設定 branch protection，三項皆需通過才能合併。
