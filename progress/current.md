<!-- progress/current.md -->
# Trabajo en curso

> **F-003 cerrada, mergeada, desplegada y empujada el 2026-09-05.**
> **F-004 arranca el 2026-09-05** en la rama `feature/F-004-endpoint-concepto-grafico`:
> `pending` → spec-author en marcha → `spec_ready` a la espera de que el humano
> apruebe la spec. Nada implementado todavía. El prompt para retomar, al final.

## Lo que espera al humano, por orden

### 1. Push — HECHO el 2026-09-05

`dev` y `main` en `f8bb8c6` local y remoto (`main` por fast-forward desde
`dev`). La rama de F-003 también está en el remoto. `azure-apps` sigue **sin
remoto configurado**: sus commits no se pueden empujar. `dev` sigue **7 commits por delante de `origin/dev`** sin empujar, y
`azure-apps` tiene 1 commit local (`5967cd8`) igual de local.

### 2. T8 — HECHA el 2026-09-05, tras desplegar

Desplegado `dev` (`e4c071b`) en `func-sigridapi-dev-huyke` con
`func azure functionapp publish`. Verificación en dos mitades, las dos medidas:

- **Nada se rompió.** `diagnose_sigrid_contrato_docs.py B86359866 0695` desde
  `albaranes-persistencia`, antes y después del despliegue: salida
  **byte a byte idéntica** (2.370 bytes). Contrato 2441136, VÍA 1 con 2 filas
  por `JOIN ruesma_rep.dbo.gra`, vías 2-4 con 0 y sin ningún error.
- **El guardia está activo.** Por `sql/read` con `database: ruesma`:
  `FROM msdb.dbo.sysjobs` → **400** «nombra la base `msdb`, que no está
  permitida»; `srv.ruesma.dbo.con` → **400** «cuatro partes o más»;
  `FROM ruesma_rep.dbo.gra` → **200**, 1 fila. Antes de F-003 las dos
  primeras se colaban.

Con esto **no queda ninguna tarea abierta en F-003**: `tasks.md` T1–T16 en
`[x]`.

## Qué se hizo en la sesión del 2026-09-05

| Qué | Resultado |
|---|---|
| Campaña de mutación sobre el código final (`e1ac0dd`) | 138 mutantes, 8 workers, 1.681,8 s |
| Recuento real, tras corregir dos clasificaciones erróneas | **124 muertos, 7 supervivientes, 7 timeouts** |
| Remuestreo EN SERIE de los 138, los 123 muertos incluidos | **0 falsos muertos**, 136/138 veredictos reproducidos |
| Revisión de `CHECKPOINTS.md`, troceada en seis encargos | los seis **APROBADO** |
| Defecto documental (§5 de `impl_F-003.md` con números de otro commit) | corregido en `c15f6b7` |
| `bash harness/init.sh` de cierre | **ENTORNO LISTO** · 1.262 pasan · cobertura 99,2 % · tamaño OK |

Dos cosas que merecen sobrevivir a esta sesión:

- **Trocear la revisión funciona.** En la sesión anterior una revisión se colgó
  por abarcar demasiado. Seis encargos acotados, cada uno con su fichero y su
  pregunta, cerraron `CHECKPOINTS.md` entero sin un solo cuelgue.
- **Los supervivientes se analizan midiendo, nunca leyendo.** Aplicándolos se
  descubrió que dos de los nueve que publicó la campaña no sobreviven: uno
  cuelga la suite y otro muere en 1,9 s.

## Pendiente de decisión del humano

### Del arnés — las tres valen para cualquier proyecto, así que van a `arnes-base`

- **Diagnosticar `harness/mutacion_paralela.py`.** La contención explica los
  timeouts, pero **no** explica que un mutante que muere en 1,9 s saliera con
  exit 0. Sin diagnóstico, la campaña paralela sigue siendo una herramienta que
  sabemos que miente en algún caso. Decidido el 2026-09-05: trabajo aparte,
  después de F-003.
- **Dar reloj al test anti-cuelgue** (`pytest-timeout`): convertiría los 7
  timeouts en muertos limpios y quitaría esa casilla ambigua.
- **Que la sección «Evidencias» declare el SHA de su campaña.** Aplicado a mano
  en `c15f6b7`; como regla, RM1 habría cazado sola el defecto que bloqueó el
  cierre. Siguen sin aplicar, de sesiones anteriores: `init.sh` no avisa de que
  falte `mutacion_F-XXX.md` en rigor `critico`, y RM5 pide reproducir **un**
  equivalente cuando reproducirlos todos destapó cuatro análisis falsos.
- **`harness/rutas_sensibles.json` no existe** en este repositorio, así que C4
  ter es siempre N/A — y eso en un repo con `infrastructure/security/`, que es
  justo la clase de ruta que ese mecanismo existe para vigilar.

### De configuración y de la base

- **`local.settings.json` está versionado con dos contraseñas reales**
  (`SQL_SERVER_PASSWORD` y `SQL_SERVER_WRITE_PASSWORD`, usuarios `ro_user` y
  `rw_user` del túnel local a Sigrid). Desde el primer commit (`e903394`,
  2026-04-16), en `origin/main` y `origin/dev`: cinco meses en GitHub. No está
  en `.gitignore`. Incumple la regla transversal «nunca secretos en un
  repositorio». Lo que cierra el hueco es **rotar las dos contraseñas** en
  Sigrid y en el Key Vault (decisión del humano, 2026-09-05: se deja anotado y
  se sigue con F-004); después, `git rm --cached local.settings.json` y
  añadirlo a `.gitignore`, dejando solo el `sample`.
- **`ALLOWED_DATABASES` incluye `master`** en la Function App, y ningún
  consumidor lo necesita. Quitarlo es una línea de configuración.
- **`user_rw` tiene `UPDATE`** sobre `ruesma_rep.dbo.gra`, donde vive la única
  copia de los 359.438 documentos, en una base con recuperación `SIMPLE`. No se
  probó si tiene `DELETE`. Merece una conversación con quien administre el
  motor.
- **`scripts/verificar_sql_ecosistema.py` copia a mano** `ALLOWED_DATABASES` y
  `ALLOWED_WRITE_DATABASES` en vez de leerlas de `config/settings.py`. Es
  deliberado —compara contra lo desplegado, no contra el `.env` local— y está
  documentado en el fichero, pero es una lista que se desincroniza sola.

## Lo siguiente en el backlog

**F-004** (endpoint `sigrid/concepto-grafico`), rigor `critico`, **en marcha**:
el spec-author redacta `specs/F-004-endpoint-concepto-grafico/` a partir de
`docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md` y de lo medido en
`progress/explore_ruesma_rep.md`. Entre sus criterios está corregir
`dedicacion.md`, `partes.md` y `remesas.md` de `azure-apps`, que siguen
llamando «réplica que no admite escritura» a `ruesma_rep`.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-004 está en `spec_ready` (o el
> spec-author quedó a medias: mira `specs/F-004-endpoint-concepto-grafico/`).
> Si el humano aprueba la spec, PARADA 1 con la propuesta de implementación y
> luego implementer. No arranques nada más hasta cerrar F-004.
