import { STATUS_LABELS, type Status } from '../progress'
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
  const prereqs = skill.prereqs.filter((s) => bySlug.has(s))
  const unlocks = skill.unlocks.filter((s) => bySlug.has(s))
  return (
    <>
      <button type="button" className="back" onClick={() => onSelect(null)}>
        返回学习路线
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
      <div className="status" role="group" aria-label="学习状态">
        {STATUS_LABELS.map((label, i) => (
          <button type="button" key={label} aria-pressed={i === status} onClick={() => onStatus(i as Status)}>
            {label}
          </button>
        ))}
      </div>
      <h3>核心概念</h3>
      <ul>
        {skill.concepts.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>
      <h3>动手练习</h3>
      <p>{skill.practice}</p>
      <h3>学习资料</h3>
      <ul>
        {skill.resources.map((r) => (
          <li key={r.title}>
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
          <h3>先修</h3>
          <p className="links">
            <SkillLinks slugs={prereqs} bySlug={bySlug} onSelect={onSelect} />
          </p>
        </>
      )}
      {unlocks.length > 0 && (
        <>
          <h3>学完可以进入</h3>
          <p className="links">
            <SkillLinks slugs={unlocks} bySlug={bySlug} onSelect={onSelect} />
          </p>
        </>
      )}
    </>
  )
}
