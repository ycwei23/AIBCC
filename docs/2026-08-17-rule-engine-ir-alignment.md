# Rule Engine ↔ Building IR 對齊決策

**日期：** 2026-08-17
**回應：** `building-law-etl-main/docs/rule_engine_interface.md` §7.1「Building IR schema — target 路徑是否與 VLM 輸出一致？」

## 決策

**不改用 `floors[].exits[].width_mm` 巢狀結構。** `BuildingElement` 維持 S0/S1 已定案、DocAI/VLM adapter 已在用的扁平列表（`backend/app/models/ir.py`）。改為在 Rule Engine 這一側定義 `target` 字串如何解析回扁平元件，讓 `building-law-etl` 產出的規則包可以直接吃現有 IR，不需要黃蘭榛或陳芊宇重寫已發佈的 interface doc。

## 新增的對齊層（`backend/app/rules/`）

| 檔案 | 用途 |
|---|---|
| `loader.py` | `load_rule_bundle(bundle)`：把 `mvp_rules_active_v0.json` 這種外部規則包轉成內部 `Rule` list，只保留 `review_status == "active"` |
| `target_resolver.py` | `TARGET_ELEMENT_TYPES`：`target` 前綴（`exit`/`corridor`/`stair`/`evac`）→ `BuildingElement.type` 對照表；`scope_matches()`：評估 `scope.building_use` 與 `scope.conditions` |
| `engine.py` | `run_rules(elements, rules) -> list[Violation]`：實際評估邏輯（先前 `agent/tools.py` 的 `RunRulesInput/Output` 只有型別，沒有實作） |

## Target 路徑解析規則

`target = "<prefix>.<field>"`：

- `prefix` 對照 `TARGET_ELEMENT_TYPES` 找出要比對的 `BuildingElement.type`（如 `exit` → `{"exit", "exit_entrance"}`）
- 一般欄位（`width_mm`、`height_mm`、`walking_distance_m`）→ 讀 `element.geometry[field]`，逐一元件比對 `operator`/`threshold`
- `stair.count` 是唯一的聚合 target：因為 `BuildingElement` 目前沒有專屬樓層欄位，暫以 `page` 當樓層代理（一頁一樓層平面圖），依 `page` 分組計數

## Scope 過濾與新欄位

`rule_engine_interface.md` 的 scope 過濾（`building_use`、`location=evacuation_floor`、`floor_index>=8`、`corridor.both_sides_habitable` 等）需要元件層級的中繼資料，`BuildingElement` 目前沒有地方放。新增：

- `BuildingElement.metadata: dict[str, Any] = {}`（選填，預設空字典，不影響既有呼叫端）— 放 `building_use`、`floor_index`、`is_evacuation_floor`、`both_sides_habitable`、`room_floor_area_sqm`
- `Rule.law_code: str = ""`、`Rule.source_quote: str = ""`（選填）— 對齊外部規則包欄位，`source_quote` 用來組 `Violation.evidence`

`scope_matches()` 只實作 §3 表列出的 MVP 條件 token；遇到無法判定（`element.metadata` 缺欄位，或條件 token 不在白名單，例如 `use_part=classroom`、`element=exit_to_outdoor`）一律回傳 `None`，`run_rules` 會把該筆判成 `Violation.status = "insufficient_data"`，**不會**猜測 pass/fail。

## 真實規則包已接入（2026-08-17 更新）

`building-law-etl-main/data/mvp/mvp_rules_active_v0.json` 已 vendor 一份進 `backend/data/rules/mvp_rules_active_v0.json`（法規 ETL 是獨立 pipeline，不隨 backend 部署，所以用複製快照而非跨目錄即時讀取；黃蘭榛那邊發新版時要手動同步這份檔案）。`loader.py` 新增 `load_rules_from_file(path)` 直接讀檔。

`backend/tests/test_rule_bundle_integration.py` 用這份真實檔案（不是手寫的單一規則 fixture）驗證：
- 11 條 active 規則全部正確解析
- 用今天品綺 Benchmark 標註格式現有欄位（沒有 scope metadata）建的元件跑過全部 11 條規則 → 誠實回報 `insufficient_data`，不是猜的 pass/fail
- 補上 scope metadata 後（`both_sides_habitable`/`building_use`/`floor_index`），走廊與樓梯規則能算出真正的 `fail`/`pass`，證明 engine 對真實規則檔案的 11 種 target 都能正確解析、不只是先前手寫測試涵蓋的案例

## 已知限制 / 待辦

1. `page` 當樓層代理是暫定；等 VLM/DocAI 真的能標出樓層時要換成專屬欄位，而不是繼續依賴頁碼。
2. `use_part=classroom`、`element=exit_to_outdoor` 這類條件 token、`exceptions[]`、多規則衝突取最嚴（interface doc §7.3）都還沒實作，目前遇到就標 `insufficient_data`——這也是為什麼用現有 Benchmark 標註格式跑真實規則包時，11 條全部落在 `insufficient_data`（見上一節）。
3. `load_rules_from_file()` + `run_rules()` 尚未接進 `agent/tools.py` 的 `run_rules` tool executor（state machine 目前還是 stub）；模組本身已可直接呼叫，接線留給 S2 pipeline 串接任務。
4. 測試（`backend/tests/test_rule_engine.py`）重現了 `rule_engine_interface.md` §6 的 T1–T8 全部案例，另外驗證了「metadata 缺欄位 → insufficient_data，不是假通過」與「scope 排除 → 不出現在結果」。
