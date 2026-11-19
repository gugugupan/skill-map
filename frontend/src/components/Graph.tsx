import * as d3 from 'd3'
import { useEffect, useRef } from 'react'
import type { Progress } from '../progress'
import type { SkillMapData } from '../types'

type NodeType = 'root' | 'hub' | 'leaf'

interface GNode extends d3.SimulationNodeDatum {
  id: string
  type: NodeType
  cluster: string
  label: string
  heat: number
  companies: string[]
}

interface GLink extends d3.SimulationLinkDatum<GNode> {
  kind: 'tree' | 'pre'
}

interface Built {
  nodeSel: d3.Selection<SVGGElement, GNode, SVGGElement, unknown>
  linkSel: d3.Selection<SVGLineElement, GLink, SVGGElement, unknown>
  color: (d: GNode) => string
}

const HUB_PREFIX = 'h_'
const HUB_RADIUS = 13
// The hottest skill in a role stays just under a hub so hubs remain the visual anchors.
const LEAF_MIN = 5
const LEAF_SPAN = 7.5
const endpoint = (end: GLink['source']) => end as GNode

interface Props {
  data: SkillMapData
  filter: string | null
  selected: string | null
  progress: Progress
  onSelect: (slug: string | null) => void
}

export function Graph({ data, filter, selected, progress, onSelect }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const builtRef = useRef<Built | null>(null)
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  useEffect(() => {
    const svgEl = svgRef.current
    const container = svgEl?.parentElement
    if (!svgEl || !container) return

    const clusterIndex = new Map(data.clusters.map((c, i) => [c.slug, i]))
    const clusterColor = new Map(data.clusters.map((c) => [c.slug, c.color]))
    const skills = data.skills.filter((s) => clusterIndex.has(s.cluster))
    const skillIds = new Set(skills.map((s) => s.slug))
    const maxHeat = Math.max(1, ...skills.map((s) => s.heat))
    const radius = (d: GNode) =>
      d.type === 'root' ? 22 : d.type === 'hub' ? HUB_RADIUS : LEAF_MIN + (LEAF_SPAN * Math.max(0, d.heat)) / maxHeat

    const nodes: GNode[] = [{ id: 'root', type: 'root', cluster: '', label: data.role.root_label, heat: 0, companies: [] }]
    const links: GLink[] = []
    for (const c of data.clusters) {
      nodes.push({ id: HUB_PREFIX + c.slug, type: 'hub', cluster: c.slug, label: c.name, heat: 0, companies: [] })
      links.push({ source: 'root', target: HUB_PREFIX + c.slug, kind: 'tree' })
    }
    for (const s of skills) {
      nodes.push({ id: s.slug, type: 'leaf', cluster: s.cluster, label: s.name, heat: s.heat, companies: s.companies })
      links.push({ source: HUB_PREFIX + s.cluster, target: s.slug, kind: 'tree' })
    }
    for (const e of data.edges) {
      if (e.type === 'prereq' && skillIds.has(e.from) && skillIds.has(e.to)) {
        links.push({ source: e.from, target: e.to, kind: 'pre' })
      }
    }

    const anchor = (cluster: string): [number, number] => {
      const a = ((clusterIndex.get(cluster) ?? 0) / data.clusters.length) * 2 * Math.PI - Math.PI / 2
      return [Math.cos(a) * 380, Math.sin(a) * 300]
    }
    const color = (d: GNode) => (d.type === 'root' ? 'var(--ink)' : (clusterColor.get(d.cluster) ?? 'var(--muted)'))

    const svg = d3.select(svgEl)
    svg.selectAll('*').remove()
    const g = svg.append('g')
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (e: d3.D3ZoomEvent<SVGSVGElement, unknown>) => g.attr('transform', e.transform.toString()))
    svg.call(zoom)

    const linkSel = g
      .append('g')
      .selectAll<SVGLineElement, GLink>('line')
      .data(links)
      .join('line')
      .attr('class', (d) => 'link' + (d.kind === 'pre' ? ' pre' : ''))

    const sim = d3.forceSimulation<GNode>(nodes)

    const nodeSel = g
      .append('g')
      .selectAll<SVGGElement, GNode>('g')
      .data(nodes)
      .join('g')
      .attr('class', (d) => 'node ' + d.type)
      .attr('tabindex', (d) => (d.type === 'leaf' ? 0 : null))
      .attr('role', (d) => (d.type === 'leaf' ? 'button' : null))
      .attr('aria-label', (d) => d.label)
      .on('click', (_e, d) => {
        if (d.type === 'leaf') onSelectRef.current(d.id)
        else if (d.type === 'root') onSelectRef.current(null)
      })
      .on('keydown', (e: KeyboardEvent, d) => {
        if ((e.key === 'Enter' || e.key === ' ') && d.type === 'leaf') {
          e.preventDefault()
          onSelectRef.current(d.id)
        }
      })
      .call(
        d3
          .drag<SVGGElement, GNode>()
          .on('start', (e, d) => {
            if (!e.active) sim.alphaTarget(0.2).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (e, d) => {
            d.fx = e.x
            d.fy = e.y
          })
          .on('end', (e, d) => {
            if (!e.active) sim.alphaTarget(0)
            d.fx = null
            d.fy = null
          }),
      )

    nodeSel.append('circle').attr('class', 'ring').attr('r', (d) => radius(d) + 3.5).attr('fill', 'none').attr('stroke-width', 2)
    nodeSel.append('circle').attr('class', 'dot').attr('r', radius).attr('stroke', 'var(--bg)').attr('stroke-width', 1.5)
    nodeSel
      .append('text')
      .attr('dy', (d) => radius(d) + 14)
      .attr('text-anchor', 'middle')
      .text((d) => d.label)

    sim
      .force(
        'link',
        d3
          .forceLink<GNode, GLink>(links)
          .id((d) => d.id)
          .distance((l) => (l.kind === 'pre' ? 120 : endpoint(l.source).id === 'root' ? 200 : 60))
          .strength((l) => (l.kind === 'pre' ? 0.05 : 0.6)),
      )
      .force('charge', d3.forceManyBody<GNode>().strength((d) => (d.type === 'root' ? -600 : d.type === 'hub' ? -300 : -140)))
      .force('x', d3.forceX<GNode>((d) => (d.type === 'root' ? 0 : anchor(d.cluster)[0])).strength((d) => (d.type === 'root' ? 0.5 : 0.12)))
      .force('y', d3.forceY<GNode>((d) => (d.type === 'root' ? 0 : anchor(d.cluster)[1])).strength((d) => (d.type === 'root' ? 0.5 : 0.12)))
      .force('collide', d3.forceCollide<GNode>((d) => radius(d) + 20))
      .on('tick', () => {
        linkSel
          .attr('x1', (d) => endpoint(d.source).x ?? 0)
          .attr('y1', (d) => endpoint(d.source).y ?? 0)
          .attr('x2', (d) => endpoint(d.target).x ?? 0)
          .attr('y2', (d) => endpoint(d.target).y ?? 0)
        nodeSel.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
      })

    const fit = () => {
      const w = container.clientWidth
      const h = container.clientHeight
      const s = Math.min(w / 1000, h / 860, 1.1)
      svg.call(zoom.transform, d3.zoomIdentity.translate(w / 2, h / 2).scale(s))
    }
    fit()
    const ro = new ResizeObserver(fit)
    ro.observe(container)

    builtRef.current = { nodeSel, linkSel, color }
    return () => {
      ro.disconnect()
      sim.stop()
      svg.on('.zoom', null)
      svg.selectAll('*').remove()
      builtRef.current = null
    }
  }, [data])

  useEffect(() => {
    const built = builtRef.current
    if (!built) return
    const { nodeSel, color } = built
    const status = (d: GNode) => progress[d.id] ?? 0
    nodeSel
      .select<SVGCircleElement>('.dot')
      .attr('fill', (d) => (d.type !== 'leaf' || status(d) !== 0 ? color(d) : 'var(--surface)'))
      .attr('stroke', (d) => (d.type === 'leaf' ? color(d) : 'var(--bg)'))
      .attr('stroke-width', (d) => (d.type === 'leaf' ? 2 : 1.5))
      .attr('fill-opacity', (d) => (d.type === 'leaf' && status(d) === 1 ? 0.45 : 1))
    nodeSel.select<SVGCircleElement>('.ring').attr('stroke', (d) => (d.id === selected ? 'var(--ink)' : 'transparent'))
  }, [data, progress, selected])

  useEffect(() => {
    const built = builtRef.current
    if (!built) return
    const { nodeSel, linkSel } = built
    const hidden = (d: GNode) => filter !== null && d.type === 'leaf' && !d.companies.includes(filter)
    nodeSel.classed('dim', hidden)
    linkSel
      .classed('hl', (l) => selected !== null && l.kind === 'pre' && (endpoint(l.source).id === selected || endpoint(l.target).id === selected))
      .classed('dim', (l) => hidden(endpoint(l.source)) || hidden(endpoint(l.target)))
  }, [data, filter, selected])

  return <svg ref={svgRef} aria-label="知识图谱" />
}
