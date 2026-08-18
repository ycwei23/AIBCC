# S3｜8/17–8/30 即時 Pipeline 與整合

> **進度檢討：8/31 22:00**

## 目標

強化系統完整性、實作 What-if 模擬、確保前端整合穩定，系統需達到可展示水準。

---

## 任務清單

### What-if 模擬 API

- [ ] 實作 `POST /v1/analyses/{id}/simulate`
  - 接受 JSON Patch 描述變更（如走道加寬 200mm）
  - 複製 JSON IR、重算 graph/path
  - 重跑受影響規則，回傳差異（非語言推測）
- [ ] What-if 結果包含：受影響規則、before/after 判定、修正後是否通過

### Geometry Validator 整合

- [ ] 整合 Geometry Validator（OpenCV / Shapely / NetworkX）進入 pipeline
- [ ] 確認幾何驗證邏輯：比例校正、polygon、門寬、最短逃生路徑
- [ ] VLM 與工具結果衝突時標為 `review_required`，不靜默通過

### JSON IR 穩定邊界驗證

- [ ] 驗證 Rule Engine 與 Frontend 不需因 VLM/Document AI 調整而改變
- [ ] 確認 JSON IR schema 版本化（有 version 欄位）

### Frontend 整合支援

- [ ] 確認圖面 highlight 座標格式（polygon 座標）符合前端需求
- [ ] 確認 violations 清單與 evidence drawer 所需欄位齊全
- [ ] 支援 Frontend 完成圖面標記功能整合

### Agent 品質強化

- [ ] Agent 每次回答必附：法條、圖面 highlight、量測值、規則版本、信心值、decision trace
- [ ] Agent 不可覆寫 Rule Engine 判定，只能解釋與建議

### S2 Final Review 遺留項目（技術債）

> 來源：S2 端到端 Alpha 最終 whole-branch review（commit `0f774be` 前），7 項 Important 發現。final review 判定不擋 S2 合併（2 個 Critical 已在同一輪修掉），留到 S3 處理，記錄於該 plan 的 SDD ledger。

**API 一致性與錯誤處理**

- [ ] 路徑參數（`analysis_id` 等）型別改為 `UUID`，非法格式回 422 而非現在的 500
- [ ] 統一「查無資料」防呆慣例：`start_analysis`/`upload_file` 目前沒有像 `copilot` 那樣的存在性檢查，補齊

**Geometry Validator 與 review_required 狀態**（與上方「Geometry Validator 整合」任務同一批，建議一起做）

- [ ] `validate_geometry` 剔除的元件目前直接消失（不保留 `geometry_errors`、不產生 `insufficient_data` 違規），改為保留錯誤紀錄，讓 `/report` 能呈現「哪些元件因幾何錯誤未被檢查」
- [ ] `analysis_runs.status` 從未真正進入 `review_required`（schema 有定義但 pipeline 從沒設過）——串進上方「VLM 與工具結果衝突時標為 `review_required`」那項

**Pipeline 各環節仍是斷點，尚未真正串起**

- [ ] 檔案上傳（`upload_file`）跟分析（`start_analysis`）目前互不相關，`analysis_runs.file_id` 永遠是 `None`
- [ ] Document AI 的 `dimension_annotation` 元件雖會被驗證、存進 graph，但沒有規則真的讀它，也沒有跟它量測的對象（門、走廊）建立關聯
- [ ] 10 份 fixture 的 `vlm_relations` 全部是空陣列，`vlm_relations_to_graph_edges` 從未在真實 pipeline 跑過
- [ ] `retrieve_law` 查到的 `LawMatch`（含 `rule_id`/`article`）沒有接進 `/copilot` 回應的 `citations`，目前永遠是空陣列

**Agent 工具契約**（與上方「Agent 品質強化」任務相關）

- [ ] S1 定義的 8 個 Agent tool 的 Pydantic Input/Output（`app/agent/tools.py`）在 S2 的 `tool_executor.py` 沒有被強制驗證，實際傳的是裸 dict，型別已跟宣告的 schema 有落差（例如 `RUN_RULES` 實際上是讀已存的 violations，不是真的「跑規則」）
- [ ] `get_agent_run` 回傳的 `final_rule_status` 用的是 state machine 的詞彙（`done`/`failed`），跟欄位名稱暗示的 `pass`/`fail`/`insufficient_data` 不是同一套，接真的 LLM planner 前建議先對齊

**CI 可靠性**

- [ ] 目前 integration 測試在 Postgres 不可達時會乾淨 skip；如果 CI 的 Postgres service 本身掛掉，CI 還是會綠燈，只是靜默跳過整條 pipeline 的驗證。建議加 `--strict-markers` 或「skip 數量超過閾值就讓 job fail」的檢查

**資料一致性**

- [ ] `upsert_rules` 目前是 `ON CONFLICT DO NOTHING`，只會插入沒有的規則；`mvp_rules_active_v0.json` 之後如果改了門檻值/內容，DB 裡的舊資料不會更新，會悄悄跟規則檔案脫鉤——改成真的 `UPDATE`，或把函式改名成 `insert_missing_rules` 讓限制寫在名字上

---

## 交付標準

- What-if API 可接受 JSON Patch 並回傳前後對比結果
- Geometry Validator 已整合，衝突情況有標記
- Frontend 可呈現違規標記、法條引用與 evidence drawer
