# Knowledge Graph PoC 結果

**日期：** 2026-08-02
**範圍：** S1 里程碑「Knowledge Graph PoC」的查詢範例與初步效能觀察，對應程式碼見 `backend/app/graph/`。

## 1. Schema

沿用 S0 已建立的 `graph_nodes` / `graph_edges` 表（`backend/migrations/init.sql`），本階段未新增或修改任何資料表，僅在既有 schema 上撰寫查詢與遍歷邏輯。

`graph_nodes.node_type` 的 CHECK 限制涵蓋 `Building`、`Floor`、`Space`、`Element`、`Path`、`Exit`、`Rule` 七種節點類型，`properties` 為 JSONB 欄位存放節點的額外屬性（如樓層編號、房間坪數、門寬）。`graph_edges` 以 `from_node` / `relation` / `to_node` 三欄描述有向邊，並以 `analysis_run_id` 隔離不同分析執行的圖譜資料，兩張表皆已有對應索引（`idx_graph_nodes_run_id`、`idx_graph_edges_run_id`）。

## 2. 範例資料集

`backend/app/graph/builder.py` 的 `build_sample_building_graph()` 建立一組代表單一樓層的示範圖譜（8 節點、8 邊）：

```
building-1 --contains--> floor-1
floor-1 --contains--> space-room-101
floor-1 --contains--> space-corridor-1
floor-1 --contains--> space-room-103        (無逃生路徑，用於驗證「查無路徑」情境)
space-room-101 --connects_via--> element-door-101
element-door-101 --connects_via--> space-corridor-1
space-corridor-1 --leads_to--> path-corridor-to-exit
path-corridor-to-exit --leads_to--> exit-1
```

`space-room-103` 刻意只透過 `contains` 掛在樓層下，沒有任何 `connects_via` / `leads_to` 邊通往 `exit-1` —— 這對應真實情境中「房間存在但沒有合法逃生動線」的違規案例，用來驗證遍歷邏輯能正確回報「查無路徑」而非誤判或拋錯。

## 3. NetworkX 查詢範例

`to_networkx_graph()` 將節點/邊轉為 `networkx.DiGraph`，可依 `relations` 參數篩選子圖。`find_escape_path()` 只在「動線關係」（`connects_via`、`leads_to`）子圖上用 `nx.shortest_path` 找最短逃生路徑：

```python
from app.graph.builder import build_sample_building_graph, to_networkx_graph, find_escape_path, CIRCULATION_RELATIONS

nodes, edges = build_sample_building_graph()
circulation = to_networkx_graph(nodes, edges, relations=CIRCULATION_RELATIONS)

find_escape_path(circulation, "space-room-101")
# ['space-room-101', 'element-door-101', 'space-corridor-1', 'path-corridor-to-exit', 'exit-1']

find_escape_path(circulation, "space-room-103")
# None  — 正確回報查無逃生路徑
```

**效能觀察：** PoC 規模（8 節點）下 `nx.shortest_path` 為毫秒等級，可忽略不計。NetworkX 的優勢在於整個圖已讀進記憶體後，可直接呼叫豐富的圖演算法函式庫（`shortest_path`、`all_simple_paths`、`has_path` 等），適合 Copilot 問答、模擬變更（`/simulate`）等需要「載入一次分析執行的完整圖譜、反覆查詢」的線上互動場景。

## 4. PostgreSQL Recursive CTE 查詢範例

`backend/app/graph/recursive_query.py` 的 `query_descendants()` 用 `WITH RECURSIVE` 從指定節點出發，沿 `from_node → to_node` 邊（不分 relation 種類）往下找所有可達節點：

```sql
WITH RECURSIVE descendants AS (
    SELECT from_node, to_node, relation, 1 AS depth
    FROM graph_edges
    WHERE analysis_run_id = :analysis_run_id AND from_node = :start_node_id
    UNION ALL
    SELECT e.from_node, e.to_node, e.relation, d.depth + 1
    FROM graph_edges e
    JOIN descendants d ON e.from_node = d.to_node
    WHERE e.analysis_run_id = :analysis_run_id
)
SELECT to_node, relation, depth FROM descendants ORDER BY depth, to_node
```

以 `building-1` 為起點，實際執行結果（10 筆）：

| to_node | relation | depth |
|---|---|---|
| floor-1 | contains | 1 |
| space-corridor-1 | contains | 2 |
| space-room-101 | contains | 2 |
| space-room-103 | contains | 2 |
| element-door-101 | connects_via | 3 |
| path-corridor-to-exit | leads_to | 3 |
| exit-1 | leads_to | 4 |
| space-corridor-1 | connects_via | 4 |
| path-corridor-to-exit | leads_to | 5 |
| exit-1 | leads_to | 6 |

**觀察 1（菱形路徑導致重複）：** `space-corridor-1` 同時被 `floor-1 --contains-->` 與 `element-door-101 --connects_via-->` 兩條路徑指向，形成「菱形」結構，導致 `space-corridor-1`（depth 2 與 4）與其下游的 `path-corridor-to-exit`（depth 3 與 5）、`exit-1`（depth 4 與 6）都各出現兩次。這是 recursive CTE 對 DAG（非樹狀）圖譜的正常行為，並非無窮迴圈（本例在 depth 6 自然終止），但意謂著「列出所有可達節點」的查詢在真實資料上應加 `DISTINCT to_node` 或在應用層去重，否則同一節點會依路徑數量重複出現。

**觀察 2（索引覆蓋現況）：** 每一層遞迴的 `WHERE e.analysis_run_id = :analysis_run_id` 都能命中既有的 `idx_graph_edges_run_id` 索引，但 `JOIN descendants d ON e.from_node = d.to_node` 這個 join 條件目前沒有專屬索引（`graph_edges.from_node` 未建索引）。PoC 規模（個位數邊數）下差異可忽略，但正式資料若單一 `analysis_run_id` 下有數千條邊，這個 join 會退化成循序掃描。**待正式資料量出現效能訊號時**（S2/S3），建議新增 `CREATE INDEX idx_graph_edges_from_node ON graph_edges(analysis_run_id, from_node);`——本 PoC 階段先不加，避免在無實際效能數據前過早優化。

## 5. 結論

- `graph_nodes` / `graph_edges` 的既有 schema 足以承載 `Building → Floor → Space → Element → Path → Exit` 六層圖譜，兩種查詢方式（PostgreSQL recursive CTE、NetworkX）皆驗證可用。
- 建議分工：**NetworkX** 用於需要反覆互動查詢同一份圖譜的場景（Copilot 問答、`/simulate` 模擬變更）——把一次分析執行的圖譜整個讀進記憶體後查詢；**PostgreSQL recursive CTE** 用於一次性、報表式的資料庫端查詢（例如 `/graph` API 直接回傳節點/邊），不需要先把資料轉成 Python 物件。
- 兩者皆需注意 DAG 的多路徑重複節點問題（見上方觀察 1），實作正式查詢邏輯時應明確決定是否需要去重。
