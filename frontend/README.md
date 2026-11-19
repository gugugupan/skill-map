# frontend

Static skills graph site (React + Vite + TypeScript + D3), published to <https://gugugupan.github.io/skill-map/>.

Data is fetched from `public/data/*.json`, written by the pipeline's `export` step (not committed).

- `npm run dev` / `npm run build`: use `public/data/`.
- `npm run dev:fixtures` / `npm run build:fixtures`: use the hand-written sample in `fixtures/data/`.
- `npm run preview`: serve `dist/` at `/skill-map/`.

Learning progress is stored in `localStorage` under `agent-infra-progress`.
