# ADR-0001: 技術棧、Agent 架構、Knowledge Graph 選型

**日期：** 2026-08-02
**狀態：** Accepted
**決策者：** ycwei（S1 負責人）

## 背景

S0 已建立服務骨架（FastAPI + PostgreSQL 15 + Docker Compose），S1 完成了 Knowledge Graph PoC（見 [docs/2026-08-02-knowledge-graph-poc.md](../2026-08-02-knowledge-graph-poc.md)）與 Agent 架構骨架（`backend/app/agent/`）。本 ADR 記錄這些選型背後的理由，作為後續 S2（端到端 Alpha）與 S3（即時 Pipeline）階段的決策依據。

## 決策 1：技術棧選型（FastAPI、PostgreSQL、顯式 state machine）

**選擇：** FastAPI + Pydantic v2 作為 API 層，PostgreSQL 15 作為唯一持久化儲存，Agent 推理迴圈以手寫的顯式 state machine（`backend/app/agent/state_machine.py`）實作，不引入 LangChain / AutoGen / CrewAI 等大型 agent framework。

**理由：**

- **FastAPI + Pydantic v2：** 系統的核心價值是「產出可被法規稽核的違規判定」，每筆輸出都需要能追溯到明確的資料契約（`BuildingElement`、`Rule`、`Violation`、`GraphEdge`、`AgentTrace`，見 `backend/app/models/ir.py`）。FastAPI 與 Pydantic v2 原生整合，讓 API 的 request/response schema 與內部資料契約共用同一套型別定義與驗證邏輯，降低契約漂移的風險，且自動產生 OpenAPI 文件，方便前端與副負責人對接。
- **PostgreSQL 15：** 專案需要同時處理結構化資料（專案、檔案、分析執行、違規）與半結構化資料（建築元件的 `geometry`、圖譜節點的 `properties`）。PostgreSQL 的 JSONB 型別可在同一顆資料庫內同時滿足兩種需求，避免多資料庫的維運與交易一致性成本；15 版對 JSONB 索引與查詢效能已相當成熟。
- **顯式 state machine：** `analysis_runs.status` 已在 S0 定義了分析管線的狀態機（`uploaded → document_parsing → ... → completed | review_required | failed`）。S1 將同樣的「顯式狀態機」精神延伸到 Agent 推理迴圈（`AgentState`: `PLANNING → EXECUTING_TOOL → ANSWERING → DONE | FAILED`），理由見決策 2。

## 決策 2：Agent 架構選擇（為何不用大型 agent framework）

**選擇：** Agent 推理迴圈以純 Python 實作的顯式 state machine 骨架，搭配三個可替換的 Protocol（`Planner`、`ToolExecutor`、`Answerer`），而非採用 LangChain、AutoGen、CrewAI 等現成 agent framework。

**理由：**

- **可稽核性優先：** `agent_steps` 表（S0 schema）要求每一步工具呼叫都保存 `tool_input`、`tool_output`、`citations`、`confidence`、`model_version`、`rule_version`。大型 framework 的 agent loop 通常把這些細節封裝在框架內部（例如 LangChain 的 `AgentExecutor`），要精確控制「每一步存什麼、何時存」需要繞過框架的抽象層，等於一開始就在對抗框架。手寫的顯式狀態機讓 `AgentStepRecord` 的產生時機與內容完全由我們自己的程式碼決定，天生對齊 `agent_steps` 的 schema。
- **黑箱風險：** 建築法規合規判定屬於高風險決策場景，若最終給使用者的答案來自一個不透明的 framework 內部重試/規劃邏輯，出錯時難以定位是「模型判斷錯」還是「框架邏輯錯」。顯式狀態機的每個轉移條件都是專案自己的程式碼，除錯與責任歸屬更清楚。
- **依賴與成本可控：** 大型 agent framework 版本更新頻繁、常帶入大量間接依賴（各種 vector store / LLM provider 整合），而 S1 階段實際只需要「依序呼叫 8 個白名單工具、記錄軌跡、產生答案」這個相對單純的迴圈。用 ~100 行的 `AgentStateMachine` 加三個 `Protocol` 就能達成，不需要為此引入一整個框架的學習與維護成本。
- **可替換設計：** `Planner` / `ToolExecutor` / `Answerer` 三個 Protocol 讓「決策邏輯」（未來可能是 LLM 呼叫）與「狀態機轉移邏輯」解耦。S2 要接上真正的 LLM 規劃器時，只需實作一個符合 `Planner` 介面的物件，不需要改動狀態機本身。

**工具白名單（鎖定於此 ADR，變更需更新此文件）：**

`parse_document`、`extract_building_ir`、`validate_geometry`、`retrieve_law`、`query_graph`、`run_rules`、`simulate_change`、`generate_report`（定義於 `backend/app/agent/tools.py` 的 `ToolName`）。

## 決策 3：Knowledge Graph 選型（PostgreSQL 優先，Neo4j 條件）

**選擇：** 以 PostgreSQL 的 `graph_nodes` / `graph_edges` 表（JSONB + recursive CTE）作為 Knowledge Graph 的儲存與查詢方案，暫不引入 Neo4j 或其他專用圖資料庫。

**理由：**

- **PoC 已驗證可行：** S1 的 Knowledge Graph PoC（見 [docs/2026-08-02-knowledge-graph-poc.md](../2026-08-02-knowledge-graph-poc.md)）證實 `Building → Floor → Space → Element → Path → Exit` 六層圖譜可用既有 schema 建立，且 PostgreSQL recursive CTE 與 NetworkX（讀入記憶體後查詢）兩種方式都能正確走訪、找出逃生路徑、正確回報無路徑情境。
- **維運與一致性成本：** 引入 Neo4j 代表要多維運一個資料庫系統，且圖譜資料與 `projects` / `analysis_runs` / `violations` 等關聯式資料之間的交易一致性（例如刪除一次分析執行時，圖譜資料要能透過 `ON DELETE CASCADE` 一併清除）會變得更複雜。PostgreSQL 方案讓所有資料留在同一顆資料庫、同一個交易邊界內。
- **現階段查詢需求可被滿足：** 目前已知的圖譜查詢需求（逃生路徑查找、模擬變更後受影響規則、Copilot 問答時查詢局部子圖）都屬於「單次分析執行、圖譜規模為單一建築物」的範圍，資料量遠低於需要專用圖資料庫的量級。

**改用 Neo4j（或其他專用圖資料庫）的觸發條件（滿足任一即重新評估）：**

1. 單一 `analysis_run_id` 下的圖譜規模成長到 PostgreSQL recursive CTE 或 NetworkX 記憶體查詢出現實測效能瓶頸（例如：P95 查詢延遲超過可接受範圍，且已加上 `docs/2026-08-02-knowledge-graph-poc.md` 中記錄的建議索引後仍無法改善）。
2. 需要 PostgreSQL recursive CTE 與 NetworkX 都難以高效支援的圖演算法（例如大規模最短路徑加權最佳化、社群偵測），且該演算法是產品需求的必要功能。
3. 多租戶情境下的圖查詢負載經效能量測證實是系統瓶頸（S2/S3 監控上線後才能取得這類數據）。

在以上任一條件被真實資料證實之前，維持 PostgreSQL 方案，避免在沒有實測效能壓力的情況下提前引入額外基礎設施。
