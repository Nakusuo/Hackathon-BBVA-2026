# Se corre desde la raíz. PY usa el entorno .venv si existe.
PY ?= $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,$(if $(wildcard .venv/bin/python),.venv/bin/python,python))

.PHONY: data test eval run check

data:
	$(PY) data/generator.py --perfil muestra

test:
	$(PY) -m pytest -q
	cd frontend && npm test

eval:
	$(PY) analitica/eval/entrenar_modelos.py

# La API queda en segundo plano y se apaga al cerrar el front con Ctrl+C.
run:
	@$(PY) -m uvicorn --app-dir backend src.api.main:app --port 8000 & api=$$!; trap "kill $$api" EXIT INT; cd frontend && npm run dev

check:
	$(PY) -m ruff check backend/src analitica/eval
	@if $(PY) -m pip_audit --version >/dev/null 2>&1; then $(PY) -m pip_audit -r backend/requirements.txt; else echo "pip-audit no está instalado: pip install pip-audit"; fi
