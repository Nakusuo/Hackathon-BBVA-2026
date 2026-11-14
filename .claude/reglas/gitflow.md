# Gitflow y ramas

Gitflow simplificado para 2 días. Lo siguen las personas y todos los agentes.

## Ramas

| Rama | Para qué | Sale de | Entra a |
|---|---|---|---|
| `main` | Lo que se entrega al jurado. Siempre funciona | — | — |
| `develop` | Integración del equipo | `main` | `main` (vía `release/`) |
| `feature/<rol>-<tema>` | Una tarea concreta | `develop` | `develop` |
| `fix/<tema>` | Arreglo durante el desarrollo | `develop` | `develop` |
| `release/entrega` | Congelamiento del domingo a mediodía | `develop` | `main` y `develop` |
| `hotfix/<tema>` | Arreglo urgente sobre lo entregado | `main` | `main` y `develop` |

Roles válidos en el nombre: `datos`, `ml`, `ia`, `backend`, `front`, `docs`.
Ejemplos: `feature/datos-generador`, `feature/ml-pronostico-banda`, `fix/ia-verificador-decimales`.

## Reglas

1. **Nadie trabaja directo en `main` ni en `develop`.** Toda tarea empieza con su rama.
2. Una rama, una tarea. Si dura más de medio día, partirla.
3. Antes de unir a `develop`: `make test` pasa y un **juez** aprueba (ver [flujo-trabajo.md](flujo-trabajo.md)).
4. Unir con Pull Request a `develop`. Borrar la rama al terminar.
5. Actualizar la rama con `develop` antes de pedir el PR (`git pull --rebase origin develop`).
6. Prohibido `git push --force` sobre `main` y `develop`.
7. Etiquetas en cada checkpoint que funcione: `v0.1-flujo`, `v0.2-demo`, `v1.0-entrega`.
8. Los agentes **no hacen push ni abren PR sin permiso** de una persona del equipo.

## Commits

- En español, pequeños y frecuentes. Formato: `tipo(área): qué cambia`.
- Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
- Ejemplos: `feat(forecast): agrega banda por bootstrap`, `test(recommender): cubre regla de crédito con colchón bajo`.
- Sin coautor ni atribución a IA.
- Nunca commitear `.env`, datos grandes generados ni `data/lucas.duckdb` (solo `data/sample/`).

## Comandos de inicio de tarea

```fish
git switch develop
git pull
git switch -c feature/<rol>-<tema>
```

## Al terminar una tarea

```fish
make test
git add <archivos>
git commit -m "feat(area): qué cambia"
git pull --rebase origin develop
# pedir revisión del juez y, con permiso, push + PR a develop
```
