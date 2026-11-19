import { LANGS, useT, type Lang } from '../i18n'

const LABELS: Record<Lang, { short: string; name: string; tag: string }> = {
  zh: { short: '中', name: '中文', tag: 'zh-CN' },
  en: { short: 'EN', name: 'English', tag: 'en' },
}

interface Props {
  lang: Lang
  onChange: (lang: Lang) => void
}

export function LangToggle({ lang, onChange }: Props) {
  const t = useT()
  return (
    <div className="lang" role="group" aria-label={t.langGroup}>
      {LANGS.map((l) => (
        <button
          type="button"
          key={l}
          lang={LABELS[l].tag}
          aria-label={LABELS[l].name}
          aria-pressed={l === lang}
          onClick={() => l !== lang && onChange(l)}
        >
          {LABELS[l].short}
        </button>
      ))}
    </div>
  )
}
