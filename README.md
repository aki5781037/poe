# poe2-currency-flip

> 当前仓库是 Public。未来若加入 GGG OAuth、Telegram Token、Discord Webhook 或个人联系方式，必须先改为 Private Repository，并将凭据放入 GitHub Secrets / Variables。

`poe2-currency-flip` 是 POE2 國際服通貨交易所小時級歷史候選掃描器。它只使用 POE2 Scout 公開 API，輸出歷史聚合數據候選與遊戲內複核閾值，不是實時盤口工具，也不會自動點擊、讀取封包、使用 Cookie 或下單。

RelativePrice 是相对价值，不是直接兑换方向；路径计算必须使用 `source_price / target_price`。

## 快速開始

1. 在 GitHub 建立 Private Repository，將本專案推送到該私有倉庫。
2. 進入 GitHub repository 的 Actions 頁面，允許 workflows 執行。
3. 打開 `POE2 Currency Flip Scan` workflow，點擊 `Run workflow` 手動執行。
4. 執行完成後，在 workflow run 的 Summary 查看 `reports/latest.md`，並在 Artifacts 下載 raw API 響應與報告。

## 本地執行

```bash
python -m pip install -e .[dev]
pytest
python -m src.main
```

輸出文件：

- `reports/latest.json`
- `reports/latest.md`
- `reports/raw/*.json`
- `docs/api-contract.md`

## 配置

- `config/portfolio.yml`: 配置實際持有資產與金幣餘額。默認 `execution_mode: existing_holdings_only`，只從餘額大於 0 的起始通貨計算可複核候選。
- `config/routing.yml`: 配置目標通貨、可作為起點的基礎通貨、最大腿數。默認只掃描 2 腿路徑：基礎通貨 → 材料/中間通貨 → 神聖石。
- `config/market-reference.yml`: 配置正式可交易项目的繁体中文名、金幣成本、来源 URL、核对日期和备注。没有 `source_url` 和 `verified_at` 的金幣成本一律视为未知。
- `config/gold.yml`: 旧版兼容配置，不作为正式金幣来源。
- `config/names.zh-Hant.yml`: 配置 API ID 到國際服繁體中文名稱。未映射名稱不會進入正式候選報告。
- `config/strategy.yml`: 配置最小歷史利潤率、快照最大延遲、測試倉位比例、顯示時區等。

## 為什麼不是實時盤口工具

POE2 Scout 的快照是已完成小時的歷史聚合數據，成交量只能作為歷史流動性參考，不能冒充當前訂單簿深度。本工具不輸出「實時可成交」或「直接下單」結論；即使出現候選，也必須在遊戲內「可用交易」界面按報告閾值複核。

## GitHub Actions

`.github/workflows/scan.yml` 支持：

- `workflow_dispatch` 手動執行。
- UTC 每小時第 12 分鐘執行：`12 * * * *`。
- concurrency 防止重疊運行。
- 最小權限：`contents: read`。
- 上傳 raw 響應與報告為 Artifact，保存 14 天。
- 將 `latest.md` 寫入 GitHub Step Summary。

## NAS cron 遷移

未來遷移到 NAS 時，保留同樣的命令邊界：安裝依賴、執行 `python -m src.main`、保存 `reports/` 和 `reports/raw/`。不要加入資料庫或長駐程序，除非先明確設計保留期、錯誤告警和憑據管理。

## 安全邊界

- API 基址固定為 `https://api.poe2scout.com`。
- 啟動時讀取 OpenAPI 契約；字段缺失、非 JSON、未知比例方向、未知金幣或未映射繁中名稱會停止或排除相關計算。
- 比率方向由 API 的 `CurrencyOne` / `CurrencyTwo` 側明確建模，不靠數字大小猜測。
