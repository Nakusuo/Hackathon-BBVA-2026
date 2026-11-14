# Abre Claude Code usando el modelo local de Ollama en vez de la API de Anthropic.
# Las variables se restauran al salir: el `claude` normal de esta terminal sigue igual.
# Uso (desde la raíz del repo): .\.claude\ollama\claude-ollama.ps1 [argumentos de claude]

$modelo = 'qwen2.5-claude:3b'

ollama show $modelo *> $null
if ($LASTEXITCODE -ne 0) {
    ollama create $modelo -f (Join-Path $PSScriptRoot 'Modelfile')
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# --bare deja el prompt de sistema en ~2.5k tokens; el modo normal ocupa ~19k de los 32k
# y la sesión cae en «Context limit reached» al segundo mensaje. --bare solo acepta
# ANTHROPIC_API_KEY como credencial; Ollama ignora su valor.
# Sin MAX_OUTPUT_TOKENS, Claude Code reserva para la respuesta más de lo que cabe en 32k.
$vars = @{
    ANTHROPIC_BASE_URL                       = 'http://localhost:11434'
    ANTHROPIC_API_KEY                        = 'ollama'
    ANTHROPIC_AUTH_TOKEN                     = $null
    CLAUDE_CODE_MAX_CONTEXT_TOKENS           = '32768'
    CLAUDE_CODE_MAX_OUTPUT_TOKENS            = '4096'
    ANTHROPIC_DEFAULT_HAIKU_MODEL            = $modelo
    CLAUDE_CODE_SUBAGENT_MODEL               = $modelo
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'
}
$antes = @{}
foreach ($k in $vars.Keys) {
    $antes[$k] = [Environment]::GetEnvironmentVariable($k)
    [Environment]::SetEnvironmentVariable($k, $vars[$k])
}
try {
    claude --model $modelo --bare --tools 'Bash,Read,Edit,Write,Glob,Grep' `
        --append-system-prompt-file (Join-Path $PSScriptRoot '..\CLAUDE.md') @args
} finally {
    foreach ($k in $antes.Keys) { [Environment]::SetEnvironmentVariable($k, $antes[$k]) }
}
