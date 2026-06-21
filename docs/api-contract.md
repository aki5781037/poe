# POE2 Scout API Contract

Base URL: `https://api.poe2scout.com`

Discovery source: `GET /openapi.json` returned HTTP 200 JSON. `/swagger` also returned HTML and points to `/api/openapi.json`.

## 實際使用的端點
- `GET /openapi.json`
- `GET /{Realm}/Leagues`
- `GET /{Realm}/Leagues/{LeagueName}/ExchangeSnapshot`
- `GET /{Realm}/Leagues/{LeagueName}/SnapshotPairs`
- `GET /{Realm}/Leagues/{LeagueName}/ReferenceCurrencies`
- `GET /{Realm}/Leagues/{LeagueName}/Currencies/Pairs/{CurrencyOneItemId}/{CurrencyTwoItemId}/History`

## 參數
- `Realm`: path string, from `config/strategy.yml`; default `pc`.
- `LeagueName`: path string. `league: auto` resolves from `GET /{Realm}/Leagues` where `IsCurrent=true`, preferring non-hardcore.
- `CurrencyOneItemId` / `CurrencyTwoItemId`: path integers from `CurrencyOne.CurrencyItemId` and `CurrencyTwo.CurrencyItemId`.
- `Limit`: required query integer for pair history.
- `EndEpoch`: optional query integer for pair history.

## 響應字段
- `ExchangeSnapshot`: `Epoch`, `Volume`, `MarketCap`, `BaseCurrencyApiId`, `BaseCurrencyText`.
- `SnapshotPairs`: `CurrencyExchangeSnapshotPairId`, `CurrencyExchangeSnapshotId`, `Volume`, `BaseCurrencyApiId`, `BaseCurrencyText`, `CurrencyOne`, `CurrencyTwo`, `CurrencyOneData`, `CurrencyTwoData`.
- `CurrencyItem`: `CurrencyItemId`, `ItemId`, `CurrencyCategoryId`, `ApiId`, `Text`, `CategoryApiId`, `IconUrl`, `ItemMetadata`.
- `PairData`: `ValueTraded`, `RelativePrice`, `StockValue`, `VolumeTraded`, `HighestStock`.

## 貨幣對比例方向
- `CurrencyOneData` and `CurrencyTwoData` are bound to API side labels.
- The scanner creates two directed edges per pair: `CurrencyOne -> CurrencyTwo` and `CurrencyTwo -> CurrencyOne`.
- Direction is recorded as `currency_one_to_two` or `currency_two_to_one`; it is never inferred from numeric magnitude.
- `RelativePrice` is a relative value, not a direct exchange direction. For `source -> target`, the derived amount is `paid_source * RelativePrice(source) / RelativePrice(target)`.
- Snapshot data is historical aggregate data and does not prove live order availability or directly executable integer orders.

## Realm、League、Currency Item ID 取得方法
- Realm: configured value, default `pc`.
- League: `GET /{Realm}/Leagues`; `auto` selects current non-hardcore league.
- Currency Item ID: `CurrencyOne.CurrencyItemId` / `CurrencyTwo.CurrencyItemId` from `GET /{Realm}/Leagues/{LeagueName}/SnapshotPairs`.

## 保守限制
- Field loss, non-JSON responses, unknown direction, unknown gold cost, stale snapshots, or unmapped Traditional Chinese names stop or exclude calculations.
- Reports must say historical candidate and in-game verification threshold only, not realtime executable order.
