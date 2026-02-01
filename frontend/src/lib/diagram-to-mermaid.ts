import type { DiagramData } from '@/types/diagram'

function escapeLabel(text: string): string {
  return text
    .replace(/"/g, '\u201C')
    .replace(/</g, '\uFF1C').replace(/>/g, '\uFF1E')
    .replace(/\[/g, '\uFF3B').replace(/\]/g, '\uFF3D')
    .replace(/\{/g, '\uFF5B').replace(/\}/g, '\uFF5D')
    .replace(/\|/g, '\uFF5C')
    .replace(/\(/g, '\uFF08').replace(/\)/g, '\uFF09')
}

function nodeToMermaid(id: string, label: string, shape: string): string {
  const escaped = escapeLabel(label)
  switch (shape) {
    case 'diamond':
      return `  ${id}{{${escaped}}}`
    case 'stadium':
      return `  ${id}([${escaped}])`
    case 'subroutine':
      return `  ${id}[[${escaped}]]`
    case 'circle':
      return `  ${id}((${escaped}))`
    case 'rect':
    default:
      return `  ${id}[${escaped}]`
  }
}

function edgeToMermaid(from: string, to: string, label?: string | null): string {
  if (label) {
    return `  ${from} -->|${escapeLabel(label)}| ${to}`
  }
  return `  ${from} --> ${to}`
}

export function diagramDataToMermaid(data: DiagramData): string {
  const nodeLines = data.nodes.map((n) => nodeToMermaid(n.id, n.label, n.shape))
  const edgeLines = data.edges.map((e) => edgeToMermaid(e.from, e.to, e.label))
  return ['flowchart TD', ...nodeLines, ...edgeLines].join('\n')
}
