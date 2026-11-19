import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { DetailPanel } from './components/DetailPanel'
import { Graph } from './components/Graph'
import { HomePanel } from './components/HomePanel'
import { LangToggle } from './components/LangToggle'
import { RoleSwitcher } from './components/RoleSwitcher'
import { loadIndex, loadRole } from './data'
import { initialLang, LangContext, saveLang, STRINGS, useT, type Lang, type Strings } from './i18n'
import { useProgress } from './progress'
import type { Role, SiteIndex, SkillMapData } from './types'

const readRoleParam = () => new URLSearchParams(window.location.search).get('role')

function urlWithRole(slug: string) {
  const url = new URL(window.location.href)
  url.searchParams.set('role', slug)
  return url
}

function subtitle(t: Strings, index: SiteIndex, role: Role) {
  const d = new Date(index.meta.generated_at)
  return t.subtitle(role.counts.companies, role.counts.postings, role.name, Number.isNaN(d.getTime()) ? null : d)
}

const without = (prev: Record<string, string>, key: string) => {
  const next = { ...prev }
  delete next[key]
  return next
}

export default function App() {
  const [lang, setLang] = useState(initialLang)
  const t = STRINGS[lang]
  // Everything fetched is cached per language, so a switch never renders text from the other language.
  const [indexes, setIndexes] = useState<Partial<Record<Lang, SiteIndex>>>({})
  const [indexError, setIndexError] = useState<Partial<Record<Lang, string>>>({})
  const [roleParam, setRoleParam] = useState(readRoleParam)
  const [roleData, setRoleData] = useState<Record<string, SkillMapData>>({})
  const [roleError, setRoleError] = useState<Record<string, string>>({})

  const index = indexes[lang]
  const indexFailed = indexError[lang]
  useEffect(() => {
    if (index || indexFailed) return
    const ac = new AbortController()
    loadIndex(lang, ac.signal).then(
      (d) => setIndexes((prev) => ({ ...prev, [lang]: d })),
      (e: unknown) => {
        if (!ac.signal.aborted) setIndexError((prev) => ({ ...prev, [lang]: String(e) }))
      },
    )
    return () => ac.abort()
  }, [lang, index, indexFailed])

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

  useLayoutEffect(() => {
    document.documentElement.lang = t.htmlLang
    document.title = role ? t.mapTitle(role.name) : t.siteTitle
  }, [t, role])

  const roleKey = role ? `${lang}:${role.slug}` : ''
  const cached = role ? roleData[roleKey] : undefined
  const failed = role ? roleError[roleKey] : undefined
  useEffect(() => {
    // A failed role stays failed until the user retries, which clears its error and re-runs this effect.
    if (!index || !role || cached || failed) return
    // Responses are stored per language and slug, so a slow response for an earlier choice can never replace the current one.
    const key = `${index.lang}:${role.slug}`
    const ac = new AbortController()
    loadRole(index, role, ac.signal).then(
      (d) => setRoleData((prev) => ({ ...prev, [key]: d })),
      (e: unknown) => {
        if (!ac.signal.aborted) setRoleError((prev) => ({ ...prev, [key]: String(e) }))
      },
    )
    return () => ac.abort()
  }, [index, role, cached, failed])

  const retry = useCallback(() => {
    if (!indexFailed) setRoleError((prev) => without(prev, roleKey))
    else setIndexError((prev) => without(prev, lang))
  }, [indexFailed, roleKey, lang])

  const selectRole = useCallback((slug: string) => {
    window.history.pushState(null, '', urlWithRole(slug))
    setRoleParam(slug)
  }, [])

  const selectLang = useCallback((next: Lang) => {
    saveLang(next)
    setLang(next)
  }, [])

  const loadError = indexFailed ?? failed
  return (
    <LangContext.Provider value={lang}>
      <RoleView
        data={cached}
        status={loadError ? t.loadFailed(loadError) : index && !role ? t.noRoles : t.loading}
        canRetry={loadError !== undefined}
        onRetry={retry}
        switcher={
          <div className="title-row">
            {index && role ? (
              <RoleSwitcher roles={index.roles} current={role} onChange={selectRole} />
            ) : (
              <h1>{t.siteTitle}</h1>
            )}
            <LangToggle lang={lang} onChange={selectLang} />
          </div>
        }
        sub={index && role ? subtitle(t, index, role) : ''}
        roleSlug={role?.slug}
      />
    </LangContext.Provider>
  )
}

interface RoleViewProps {
  data: SkillMapData | undefined
  status: string
  canRetry: boolean
  onRetry: () => void
  switcher: ReactNode
  sub: string
  roleSlug: string | undefined
}

// Always mounted and not keyed by role: the switcher and language toggle keep their DOM nodes (and focus) across
// a switch, and the selected skill and company filter (slug / code based) survive a language switch.
function RoleView({ data, status, canRetry, onRetry, switcher, sub, roleSlug }: RoleViewProps) {
  const t = useT()
  const [filter, setFilter] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [shownRole, setShownRole] = useState(roleSlug)
  // roleSlug is undefined while a language's index loads; that is not a role change.
  if (roleSlug !== undefined && shownRole !== roleSlug) {
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
          {status}
          {canRetry && (
            <button type="button" className="chip retry" onClick={onRetry}>
              {t.retry}
            </button>
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
          <span>{t.progress(done, total, doing)}</span>
        </div>
        <div className="filters" role="group" aria-label={t.filterGroup}>
          {[{ code: null, name: t.allCompanies }, ...data.companies].map((c) => (
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
          <div className="hint">{t.hint}</div>
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
