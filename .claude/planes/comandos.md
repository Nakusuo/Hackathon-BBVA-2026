# Comandos del equipo

Copiar y pegar. Funcionan en Linux, macOS y en Windows con **Git Bash** o **WSL**.
Requisitos: Git, Python 3.12 o más, Docker, Make, GitHub CLI (`gh`) y Ollama.

## 1. Solo la primera vez

```bash
git clone https://github.com/MaickolO/Hackathon-BBVA-2026-Equipo-2.git
cd Hackathon-BBVA-2026-Equipo-2
git switch develop
gh auth login                      # para abrir PR desde la terminal
python -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
pip install -r backend/requirements.txt    # analítica, agente y API
cp .env.example .env               # y completar valores locales
```

Si ya lo tenías clonado:

```bash
git fetch origin
git switch develop
git pull
```

## 2. Actualizarte (cada hora y cada vez que alguien avise [MERGE])

```bash
git switch develop
git pull
```

Si estás a mitad de una tarea, trae lo nuevo a tu rama:

```bash
git add -A && git commit -m "wip(area): avance"     # o guarda lo tuyo primero
git pull --rebase origin develop
```

## 3. Empezar una tarea

```bash
git switch develop
git pull
git switch -c feature/<rol>-<tema>      # ej: feature/ml-pronostico
```

Roles: `datos`, `ml`, `ia`, `backend`, `front`, `arq`, `docs`.

## 4. Guardar avance (seguido, cada 30 a 60 min)

```bash
git status                              # mira qué cambió
git add <archivos>                      # evita "git add ." si hay archivos raros
git commit -m "feat(forecast): agrega banda bootstrap"
git push -u origin HEAD                 # sube tu rama (la primera vez con -u)
```

Tipos de commit: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`. En español, sin coautor.

## 5. Terminar la tarea y pedir revisión

```bash
make check                              # ruff y pip-audit; luego make test
git pull --rebase origin develop
git push
gh pr create --base develop --fill      # abre el PR
```

Luego manda el aviso `[LISTO]` al grupo (formato en [tareas.md](tareas.md)).

## 6. Revisar el PR de tu compañero

```bash
gh pr list                              # ver PR abiertos
gh pr checkout <número>                 # bajar su rama
make check
(cd frontend && PW_PUERTO=5200 npm run e2e)   # si el cambio se ve en la demo
gh pr review <número> --approve         # o: --request-changes -b "qué falta"
git switch develop                      # volver a lo tuyo
```

## 7. Unir tu PR aprobado

```bash
gh pr merge <número> --squash --delete-branch
git switch develop
git pull
```

Aviso al grupo: `[MERGE] DI-06 en develop`.

## 8. Si hay un conflicto

```bash
git pull --rebase origin develop        # aparece el conflicto
git status                              # muestra los archivos en conflicto
# abrir cada archivo, elegir qué queda entre <<<<<<< y >>>>>>>, guardar
git add <archivo>
git rebase --continue
```

¿Te perdiste? `git rebase --abort` vuelve todo como estaba. Pide ayuda en el grupo antes de borrar nada.

## 9. Proyecto

```bash
make data        # genera los datos sintéticos de muestra (data/generator.py --perfil muestra)
make test        # pytest -q y npm test en frontend
make eval        # entrena y evalúa los modelos (analitica/eval/entrenar_modelos.py)
make run         # API en el puerto 8000 y front con npm run dev
make check       # ruff sobre backend/src y analitica/eval, y pip-audit si está instalado
```

`PY` es el Python del Makefile: `.venv/Scripts/python.exe` si existe y, si no, `python`. Se cambia con `make test PY=python3`. No existen `make db`, `make psql` ni `make e2e`: la base se levanta con `docker compose` y el e2e con `PW_PUERTO=5200 npm run e2e` dentro de `frontend/`.

Para levantar la demo completa con la base de datos y el RAG, a mano (cada bloque en su terminal, desde la raíz):

```bash
# Una sola vez: base de datos con los datos sintéticos y el RAG (unos 3 minutos)
docker compose up -d
source .venv/Scripts/activate && set -a && . ./.env && set +a
python analitica/eval/cargar_a_postgres.py --crear --rag

# Terminal 1: API con el agente (carga modelos y datos de Postgres al arrancar)
python -m uvicorn --app-dir backend src.api.main:app --port 8000

# Terminal 2: front; con VITE_CHAT_AGENTE=si en frontend/.env el chat pregunta al agente
cd frontend && npm run dev
```

Ollama debe estar abierto con `qwen2.5:3b` y `nomic-embed-text`. La app queda en `http://127.0.0.1:5173`.

Docker:

```bash
docker compose up -d        # levantar
docker compose ps           # ver qué corre
docker compose logs -f db   # ver errores de Postgres
docker compose down         # apagar
docker compose down -v      # apagar y BORRAR datos (luego: make data)
```

Ollama:

```bash
ollama list                 # modelos descargados
ollama pull <modelo>        # bajar el modelo acordado (ver PROMPTS.md)
```

Claude Code con el modelo local (sin red ni cuota de Anthropic):

```powershell
.\.claude\ollama\claude-ollama.ps1                 # sesión interactiva
.\.claude\ollama\claude-ollama.ps1 -p "pregunta"   # una sola respuesta
```

La primera vez crea `qwen2.5-claude:3b` (el mismo `qwen2.5:3b` con 32k de contexto, su máximo). Abre Claude Code en modo `--bare`: sin plugins, hooks, MCP ni agentes, pero con este CLAUDE.md y las herramientas de archivos y Bash. En modo normal el prompt ocupa ~19k tokens y la sesión cae en «Context limit reached» enseguida.

- Abrirlo desde la raíz del repo: los archivos solo se tocan dentro de esa carpeta.
- Si aparece «Context limit reached», escribir `/clear` (compactar no funciona con este modelo).
- En la RTX 3050 queda ~80 % en GPU y tarda de 10 a 50 s por respuesta.
- Un modelo de 3B sirve para pedidos de un paso (leer, buscar, crear un archivo) y a veces se equivoca o inventa: revisar lo que diga. Para trabajo real, el `claude` normal.
- Antes de la demo, `ollama stop qwen2.5-claude:3b` para dejar la GPU libre a Lucas.

## 10. Pedir ayuda a los agentes de Claude Code

Dentro del repo, en Claude Code:

- «Usa el investigador para comparar ETS y regresión para el pronóstico.»
- «Usa el agente ml-analitica para hacer DI-06 en la rama feature/ml-pronostico.»
- «Pasa mi rama por el juez-tecnico.»
- «Pasa develop por el juez-producto como si fuera el jurado.»

Anota cada veredicto en [verificaciones.md](verificaciones.md).

## Nunca

- `git push --force` en `main` o `develop`.
- Commitear `.env`, `data/*.parquet` grandes o volcados de la base.
- Trabajar directo en `main` o `develop`.
