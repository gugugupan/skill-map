import { useT } from '../i18n'
import type { Progress } from '../progress'
import type { Skill, SkillMapData } from '../types'
import { SkillLinks } from './SkillLinks'

interface Props {
  data: SkillMapData
  bySlug: Map<string, Skill>
  progress: Progress
  onSelect: (slug: string) => void
}

export function HomePanel({ data, bySlug, progress, onSelect }: Props) {
  const t = useT()
  const top = [...data.skills].sort((a, b) => b.companies.length - a.companies.length).slice(0, 8)
  const coverage = (code: string) => data.skills.filter((s) => s.companies.includes(code)).length
  return (
    <>
      <h2>{t.pathTitle}</h2>
      <p>{t.pathIntro}</p>
      <h3>{t.topMentioned}</h3>
      <ol>
        {top.map((s) => (
          <li key={s.slug}>
            <span className="links">
              <SkillLinks slugs={[s.slug]} bySlug={bySlug} onSelect={onSelect} />
            </span>
            {t.companyCount(s.companies.length)}
          </li>
        ))}
      </ol>
      <h3>{t.suggestedOrder}</h3>
      <ol className="path">
        {data.roadmap.phases.map((phase, i) => (
          <li key={i}>
            <strong>{phase.title}</strong>
            <br />
            <SkillLinks slugs={phase.skills} bySlug={bySlug} onSelect={onSelect} isDone={(slug) => progress[slug] === 2} />
          </li>
        ))}
      </ol>
      <h3>{t.sources}</h3>
      {data.sources.map((src) => (
        <div key={src.code}>
          <p style={{ marginBottom: 4 }}>
            <strong>{src.name}</strong>
            {t.coverage(coverage(src.code))}
          </p>
          <ul style={{ marginBottom: 10 }}>
            {src.jobs.map((job, i) => (
              <li key={i}>
                {job.url ? (
                  <a className="ext" href={job.url} target="_blank" rel="noopener">
                    {job.title}
                  </a>
                ) : (
                  job.title
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </>
  )
}
