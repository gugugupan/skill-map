# CLAUDE.md

完整设计见 @docs/DESIGN.md。

## 架构

GitHub Pages 静态站，没有常驻后端（覆盖设计文档里的 FastAPI / 本地平台）：

- 管线脚本（`backend/`，Python 3.12 + uv）把数据存进 SQLite，`export` 导出静态 JSON 到 `frontend/public/data/`。
- 前端（`frontend/`，React + Vite + D3）构建后由 GitHub Actions 发布到 <https://gugugupan.github.io/skill-map/>，`base` 为 `/skill-map/`。
- 学习进度存在浏览器 `localStorage`。
- 运行 Python 一律 `cd backend && uv run ...`。默认 DB 路径为 `<repo>/data/skillmap.db`（按 `__file__` 解析），可用环境变量 `SKILLMAP_DB` 覆盖。

## 约定

- 按里程碑推进，每个里程碑结束前先跑测试和金标准评测，再进入下一个。
- 单元测试中不调用真实 LLM，用录制好的响应做 mock；真实调用只出现在评测脚本中。
- 所有 prompt 放在 `prompts/` 目录，文件名带版本号；`extractor_version` 由模型名和 prompt 版本拼成。
- LLM 输出一律用 JSON schema 约束，并在代码中校验。
- API Key 从环境变量读取（`ANTHROPIC_API_KEY` 等），不写入仓库。
- 采集模块必须限速，并在请求头中标明用途。
- 遇到设计文档未覆盖的取舍，先在 `docs/decisions/` 下写一条简短记录，再实现。
