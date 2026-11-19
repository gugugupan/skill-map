import { Fragment } from 'react'
import type { Skill } from '../types'

interface Props {
  slugs: string[]
  bySlug: Map<string, Skill>
  onSelect: (slug: string) => void
  isDone?: (slug: string) => boolean
}

export function SkillLinks({ slugs, bySlug, onSelect, isDone }: Props) {
  const known = slugs.filter((s) => bySlug.has(s))
  return known.map((slug, i) => (
    <Fragment key={slug}>
      {i > 0 && '、'}
      <button type="button" className={'slink' + (isDone?.(slug) ? ' done' : '')} onClick={() => onSelect(slug)}>
        {bySlug.get(slug)!.name}
      </button>
    </Fragment>
  ))
}
