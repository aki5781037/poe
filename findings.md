# 关键证据
- `GET https://api.poe2scout.com/openapi.json` 返回 HTTP 200，Content-Type 为 `application/json`。
- Swagger 页面 `/swagger` 返回 HTTP 200，并配置 `url: '/api/openapi.json'`。
- OpenAPI paths 包含 `/{Realm}/Leagues`、`/{Realm}/Leagues/{LeagueName}/ExchangeSnapshot`、`/{Realm}/Leagues/{LeagueName}/SnapshotPairs`、`/{Realm}/Leagues/{LeagueName}/ReferenceCurrencies`、`/{Realm}/Leagues/{LeagueName}/Currencies/Pairs/{CurrencyOneItemId}/{CurrencyTwoItemId}/History`。
- 当前 `pc` realm 的 `IsCurrent=true` 联赛包括 `Mirage` 与 `Hardcore Mirage`。
- `GET /pc/Leagues/Mirage/ExchangeSnapshot` 返回 `Epoch: 1782018000`、`BaseCurrencyApiId: chaos`。
- `GET /pc/Leagues/Mirage/SnapshotPairs` 返回的 pair 包含 `CurrencyOne`、`CurrencyTwo`、`CurrencyOneData`、`CurrencyTwoData`，零成交示例会被策略排除。

# 命令结果
- `git status --short --branch`: `## No commits yet on master`
- `python --version`: 未取得版本，命令指向 `C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe` 且退出码 1。
- 结构检查确认需求文件均存在：`.github/workflows/scan.yml`、`config/*.yml`、`src/*.py`、`tests/*.py`、`docs/api-contract.md`、`README.md`、`.env.example`。
- `Select-String` 确认 workflow 包含 `workflow_dispatch`、`cron: "12 * * * *"`、`concurrency`、`contents: read`、`retention-days: 14`。
- 报告文本检索确认包含 `POE2 通貨套利候選報告`、历史聚合数据警告、无候选文案。
- 语言检索发现英文物品名只在 `tests/test_ratio_direction.py` 的 API 模拟数据中出现。

# 失败尝试
- 使用示例旧联赛 `Dawn of the Hunt` 请求 `ExchangeSnapshot` 返回 400。
- 本地未找到可执行 Python 3.12+，因此未能运行 `pytest` 或 `python -m src.main`。

# 决策原因
- `league: auto` 应通过 `/pc/Leagues` 的 `IsCurrent=true` 自动选择非 Hardcore 当前联赛。
- POE2 Scout 快照数据提供聚合相对价格与成交/库存字段，但未提供可直接还原订单簿的明确整数订单比例；默认报告验证阈值，不宣称可直接下单。
