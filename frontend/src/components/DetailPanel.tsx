import { useT } from '../i18n'
import type { Status } from '../progress'
import type { Cluster, Company, Skill } from '../types'
import { SkillLinks } from './SkillLinks'

interface Props {
  skill: Skill
  cluster: Cluster | undefined
  companies: Company[]
  bySlug: Map<string, Skill>
  status: Status
  onStatus: (status: Status) => void
  onSelect: (slug: string | null) => void
}

export function DetailPanel({ skill, cluster, companies, bySlug, status, onStatus, onSelect }: Props) {
  const t = useT()
  const prereqs = skill.prereqs.filter((s) => bySlug.has(s))
  const unlocks = skill.unlocks.filter((s) => bySlug.has(s))
  return (
    <>
      <button type="button" className="back" onClick={() => onSelect(null)}>
        {t.back}
      </button>
      {cluster && (
        <div className="cl" style={{ color: cluster.color, marginTop: 14 }}>
          {cluster.name}
        </div>
      )}
      <h2>{skill.name}</h2>
      <p>{skill.description}</p>
      <div className="jd">
        {companies.map((c) => (
          <span key={c.code} className={skill.companies.includes(c.code) ? 'on' : ''}>
            {c.name}
          </span>
        ))}
      </div>
      <div className="status" role="group" aria-label={t.statusGroup}>
        {t.statusLabels.map((label, i) => (
          <button type="button" key={i} aria-pressed={i === status} onClick={() => onStatus(i as Status)}>
            {label}
          </button>
        ))}
      </div>
      <h3>{t.concepts}</h3>
      <ul>
        {skill.concepts.map((c, i) => (
          <li key={i}>{c}</li>
        ))}
      </ul>
      <h3>{t.practice}</h3>
      <p>{skill.practice}</p>
      <h3>{t.resources}</h3>
      <ul>
        {skill.resources.map((r, i) => (
          <li key={i}>
            {r.url ? (
              <a className="ext" href={r.url} target="_blank" rel="noopener">
                {r.title}
              </a>
            ) : (
              r.title
            )}
          </li>
        ))}
      </ul>
      {prereqs.length > 0 && (
        <>
          <h3>{t.prereqs}</h3>
          <p className="links">
            <SkillLinks slugs={prereqs} bySlug={bySlug} onSelect={onSelect} />
          </p>
        </>
      )}
      {unlocks.length > 0 && (
        <>
          <h3>{t.unlocks}</h3>
          <p className="links">
            <SkillLinks slugs={unlocks} bySlug={bySlug} onSelect={onSelect} />
          </p>
        </>
      )}
    </>
  )
}
