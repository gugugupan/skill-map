import type { Cluster, Company, Edge, Meta, Roadmap, Skill, SkillMapData, Source } from './types'

const DATA_BASE = `${import.meta.env.BASE_URL}data/`

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(DATA_BASE + path)
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`)
  return (await res.json()) as T
}

export async function loadData(): Promise<SkillMapData> {
  const [meta, clusters, companies, sources, skills, edges, roadmap] = await Promise.all([
    getJson<Meta>('meta.json'),
    getJson<Cluster[]>('clusters.json'),
    getJson<Company[]>('companies.json'),
    getJson<Source[]>('sources.json'),
    getJson<Skill[]>('skills.json'),
    getJson<Edge[]>('edges.json'),
    getJson<Roadmap>('roadmaps/agent-infra.json'),
  ])
  return { meta, clusters, companies, sources, skills, edges, roadmap }
}
