export type DiagramNodeShape = 'rect' | 'diamond' | 'stadium' | 'subroutine' | 'circle'

export interface DiagramNode {
  id: string
  label: string
  shape: DiagramNodeShape
}

export interface DiagramEdge {
  from: string
  to: string
  label?: string | null
}

export interface DiagramData {
  nodes: DiagramNode[]
  edges: DiagramEdge[]
}
