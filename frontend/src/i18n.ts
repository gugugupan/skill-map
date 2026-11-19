import { createContext, useContext } from 'react'

export type Lang = 'zh' | 'en'
export const LANGS: readonly Lang[] = ['zh', 'en']

const STORAGE_KEY = 'skill-map-lang'
const isLang = (v: unknown): v is Lang => v === 'zh' || v === 'en'

function readStoredLang(): Lang | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    return isLang(v) ? v : null
  } catch {
    return null
  }
}

export function saveLang(lang: Lang) {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // storage can be unavailable (private mode); the choice then lives for this session only
  }
}

let initial: Lang | undefined

// `?lang=` is an entry parameter: it is consumed once and removed, so it never fights the toggle or history.
// Memoised because StrictMode calls state initialisers twice and the URL is already clean the second time.
export function initialLang(): Lang {
  if (initial) return initial
  const url = new URL(window.location.href)
  const param = url.searchParams.get('lang')
  if (url.searchParams.has('lang')) {
    url.searchParams.delete('lang')
    window.history.replaceState(window.history.state, '', url)
  }
  if (isLang(param)) {
    saveLang(param)
    initial = param
  } else {
    initial = readStoredLang() ?? (navigator.language?.toLowerCase().startsWith('zh') ? 'zh' : 'en')
  }
  return initial
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

const zh = {
  htmlLang: 'zh-CN',
  siteTitle: '知识图谱',
  mapTitle: (role: string) => `${role} 知识图谱`,
  subtitle: (companies: number, postings: number, role: string, date: Date | null) =>
    `来自 ${companies} 家公司、${postings} 份 ${role}相关 JD 的能力地图` +
    (date ? `（${date.getFullYear()} 年 ${date.getMonth() + 1} 月 ${date.getDate()} 日更新）` : ''),
  switcherLabel: (role: string) => `${role} 知识图谱，切换岗位`,
  chooseRole: '选择岗位',
  roleMeta: (skills: number, postings: number) => `${skills} 个能力点 · ${postings} 份 JD`,
  langGroup: '界面语言',
  loading: '加载中…',
  loadFailed: (err: string) => `数据加载失败：${err}`,
  noRoles: '暂无岗位数据',
  retry: '重试',
  progress: (done: number, total: number, doing: number) => `已掌握 ${done} / ${total}，学习中 ${doing}`,
  filterGroup: '按公司筛选',
  allCompanies: '全部',
  hint: '拖动平移，滚轮缩放，点击节点查看',
  graphLabel: '知识图谱',
  back: '返回学习路线',
  statusGroup: '学习状态',
  statusLabels: ['未开始', '学习中', '已掌握'] as readonly string[],
  concepts: '核心概念',
  practice: '动手练习',
  resources: '学习资料',
  prereqs: '先修',
  unlocks: '学完可以进入',
  pathTitle: '学习路线',
  pathIntro: '节点越大，被越多公司提到。空心是未开始，半透明是学习中，实心是已掌握。虚线表示先修关系。',
  topMentioned: '被最多公司提到',
  companyCount: (n: number) => `（${n} 家）`,
  suggestedOrder: '建议顺序',
  sources: 'JD 来源',
  coverage: (n: number) => `（覆盖 ${n} 个节点）`,
  listSep: '、',
}

export type Strings = typeof zh

const en: Strings = {
  htmlLang: 'en',
  siteTitle: 'Skill Map',
  mapTitle: (role) => `${role} Skill Map`,
  subtitle: (companies, postings, _role, date) =>
    `Skill map from ${plural(postings, 'job description', 'job descriptions')} at ${plural(companies, 'company', 'companies')}` +
    (date ? ` (updated ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })})` : ''),
  switcherLabel: (role) => `${role} skill map, switch role`,
  chooseRole: 'Choose a role',
  roleMeta: (skills, postings) => `${plural(skills, 'skill', 'skills')} · ${plural(postings, 'JD', 'JDs')}`,
  langGroup: 'Language',
  loading: 'Loading…',
  loadFailed: (err) => `Failed to load data: ${err}`,
  noRoles: 'No role data yet',
  retry: 'Retry',
  progress: (done, total, doing) => `${done} / ${total} mastered, ${doing} in progress`,
  filterGroup: 'Filter by company',
  allCompanies: 'All',
  hint: 'Drag to pan, scroll to zoom, click a node for details',
  graphLabel: 'Skill map',
  back: 'Back to learning path',
  statusGroup: 'Learning status',
  statusLabels: ['Not started', 'Learning', 'Mastered'],
  concepts: 'Key concepts',
  practice: 'Hands-on practice',
  resources: 'Resources',
  prereqs: 'Prerequisites',
  unlocks: 'Unlocks',
  pathTitle: 'Learning path',
  pathIntro:
    'Bigger nodes are mentioned by more companies. Hollow means not started, translucent means learning, solid means mastered. Dashed lines are prerequisites.',
  topMentioned: 'Most mentioned by companies',
  companyCount: (n) => ` (${plural(n, 'company', 'companies')})`,
  suggestedOrder: 'Suggested order',
  sources: 'JD sources',
  coverage: (n) => ` (covers ${plural(n, 'node', 'nodes')})`,
  listSep: ', ',
}

export const STRINGS: Record<Lang, Strings> = { zh, en }

export const LangContext = createContext<Lang>('zh')
export const useLang = () => useContext(LangContext)
export const useT = () => STRINGS[useContext(LangContext)]
