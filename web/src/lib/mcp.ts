import { MOCK, workspace } from './api'

export const MCP_URL = window.location.origin + '/mcp'

interface Content {
  type: string
  text?: string
}

const texts = (content: unknown) => (Array.isArray(content) ? (content as Content[]) : [])

// ponytail: one short-lived client per call; the server is stateless JSON mode, so nothing to keep.
export async function callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  if (MOCK) return (await import('./mock')).mockTool(name, args)
  // loaded on first call: the SDK is large and only the playground needs it
  const [{ Client }, { StreamableHTTPClientTransport }] = await Promise.all([
    import('@modelcontextprotocol/sdk/client/index.js'),
    import('@modelcontextprotocol/sdk/client/streamableHttp.js'),
  ])
  const client = new Client({ name: 'playground', version: '1.0.0' })
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL), {
    requestInit: { headers: { 'X-Canon-Workspace': workspace() } },
  })
  await client.connect(transport)
  try {
    const res = await client.callTool({ name, arguments: args })
    if (res.isError) {
      const text = texts(res.content)
        .map(c => c.text ?? '')
        .join('\n')
      throw new Error(text || 'The tool returned an error.')
    }
    const structured = res.structuredContent as Record<string, unknown> | undefined
    if (structured) return 'result' in structured && Object.keys(structured).length === 1 ? structured.result : structured
    const text = texts(res.content).find(c => c.type === 'text')?.text ?? ''
    try {
      return JSON.parse(text) as unknown
    } catch {
      return text
    }
  } finally {
    await client.close()
  }
}
