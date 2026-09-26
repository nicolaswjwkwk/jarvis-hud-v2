// Plugin OpenCode — JARVIS Guard
// Bloqueia leitura de .env e impede que segredos entrem no contexto do modelo.
export const JarvisGuard = async ({ project, client, $, directory, worktree }) => {
  await client.app.log({
    body: { service: "jarvis-guard", level: "info", message: "JARVIS Guard ativo" },
  })
  return {
    "tool.execute.before": async (input, output) => {
      const blocked = [".env", ".env.", "secrets.json", "id_rsa", "credentials.json"]
      const target = String(
        (output && output.args && (output.args.filePath || output.args.path)) || ""
      )
      if (input.tool === "read" && blocked.some((b) => target.includes(b))) {
        throw new Error("JARVIS Guard: arquivo sensível bloqueado. Use variáveis de ambiente.")
      }
    },
  }
}
