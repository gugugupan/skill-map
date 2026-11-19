import type { Lang } from './i18n'

export interface Meta {
  generated_at: string
}

export interface Role {
  slug: string
  name: string
  root_label: string
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

export interface SkillContent {
  slug: string
  name: string
  description: string
  concepts: string[]
  practice: string
  resources: Resource[]
  prereqs: string[]
  unlocks: string[]
}

export interface RoleSkill {
  slug: string
  cluster: string
  companies: string[]
  heat: number
}

export type Skill = SkillContent & Omit<RoleSkill, 'slug'>

export interface Edge {
  from: string
  to: string
  type: string
}

export interface Roadmap {
  phases: { title: string; skills: string[] }[]
}

export interface SiteIndex {
  lang: Lang
  meta: Meta
  roles: Role[]
  skills: SkillContent[]
}

export interface SkillMapData {
  meta: Meta
  role: Role
  clusters: Cluster[]
  companies: Company[]
  sources: Source[]
  skills: Skill[]
  edges: Edge[]
  roadmap: Roadmap
}
