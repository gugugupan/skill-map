import type { Lang } from './i18n'
import type { Cluster, Company, Edge, Meta, Roadmap, Role, RoleSkill, SiteIndex, Skill, SkillContent, SkillMapData, Source } from './types'

// English data mirrors the zh layout under data/en/.
const dataBase = (lang: Lang) => `${import.meta.env.BASE_URL}data/${lang === 'zh' ? '' : 'en/'}`

async function getJson<T>(lang: Lang, path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(dataBase(lang) + path, { signal })
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`)
  return (await res.json()) as T
}

export async function loadIndex(lang: Lang, signal?: AbortSignal): Promise<SiteIndex> {
  const [meta, roles, skills] = await Promise.all([
    getJson<Meta>(lang, 'meta.json', signal),
    getJson<Role[]>(lang, 'roles.json', signal),
    getJson<SkillContent[]>(lang, 'skills.json', signal),
  ])
  return { lang, meta, roles, skills }
}

export async function loadRole(index: SiteIndex, role: Role, signal?: AbortSignal): Promise<SkillMapData> {
  const base = `roles/${encodeURIComponent(role.slug)}/`
  const [clusters, companies, sources, roleSkills, edges, roadmap] = await Promise.all([
    getJson<Cluster[]>(index.lang, base + 'clusters.json', signal),
    getJson<Company[]>(index.lang, base + 'companies.json', signal),
    getJson<Source[]>(index.lang, base + 'sources.json', signal),
    getJson<RoleSkill[]>(index.lang, base + 'skills.json', signal),
    getJson<Edge[]>(index.lang, base + 'edges.json', signal),
    getJson<Roadmap>(index.lang, base + 'roadmap.json', signal),
  ])
  const content = new Map(index.skills.map((s) => [s.slug, s]))
  const skills: Skill[] = []
  for (const rs of roleSkills) {
    const c = content.get(rs.slug)
    if (c) skills.push({ ...c, cluster: rs.cluster, companies: rs.companies, heat: rs.heat })
  }
  return { meta: index.meta, role, clusters, companies, sources, skills, edges, roadmap }
}
