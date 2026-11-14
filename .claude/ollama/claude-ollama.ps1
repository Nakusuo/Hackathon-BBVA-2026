# Abre Claude Code usando el modelo local de Ollama en vez de la API de Anthropic.
# Las variables se restauran al salir: el `claude` normal de esta terminal sigue igual.
# Uso: .\.claude\ollama\claude-ollama.ps1 [argumentos de claude, p. ej. -p "pregunta"]

$modelo = 'qwen2.5-claude:3b'

ollama show $modelo *> $null
if ($LASTEXITCODE -ne 0) {
    ollama create $modelo -f (Join-Path $PSScriptRoot 'Modelfile')
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

$vars = @{
    ANTHROPIC_BASE_URL                       = 'http://localhost:11434'
    ANTHROPIC_AUTH_TOKEN                     = 'ollama'
    ANTHROPIC_API_KEY                        = $null
    CLAUDE_CODE_MAX_CONTEXT_TOKENS           = '32768'
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
    claude --model $modelo @args
} finally {
    foreach ($k in $antes.Keys) { [Environment]::SetEnvironmentVariable($k, $antes[$k]) }
}
