<!-- progress/current.md -->
# Trabajo en curso

> **F-004 implementada el 2026-09-05** en `feature/F-004-endpoint-concepto-grafico`
> (`87098d6`), con la spec y la propuesta aprobadas por el humano ese mismo día.
> Informe: [`impl_F-004.md`](impl_F-004.md). `bash harness/init.sh` en **ENTORNO
> LISTO**: 1.437 tests, cobertura de líneas cambiadas **100 %** (455/455), ruff
> en los 79 avisos previos. **Nada se ha escrito en el ERP**: ni una llamada.
> **F-003 cerrada, mergeada, desplegada y empujada el 2026-09-05.**

## F-004 · lo que queda

1. **T15, campaña de mutación** (rigor `critico`, sin tope): la lanza el líder
   con `python -m harness.mutacion --feature F-004` → `progress/mutacion_F-004.md`.
   Es la única evidencia del nivel que el informe no puede cerrar.
2. **Revisión** contra `CHECKPOINTS.md` (troceada, como en F-003).
3. **T18-T22, manuales del humano**: desplegar y fijar las App Settings nuevas
   **cerradas**, dry-run contra producción (incluida la reclamación con el
   gráfico huérfano), primer `commit:true` autorizado por Posventa y su
   repetición idempotente. Hasta T20 nadie ha escrito nunca en `ruesma_rep`.
4. **Commit pendiente de push en `azure-apps`**: `a40684f` (ese repositorio
   sigue sin remoto). En este repositorio, la rama de F-004 tampoco se ha
   empujado: son todo commits locales.

Dos cosas que el reviewer debe mirar con lupa, dichas de frente:

- **La hora de Madrid se calcula a mano** (`hora_local_de_madrid`), sin
  `zoneinfo`: `tzdata` no está en `requirements.txt` y Windows no trae zonas
  horarias, así que `ZoneInfo("Europe/Madrid")` **revienta** en esta máquina y
  la spec no autoriza dependencias nuevas. Regla europea fija desde 1996, con
  siete casos de test.
- **Que `pyodbc` convierta `bytes` → `image` en E4 no está comprobado** y no se
  puede comprobar sin escribir. Si fallara, sería un `ROLLBACK` con nada
  escrito; el arreglo sería `CAST(? AS image)`. Lo despeja T20.

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

**Decisiones del humano el 2026-09-05 sobre F-004:**

- **Aprobado el cambio de regla de gobierno**: «`ruesma_rep` no se escribe»
  pasa a «se escribe **solo** por `sigrid/concepto-grafico`, nunca por
  `sql/write`», en `CLAUDE.md`, `CHECKPOINTS.md` (C3) y `docs/ARCHITECTURE.md`
  (R24, T16 de la spec).
- **Q4, Q5, Q7 y T1 resueltos con lecturas** por `sql/read`, informe en
  [`explore_F-004_mediciones.md`](explore_F-004_mediciones.md): Sigrid no
  interpreta el formato de `cod` (tolera 31.941 nombres de fichero), no usa
  `guid` (0 de 643.668 filas) y no escribe `dbo.log` al importar gráficos
  (0 filas `tab='gra'` en 8,4 M): no hay cuarta escritura. **Lo que cambia el
  diseño**: la fila documental lleva siempre `gratipide=0` y `res=''`, y `rcg`
  tiene `feclee` y `fecalt`, ausentes del diccionario. Hay **1 gráfico de clase
  35 sin pareja documental**, por identificar antes de T19.

**F-004** (endpoint `sigrid/concepto-grafico`), rigor `critico`, **en marcha**:
el spec-author redacta `specs/F-004-endpoint-concepto-grafico/` a partir de
`docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md` y de lo medido en
`progress/explore_ruesma_rep.md`. Entre sus criterios está corregir
`dedicacion.md`, `partes.md` y `remesas.md` de `azure-apps`, que siguen
llamando «réplica que no admite escritura» a `ruesma_rep`.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-004 está **implementada** en su
> rama (`87098d6`) con `init.sh` en verde y el informe en
> `progress/impl_F-004.md`; `tasks.md` tiene T3-T14, T16 y T17 en `[x]`. Lo que
> falta: lanzar **T15** (mutación, rigor `critico`, sin tope), revisar contra
> `CHECKPOINTS.md` troceando la revisión, y entonces la PARADA 2 con el humano
> para las tareas manuales T18-T22. No arranques nada más hasta cerrar F-004.
