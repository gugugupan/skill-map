import { Fragment } from 'react'
import { useT } from '../i18n'
import type { Skill } from '../types'

interface Props {
  slugs: string[]
  bySlug: Map<string, Skill>
  onSelect: (slug: string) => void
  isDone?: (slug: string) => boolean
}

export function SkillLinks({ slugs, bySlug, onSelect, isDone }: Props) {
  const t = useT()
  const known = slugs.filter((s) => bySlug.has(s))
  // Each separator stays on the line of the name before it, so a wrapped line never starts with one.
  return known.map((slug, i) => (
    <Fragment key={slug}>
      {i > 0 && t.listGap}
      <span className="slink-item">
        <button type="button" className={'slink' + (isDone?.(slug) ? ' done' : '')} onClick={() => onSelect(slug)}>
          {bySlug.get(slug)!.name}
        </button>
        {i < known.length - 1 && t.listSep}
      </span>
    </Fragment>
  ))
}
