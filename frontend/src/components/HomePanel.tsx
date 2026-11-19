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
  const top = [...data.skills].sort((a, b) => b.companies.length - a.companies.length).slice(0, 8)
  const coverage = (code: string) => data.skills.filter((s) => s.companies.includes(code)).length
  return (
    <>
      <h2>学习路线</h2>
      <p>节点越大，被越多公司提到。空心是未开始，半透明是学习中，实心是已掌握。虚线表示先修关系。</p>
      <h3>被最多公司提到</h3>
      <ol>
        {top.map((s) => (
          <li key={s.slug}>
            <span className="links">
              <SkillLinks slugs={[s.slug]} bySlug={bySlug} onSelect={onSelect} />
            </span>
            （{s.companies.length} 家）
          </li>
        ))}
      </ol>
      <h3>建议顺序</h3>
      <ol className="path">
        {data.roadmap.phases.map((phase) => (
          <li key={phase.title}>
            <strong>{phase.title}</strong>
            <br />
            <SkillLinks slugs={phase.skills} bySlug={bySlug} onSelect={onSelect} isDone={(slug) => progress[slug] === 2} />
          </li>
        ))}
      </ol>
      <h3>JD 来源</h3>
      {data.sources.map((src) => (
        <div key={src.code}>
          <p style={{ marginBottom: 4 }}>
            <strong>{src.name}</strong>（覆盖 {coverage(src.code)} 个节点）
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
