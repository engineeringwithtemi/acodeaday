import { Parser, Language, Node as SyntaxNode } from 'web-tree-sitter'

let initialized = false
let pythonParser: Parser | null = null
let jsParser: Parser | null = null

const MAX_LINES = 100
const MAX_DEPTH = 5

// --- Parser initialization ---

export async function initParsers(): Promise<void> {
  if (initialized) return

  await Parser.init({
    locateFile: (scriptName: string) => `/${scriptName}`,
  })

  // Fetch WASM as Uint8Array to bypass web-tree-sitter's broken
  // Node.js detection (globalThis.process?.versions.node throws
  // when Vite defines process without versions)
  const [pyBytes, jsBytes] = await Promise.all([
    fetch('/tree-sitter-python.wasm').then((r) => r.arrayBuffer()).then((b) => new Uint8Array(b)),
    fetch('/tree-sitter-javascript.wasm').then((r) => r.arrayBuffer()).then((b) => new Uint8Array(b)),
  ])

  const pythonLang = await Language.load(pyBytes)
  pythonParser = new Parser()
  pythonParser.setLanguage(pythonLang)

  const jsLang = await Language.load(jsBytes)
  jsParser = new Parser()
  jsParser.setLanguage(jsLang)

  initialized = true
}

function getParser(language: string): Parser | null {
  if (language === 'python') return pythonParser
  if (language === 'javascript') return jsParser
  return null
}

// --- Types ---

interface FlowchartState {
  nodes: string[]
  edges: string[]
  nodeCounter: number
}

interface Exit {
  id: string
  label?: string
}

// --- Label helpers ---

