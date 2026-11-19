export interface Meta {
  generated_at: string
  counts: { companies: number; postings: number; skills: number; edges: number }
}

export interface Cluster {
  slug: string
  name: string
  color: string
}

export interface Company {
  code: string
  name: string
}

export interface Source {
  code: string
  name: string
  jobs: { title: string; url: string | null }[]
}

export interface Resource {
  title: string
  url: string | null
  type: string
}

export interface Skill {
  slug: string
  name: string
  cluster: string
  description: string
  concepts: string[]
  practice: string
  resources: Resource[]
  companies: string[]
  heat: number
  prereqs: string[]
  unlocks: string[]
}

export interface Edge {
  from: string
  to: string
  type: string
}

export interface Roadmap {
  phases: { title: string; skills: string[] }[]
}

export interface SkillMapData {
  meta: Meta
  clusters: Cluster[]
  companies: Company[]
  sources: Source[]
  skills: Skill[]
  edges: Edge[]
  roadmap: Roadmap
}
