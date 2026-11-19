import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { DetailPanel } from './components/DetailPanel'
import { Graph } from './components/Graph'
import { HomePanel } from './components/HomePanel'
import { RoleSwitcher } from './components/RoleSwitcher'
import { loadIndex, loadRole } from './data'
import { useProgress } from './progress'
import type { Role, SiteIndex, SkillMapData } from './types'

const readRoleParam = () => new URLSearchParams(window.location.search).get('role')

function urlWithRole(slug: string) {
  const url = new URL(window.location.href)
  url.searchParams.set('role', slug)
  return url
}

function subtitle(index: SiteIndex, role: Role) {
  const d = new Date(index.meta.generated_at)
  const when = Number.isNaN(d.getTime()) ? '' : `（${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日更新）`
  return `来自 ${role.counts.companies} 家公司、${role.counts.postings} 份 ${role.name}相关 JD 的能力地图${when}`
}

export default function App() {
  const [index, setIndex] = useState<SiteIndex | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [roleParam, setRoleParam] = useState(readRoleParam)
  const [roleData, setRoleData] = useState<Record<string, SkillMapData>>({})
  const [roleError, setRoleError] = useState<Record<string, string>>({})

  useEffect(() => {
    let cancelled = false
    loadIndex().then(
      (d) => !cancelled && setIndex(d),
      (e: unknown) => !cancelled && setError(String(e)),
    )
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const onPop = () => setRoleParam(readRoleParam())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const role = index ? (index.roles.find((r) => r.slug === roleParam) ?? index.roles[0]) : undefined

  useEffect(() => {
    if (!role || roleParam === role.slug) return
    window.history.replaceState(window.history.state, '', urlWithRole(role.slug))
  }, [role, roleParam])

  useEffect(() => {
    if (role) document.title = `${role.name} 知识图谱`
  }, [role])

  const cached = role ? roleData[role.slug] : undefined
  const failed = role ? roleError[role.slug] : undefined
  useEffect(() => {
    // A failed role stays failed until the user retries, which clears its error and re-runs this effect.
    if (!index || !role || cached || failed) return
    // Responses are stored per slug, so a slow response for an earlier role can never replace the current one.
    const ac = new AbortController()
    loadRole(index, role, ac.signal).then(
      (d) => setRoleData((prev) => ({ ...prev, [role.slug]: d })),
      (e: unknown) => {
        if (!ac.signal.aborted) setRoleError((prev) => ({ ...prev, [role.slug]: String(e) }))
      },
    )
    return () => ac.abort()
  }, [index, role, cached, failed])

  const retryRole = useCallback((slug: string) => {
    setRoleError((prev) => {
      const next = { ...prev }
      delete next[slug]
      return next
    })
  }, [])

  const selectRole = useCallback((slug: string) => {
    window.history.pushState(null, '', urlWithRole(slug))
    setRoleParam(slug)
  }, [])

  if (!index || !role) {
    const msg = error ? `数据加载失败：${error}` : index ? '暂无岗位数据' : '加载中…'
    return <div className="loading">{msg}</div>
  }

  return (
    <RoleView
      data={cached}
      loadError={failed}
      onRetry={() => retryRole(role.slug)}
      switcher={<RoleSwitcher roles={index.roles} current={role} onChange={selectRole} />}
      sub={subtitle(index, role)}
      roleSlug={role.slug}
    />
  )
}

interface RoleViewProps {
  data: SkillMapData | undefined
  loadError: string | undefined
  onRetry: () => void
  switcher: ReactNode
  sub: string
  roleSlug: string
}

// Not keyed by role: the switcher must keep its DOM node (and focus) across a switch.
function RoleView({ data, loadError, onRetry, switcher, sub, roleSlug }: RoleViewProps) {
  const [filter, setFilter] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [shownRole, setShownRole] = useState(roleSlug)
  if (shownRole !== roleSlug) {
    setShownRole(roleSlug)
    setFilter(null)
    setSelected(null)
  }
  const [progress, setStatus] = useProgress()
  const panelRef = useRef<HTMLElement>(null)

  const bySlug = useMemo(() => new Map((data?.skills ?? []).map((s) => [s.slug, s])), [data])

  useEffect(() => {
    panelRef.current?.scrollTo(0, 0)
  }, [selected])

  if (!data) {
    return (
      <div className="app">
        <header>
          <div>
            {switcher}
            <div className="sub">{sub}</div>
          </div>
        </header>
        <div className="loading">
          {loadError ? (
            <>
              数据加载失败：{loadError}
              <button type="button" className="chip retry" onClick={onRetry}>
                重试
              </button>
            </>
          ) : (
            '加载中…'
          )}
        </div>
      </div>
    )
  }

  const skill = selected ? bySlug.get(selected) : undefined
  const total = data.skills.length
  const done = data.skills.filter((s) => progress[s.slug] === 2).length
  const doing = data.skills.filter((s) => progress[s.slug] === 1).length

  return (
    <div className="app">
      <header>
        <div>
          {switcher}
          <div className="sub">{sub}</div>
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
