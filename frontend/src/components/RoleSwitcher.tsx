import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import type { Role } from '../types'

interface Props {
  roles: Role[]
  current: Role
  onChange: (slug: string) => void
}

export function RoleSwitcher({ roles, current, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const listId = useId()

  const show = () => {
    setActive(Math.max(0, roles.findIndex((r) => r.slug === current.slug)))
    setOpen(true)
  }
  const close = (refocus: boolean) => {
    setOpen(false)
    if (refocus) buttonRef.current?.focus()
  }
  const choose = (slug: string) => {
    close(true)
    if (slug !== current.slug) onChange(slug)
  }

  useEffect(() => {
    if (!open) return
    listRef.current?.focus()
    const onDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onDown)
    return () => document.removeEventListener('pointerdown', onDown)
  }, [open])

  useEffect(() => {
    if (open) listRef.current?.children[active]?.scrollIntoView({ block: 'nearest' })
  }, [open, active])

  const onButtonKey = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      show()
    }
  }

  const onListKey = (e: KeyboardEvent) => {
    const last = roles.length - 1
    switch (e.key) {
      case 'ArrowDown':
        setActive((i) => (i >= last ? 0 : i + 1))
        break
      case 'ArrowUp':
        setActive((i) => (i <= 0 ? last : i - 1))
        break
      case 'Home':
        setActive(0)
        break
      case 'End':
        setActive(last)
        break
      case 'Enter':
      case ' ':
        choose(roles[active].slug)
        break
      case 'Escape':
        close(true)
        break
      case 'Tab':
        setOpen(false)
        return
      default:
        return
    }
    e.preventDefault()
  }

  return (
    <div className="switcher" ref={rootRef}>
      <h1>
        <button
          ref={buttonRef}
          type="button"
          className="switcher-btn"
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={open ? listId : undefined}
          aria-label={`${current.name} 知识图谱，切换岗位`}
          onClick={() => (open ? close(false) : show())}
          onKeyDown={onButtonKey}
        >
          {current.name} 知识图谱
          <svg className="caret" viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </button>
      </h1>
      {open && (
        <ul
          ref={listRef}
          id={listId}
          className="switcher-list"
          role="listbox"
          aria-label="选择岗位"
          tabIndex={-1}
          aria-activedescendant={`${listId}-${active}`}
          onKeyDown={onListKey}
        >
          {roles.map((r, i) => (
            <li
              key={r.slug}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={r.slug === current.slug}
              className={i === active ? 'active' : undefined}
              onPointerMove={() => setActive(i)}
              onClick={() => choose(r.slug)}
            >
              <span className="name">{r.name}</span>
              <span className="meta">
                {r.counts.skills} 个能力点 · {r.counts.postings} 份 JD
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
