# 目标
创建 Python 3.12+ 项目 `poe2-currency-flip`，用于基于 POE2 Scout 公开 API 生成小时级历史通货路径候选与游戏内复核阈值。

# 范围
- 当前仓库根目录项目文件、配置、测试、文档和 GitHub Actions。
- 使用 `https://api.poe2scout.com/openapi.json` 发现 API 契约。
- 默认扫描 `existing_holdings_only` 的 2 腿路径：起始通货 -> 中间通货/材料 -> 神聖石。

# 非目标
- 不使用游戏内存、封包、Cookie、自动点击或下单。
- 不输出实时盘口、当前可成交或直接下单结论。
- 不引入数据库。

# 阶段
1. 读取需求、确认 API OpenAPI 规范。
2. 创建项目结构、配置和核心模块。
3. 添加测试和 GitHub Actions。
4. 运行可用验证并记录结果。

# 验收标准
- `reports/latest.json` 与 `reports/latest.md` 可生成。
- API 契约记录实际端点、字段、方向约束和 ID 获取方式。
- pytest 测试覆盖关键安全规则。
- GitHub Actions 支持手动与定时运行，并上传 artifact。