function escapeLabel(text: string): string {
  // Use Unicode fullwidth variants for chars that conflict with Mermaid syntax.
  // Do NOT use HTML entities (&lt; etc) — beautiful-mermaid renders them literally.
  return text
    .replace(/"/g, '\u201C')
    .replace(/</g, '\uFF1C').replace(/>/g, '\uFF1E')   // fullwidth < >
    .replace(/\[/g, '\uFF3B').replace(/\]/g, '\uFF3D') // fullwidth [ ]
    .replace(/\{/g, '\uFF5B').replace(/\}/g, '\uFF5D') // fullwidth { }
    .replace(/\|/g, '\uFF5C')                           // fullwidth |
    .replace(/\(/g, '\uFF08').replace(/\)/g, '\uFF09') // fullwidth ( )
}

function truncate(text: string, maxLen: number): string {
  const cleaned = text.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim()
  return cleaned.length > maxLen ? cleaned.slice(0, maxLen - 3) + '...' : cleaned
}

// --- Node creation ---

function newNode(
  state: FlowchartState,
  label: string,
  shape: 'rect' | 'diamond' | 'stadium' | 'subroutine' | 'circle',
): string {
  const id = `n${state.nodeCounter++}`
  const escaped = escapeLabel(label)

  switch (shape) {
    case 'diamond':
      state.nodes.push(`  ${id}{{${escaped}}}`)
      break
    case 'stadium':
      state.nodes.push(`  ${id}([${escaped}])`)
      break
    case 'subroutine':
      state.nodes.push(`  ${id}[[${escaped}]]`)
      break
    case 'circle':
      state.nodes.push(`  ${id}((${escaped}))`)
      break
    default:
      state.nodes.push(`  ${id}[${escaped}]`)
  }
  return id
}

function addEdge(state: FlowchartState, from: string, to: string, label?: string): void {
  if (label) {
    state.edges.push(`  ${from} -->|${label}| ${to}`)
  } else {
    state.edges.push(`  ${from} --> ${to}`)
  }
}

function connectExits(state: FlowchartState, exits: Exit[], targetId: string): void {
  for (const exit of exits) {
    addEdge(state, exit.id, targetId, exit.label)
  }
}

// --- Error counting ---

function countNodes(node: SyntaxNode): { total: number; errors: number } {
  let total = 1
  let errors = node.type === 'ERROR' ? 1 : 0
  for (let i = 0; i < node.childCount; i++) {
    const child = node.child(i)
    if (child) {
      const counts = countNodes(child)
      total += counts.total
      errors += counts.errors
    }
  }
  return { total, errors }
}

// --- AST classification ---

function isFunctionNode(type: string): boolean {
  return [
    'function_definition', 'function_declaration', 'arrow_function',
    'method_definition', 'async_function_definition', 'async_function_declaration',
  ].includes(type)
}

function isLoopNode(type: string): boolean {
  return ['for_statement', 'for_in_statement', 'while_statement'].includes(type)
}

function isControlFlow(node: SyntaxNode): boolean {
  const t = node.type
  return (
    isFunctionNode(t) ||
    t === 'if_statement' ||
    isLoopNode(t) ||
    t === 'return_statement' ||
    t === 'try_statement'
  )
}

function isTransparent(node: SyntaxNode): boolean {
  const t = node.type
  return (
    t === 'class_definition' || t === 'class_declaration' ||
    t === 'decorated_definition'
  )
}

// --- Child helpers ---

function getNamedChildren(node: SyntaxNode): SyntaxNode[] {
  const children: SyntaxNode[] = []
  for (let i = 0; i < node.namedChildCount; i++) {
    const child = node.namedChild(i)
    if (child) children.push(child)
  }
  return children
}

function expandTransparent(children: SyntaxNode[]): SyntaxNode[] {
  const result: SyntaxNode[] = []
  for (const child of children) {
    if (child.type === 'decorated_definition') {
      for (const inner of getNamedChildren(child)) {
        if (isFunctionNode(inner.type) || isTransparent(inner)) {
          result.push(...expandTransparent([inner]))
        }
      }
    } else if (child.type === 'class_definition' || child.type === 'class_declaration') {
      const body = child.childForFieldName('body')
      if (body) result.push(...expandTransparent(getNamedChildren(body)))
    } else {
      result.push(child)
    }
  }
  return result
}

// --- Statement summary ---
// Renders a group of consecutive non-control-flow statements as summary nodes.
// 1 statement  → single rect
// 2 statements → two rects (first, last)
// 3+ statements → first rect → "..." rect → last rect

function flushStatements(
  buffer: SyntaxNode[],
  state: FlowchartState,
  currentExits: Exit[],
): Exit[] {
  // Filter out comments, ERRORs, pass/empty statements
  const stmts = buffer.filter(c =>
    c.type !== 'comment' && c.type !== 'ERROR' && c.type !== 'pass_statement'
  )
  if (stmts.length === 0) return currentExits

  const first = stmts[0]
  const last = stmts[stmts.length - 1]

  const firstId = newNode(state, truncate(first.text, 35), 'rect')
  connectExits(state, currentExits, firstId)

  if (stmts.length === 1) {
    return [{ id: firstId }]
  }

  if (stmts.length === 2) {
    const lastId = newNode(state, truncate(last.text, 35), 'rect')
    addEdge(state, firstId, lastId)
    return [{ id: lastId }]
  }

  // 3+ statements: first → ... → last
  const dotsId = newNode(state, '...', 'rect')
  addEdge(state, firstId, dotsId)
  const lastId = newNode(state, truncate(last.text, 35), 'rect')
  addEdge(state, dotsId, lastId)
  return [{ id: lastId }]
}

// --- Core walker ---
// Creates diagram nodes for control flow (functions, if/else, loops, returns, try/catch)
// and renders non-control-flow statements as summary rects (first / ... / last).
// Each handler returns Exit[] — the dangling node IDs that need connecting to whatever comes next.

function processBlock(
  children: SyntaxNode[],
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  let currentExits = entries
  let stmtBuffer: SyntaxNode[] = []

  for (const child of children) {
    if (child.type === 'comment' || child.type === 'ERROR') continue

    if (!isControlFlow(child)) {
      stmtBuffer.push(child)
      continue
    }

    // Flush any pending non-CF statements before this CF node
    currentExits = flushStatements(stmtBuffer, state, currentExits)
    stmtBuffer = []

    if (depth > MAX_DEPTH) {
      const id = newNode(state, '...', 'rect')
      connectExits(state, currentExits, id)
      currentExits = [{ id }]
      continue
    }

    currentExits = processControlFlow(child, state, currentExits, endId, depth)
  }

  // Flush any trailing non-CF statements
  currentExits = flushStatements(stmtBuffer, state, currentExits)

  return currentExits
}

function processControlFlow(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  const type = node.type

  if (isFunctionNode(type)) return processFunction(node, state, entries, endId, depth)
  if (type === 'if_statement') return processIf(node, state, entries, endId, depth)
  if (isLoopNode(type)) return processLoop(node, state, entries, endId, depth)
  if (type === 'return_statement') return processReturn(node, state, entries, endId)
  if (type === 'try_statement') return processTry(node, state, entries, endId, depth)

  return entries
}

// --- Function ---

function processFunction(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  const nameNode = node.childForFieldName('name')
  const label = nameNode ? truncate(nameNode.text, 30) : 'function'
  const funcId = newNode(state, label, 'subroutine')
  connectExits(state, entries, funcId)

  const body = node.childForFieldName('body')
  if (body) {
    const bodyChildren = expandTransparent(getNamedChildren(body))
    return processBlock(bodyChildren, state, [{ id: funcId }], endId, depth + 1)
  }
  return [{ id: funcId }]
}

// --- If / elif ---

function processIf(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  const condition = node.childForFieldName('condition')
  const condText = condition ? truncate(condition.text, 35) : '?'
  const condId = newNode(state, condText, 'diamond')
  connectExits(state, entries, condId)

  const allExits: Exit[] = []

  // Yes branch
  const consequence = node.childForFieldName('consequence')
  if (consequence) {
    const yesChildren = expandTransparent(getNamedChildren(consequence))
    const yesExits = processBlock(yesChildren, state, [{ id: condId, label: 'Yes' }], endId, depth + 1)
    allExits.push(...yesExits)
  } else {
    allExits.push({ id: condId, label: 'Yes' })
  }

  // No branch
  const alternative = node.childForFieldName('alternative')
  if (alternative) {
    if (alternative.type === 'elif_clause') {
      const elifExits = processElif(alternative, state, [{ id: condId, label: 'No' }], endId, depth)
      allExits.push(...elifExits)
    } else if (alternative.type === 'else_clause') {
      const elseBody = alternative.childForFieldName('body') || alternative
      const elseChildren = expandTransparent(getNamedChildren(elseBody))
      const elseExits = processBlock(elseChildren, state, [{ id: condId, label: 'No' }], endId, depth + 1)
      allExits.push(...elseExits)
    } else if (alternative.type === 'if_statement') {
      // JS else-if: alternative is another if_statement
      const elseIfExits = processIf(alternative, state, [{ id: condId, label: 'No' }], endId, depth)
      allExits.push(...elseIfExits)
    } else {
      allExits.push({ id: condId, label: 'No' })
    }
  } else {
    allExits.push({ id: condId, label: 'No' })
  }

  return allExits
}

function processElif(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  const condition = node.childForFieldName('condition')
  const condText = condition ? truncate(condition.text, 35) : '?'
  const condId = newNode(state, condText, 'diamond')
  connectExits(state, entries, condId)

  const allExits: Exit[] = []

  const consequence = node.childForFieldName('consequence')
  if (consequence) {
    const yesChildren = expandTransparent(getNamedChildren(consequence))
    const yesExits = processBlock(yesChildren, state, [{ id: condId, label: 'Yes' }], endId, depth + 1)
    allExits.push(...yesExits)
  } else {
    allExits.push({ id: condId, label: 'Yes' })
  }

  const alternative = node.childForFieldName('alternative')
  if (alternative) {
    if (alternative.type === 'elif_clause') {
      const elifExits = processElif(alternative, state, [{ id: condId, label: 'No' }], endId, depth)
      allExits.push(...elifExits)
    } else if (alternative.type === 'else_clause') {
      const elseBody = alternative.childForFieldName('body') || alternative
      const elseChildren = expandTransparent(getNamedChildren(elseBody))
      const elseExits = processBlock(elseChildren, state, [{ id: condId, label: 'No' }], endId, depth + 1)
      allExits.push(...elseExits)
    } else {
      allExits.push({ id: condId, label: 'No' })
    }
  } else {
    allExits.push({ id: condId, label: 'No' })
  }

  return allExits
}

// --- Loop ---

function processLoop(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  _endId: string,
  depth: number,
): Exit[] {
  const type = node.type
  let label: string

  if (type === 'for_statement' || type === 'for_in_statement') {
    const left = node.childForFieldName('left')
    const right = node.childForFieldName('right')
    if (left && right) {
      label = `for ${truncate(left.text, 12)} in ${truncate(right.text, 15)}`
    } else {
      const condition = node.childForFieldName('condition')
      label = condition ? `for ${truncate(condition.text, 25)}` : 'for loop'
    }
  } else {
    const condition = node.childForFieldName('condition')
    label = condition ? `while ${truncate(condition.text, 25)}` : 'while'
  }

  const loopId = newNode(state, label, 'diamond')
  connectExits(state, entries, loopId)

  const body = node.childForFieldName('body')
  if (body) {
    const bodyChildren = expandTransparent(getNamedChildren(body))
    const bodyExits = processBlock(bodyChildren, state, [{ id: loopId }], _endId, depth + 1)

    // Instead of back-edges (which break dagre's top-down layout), connect
    // body exits to a small "repeat" node that visually closes the loop.
    const nonLoopExits = bodyExits.filter(e => e.id !== loopId)
    if (nonLoopExits.length > 0) {
      const repeatId = newNode(state, '↺', 'circle')
      for (const exit of nonLoopExits) {
        addEdge(state, exit.id, repeatId, exit.label)
      }
    }
  }

  return [{ id: loopId, label: 'done' }]
}

// --- Return ---

function processReturn(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
): Exit[] {
  const retExpr = node.namedChildCount > 0 ? node.namedChild(0) : null
  const retText = retExpr ? `return ${truncate(retExpr.text, 25)}` : 'return'
  const retId = newNode(state, retText, 'stadium')
  connectExits(state, entries, retId)
  addEdge(state, retId, endId)
  return [] // Dead end — return terminates the path
}

// --- Try/catch ---

function processTry(
  node: SyntaxNode,
  state: FlowchartState,
  entries: Exit[],
  endId: string,
  depth: number,
): Exit[] {
  const tryId = newNode(state, 'try', 'rect')
  connectExits(state, entries, tryId)

  const allExits: Exit[] = []

  const body = node.childForFieldName('body')
  if (body) {
    const bodyChildren = expandTransparent(getNamedChildren(body))
    const tryExits = processBlock(bodyChildren, state, [{ id: tryId }], endId, depth + 1)
    allExits.push(...tryExits)
  } else {
    allExits.push({ id: tryId })
  }

  for (const child of getNamedChildren(node)) {
    if (child.type === 'except_clause' || child.type === 'catch_clause') {
      const param = child.childForFieldName('parameter') || child.childForFieldName('type')
      const catchLabel = param ? `catch ${truncate(param.text, 20)}` : 'catch'
      const catchId = newNode(state, catchLabel, 'rect')
      addEdge(state, tryId, catchId, 'error')

      const catchBody = child.childForFieldName('body') || child
      const catchChildren = expandTransparent(getNamedChildren(catchBody))
      const catchExits = processBlock(catchChildren, state, [{ id: catchId }], endId, depth + 1)
      allExits.push(...catchExits)
    }
  }

  for (const child of getNamedChildren(node)) {
    if (child.type === 'finally_clause') {
      const finallyId = newNode(state, 'finally', 'rect')
      connectExits(state, allExits, finallyId)

      const finallyBody = child.childForFieldName('body') || child
      const finallyChildren = expandTransparent(getNamedChildren(finallyBody))
      return processBlock(finallyChildren, state, [{ id: finallyId }], endId, depth + 1)
    }
  }

  return allExits
}

// --- Main export ---

export interface CodeToDiagramResult {
  mermaid: string | null
  reason: string | null
}

export function codeToMermaid(code: string, language: string): CodeToDiagramResult {
  if (!code.trim()) {
    return { mermaid: null, reason: null }
  }

  const lineCount = code.split('\n').length
  if (lineCount > MAX_LINES) {
    return { mermaid: null, reason: `Code exceeds ${MAX_LINES} lines — diagram skipped for readability` }
  }

  const parser = getParser(language)
  if (!parser) {
    return { mermaid: null, reason: 'Parser not initialized' }
  }

  const tree = parser.parse(code)
  if (!tree) {
    return { mermaid: null, reason: null }
  }
  const root = tree.rootNode

  if (root.namedChildCount === 0) {
    return { mermaid: null, reason: null }
  }

  // Check error ratio — skip if >50% of AST nodes are errors
  if (root.hasError) {
    const counts = countNodes(root)
    if (counts.total > 0 && counts.errors / counts.total > 0.5) {
      return { mermaid: null, reason: null }
    }
  }

  const state: FlowchartState = { nodes: [], edges: [], nodeCounter: 0 }
  const startId = newNode(state, 'Start', 'stadium')

  // Use a placeholder for End so return edges reference it during processing.
  // The real End node is created after all body nodes, ensuring dagre places it last.
  const endPlaceholder = 'n_end'

  // Expand class/decorator wrappers at top level, then walk control flow
  const topChildren = expandTransparent(getNamedChildren(root))
  const exits = processBlock(topChildren, state, [{ id: startId }], endPlaceholder, 0)

  // If only the Start node was created, nothing to diagram
  if (state.nodeCounter <= 1) {
    return { mermaid: null, reason: 'No control flow detected' }
  }

  // Now create End node — gets the highest counter so dagre places it at the bottom
  const endId = newNode(state, 'End', 'stadium')

  // Replace placeholder references in edges with the real End node ID
  state.edges = state.edges.map(e =>
    e.replaceAll(endPlaceholder, endId)
  )

  // Connect remaining exits to End
  connectExits(state, exits, endId)

  const lines = ['flowchart TD', ...state.nodes, ...state.edges]
  return { mermaid: lines.join('\n'), reason: null }
}
