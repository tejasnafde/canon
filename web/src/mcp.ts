import { MOCK, workspace } from './api'

export const MCP_URL = window.location.origin + '/mcp'

// ponytail: one short-lived client per call; the server is stateless JSON mode, so nothing to keep.
export async function callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  if (MOCK) return (await import('./mock')).mockTool(name, args)
  // loaded on first call: the SDK is most of the bundle and only this page needs it
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
      const text = (res.content as { type: string; text?: string }[]).map(c => c.text ?? '').join('\n')
      throw new Error(text || 'Tool returned an error')
    }
    const structured = res.structuredContent as Record<string, unknown> | undefined
    if (structured) return 'result' in structured && Object.keys(structured).length === 1 ? structured.result : structured
    const text = (res.content as { type: string; text?: string }[]).find(c => c.type === 'text')?.text ?? ''
    try { return JSON.parse(text) } catch { return text }
  } finally {
    await client.close()
  }
}
