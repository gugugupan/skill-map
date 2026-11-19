import { useEffect, useMemo, useRef, useState } from 'react'
import { DetailPanel } from './components/DetailPanel'
import { Graph } from './components/Graph'
import { HomePanel } from './components/HomePanel'
import { loadData } from './data'
import { useProgress } from './progress'
import type { SkillMapData } from './types'

function subtitle({ meta }: SkillMapData) {
  const d = new Date(meta.generated_at)
  const when = Number.isNaN(d.getTime()) ? '' : `（${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日更新）`
  return `来自 ${meta.counts.companies} 家公司、${meta.counts.postings} 份 Agent Infra 相关 JD 的能力地图${when}`
}

export default function App() {
  const [data, setData] = useState<SkillMapData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [progress, setStatus] = useProgress()
  const panelRef = useRef<HTMLElement>(null)

  useEffect(() => {
    let cancelled = false
    loadData().then(
      (d) => !cancelled && setData(d),
      (e: unknown) => !cancelled && setError(String(e)),
    )
    return () => {
      cancelled = true
    }
  }, [])

  const bySlug = useMemo(() => new Map((data?.skills ?? []).map((s) => [s.slug, s])), [data])

  useEffect(() => {
    panelRef.current?.scrollTo(0, 0)
  }, [selected])

  if (!data) {
    return <div className="loading">{error ? `数据加载失败：${error}` : '加载中…'}</div>
  }

  const skill = selected ? bySlug.get(selected) : undefined
  const total = data.skills.length
  const done = data.skills.filter((s) => progress[s.slug] === 2).length
  const doing = data.skills.filter((s) => progress[s.slug] === 1).length

  return (
    <div className="app">
      <header>
        <div>
          <h1>Agent Infra 知识图谱</h1>
          <div className="sub">{subtitle(data)}</div>
        </div>
        <div className="prog">
          <div className="bar">
            <i style={{ width: `${total ? (done / total) * 100 : 0}%` }} />
          </div>
          <span>
            已掌握 {done} / {total}，学习中 {doing}
          </span>
        </div>
        <div className="filters" role="group" aria-label="按公司筛选">
          {[{ code: null, name: '全部' }, ...data.companies].map((c) => (
            <button type="button" key={c.code ?? ''} className="chip" aria-pressed={filter === c.code} onClick={() => setFilter(c.code)}>
              {c.name}
            </button>
          ))}
        </div>
      </header>
      <main>
        <div id="graph">
          <Graph data={data} filter={filter} selected={selected} progress={progress} onSelect={setSelected} />
          <div className="legend">
            {data.clusters.map((c) => (
              <span key={c.slug}>
                <b style={{ background: c.color }} />
                {c.name}
              </span>
            ))}
          </div>
          <div className="hint">拖动平移，滚轮缩放，点击节点查看</div>
        </div>
        <aside ref={panelRef} aria-live="polite">
          {skill ? (
            <DetailPanel
              skill={skill}
              cluster={data.clusters.find((c) => c.slug === skill.cluster)}
              companies={data.companies}
              bySlug={bySlug}
              status={progress[skill.slug] ?? 0}
              onStatus={(s) => setStatus(skill.slug, s)}
              onSelect={setSelected}
            />
          ) : (
            <HomePanel data={data} bySlug={bySlug} progress={progress} onSelect={setSelected} />
          )}
        </aside>
      </main>
    </div>
  )
}
