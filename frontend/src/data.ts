import type { Cluster, Company, Edge, Meta, Roadmap, Role, RoleSkill, SiteIndex, Skill, SkillContent, SkillMapData, Source } from './types'

const DATA_BASE = `${import.meta.env.BASE_URL}data/`

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(DATA_BASE + path, { signal })
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`)
  return (await res.json()) as T
}

export async function loadIndex(): Promise<SiteIndex> {
  const [meta, roles, skills] = await Promise.all([
    getJson<Meta>('meta.json'),
    getJson<Role[]>('roles.json'),
    getJson<SkillContent[]>('skills.json'),
  ])
  return { meta, roles, skills }
}

export async function loadRole(index: SiteIndex, role: Role, signal?: AbortSignal): Promise<SkillMapData> {
  const base = `roles/${encodeURIComponent(role.slug)}/`
  const [clusters, companies, sources, roleSkills, edges, roadmap] = await Promise.all([
    getJson<Cluster[]>(base + 'clusters.json', signal),
    getJson<Company[]>(base + 'companies.json', signal),
    getJson<Source[]>(base + 'sources.json', signal),
    getJson<RoleSkill[]>(base + 'skills.json', signal),
    getJson<Edge[]>(base + 'edges.json', signal),
    getJson<Roadmap>(base + 'roadmap.json', signal),
  ])
  const content = new Map(index.skills.map((s) => [s.slug, s]))
  const skills: Skill[] = []
  for (const rs of roleSkills) {
    const c = content.get(rs.slug)
    if (c) skills.push({ ...c, cluster: rs.cluster, companies: rs.companies, heat: rs.heat })
  }
  return { meta: index.meta, role, clusters, companies, sources, skills, edges, roadmap }
}
