<!-- progress/current.md -->
# Trabajo en curso

> **Sesión cortada el 2026-09-05 por contexto agotado, con el árbol limpio y
> todo commiteado.** El prompt para retomar está al final de este fichero.

## F-003 · El guardia valida también las bases nombradas dentro del SQL

| | |
|---|---|
| **Estado** | `in_progress` · rigor `critico` · **falta solo la revisión final** |
| **Rama** | `feature/F-003-guardia-bases-cruzadas`, 20 commits sobre `dev` |
| **Spec** | `specs/F-003-guardia-bases-cruzadas/` (R1–R11) |
| **Implementación** | [`impl_F-003.md`](impl_F-003.md) |
| **Revisiones** | [`review_F-003.md`](review_F-003.md) (pasadas 1 y 2) · [`review_F-003_reconocedor.md`](review_F-003_reconocedor.md) (auditoría del código) |
| **Mutación** | [`mutacion_F-003.md`](mutacion_F-003.md) |
| **Condición innegociable del humano** | «No puede fallar la escritura/lectura que se hace ahora» |

### Qué hace la feature

`SqlWriteGuard` y `SqlQueryGuard` validaban el campo `database` de la petición,
que es la base de la **conexión**. Como en SQL Server una sentencia salta a otra
base de la misma instancia con solo cualificar el nombre, con
`database: "ruesma"` se podía escribir en `ruesma_rep`: la política que
`ALLOWED_WRITE_DATABASES` decía aplicar **no estaba aplicada**.

Lo cierra `infrastructure/security/database_reference_guard.py`, un reconocedor
de nombres cualificados —no un analizador de T-SQL—. Tres o más partes se
validan contra la lista blanca; cuatro o más se rechazan siempre. Sin variable
de entorno para desactivarlo, a propósito.

### Estado de verificación: todo en verde

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO** |
| Suite | **1.262 pasan**, 1 skip |
| Cobertura | **99,2 %** (254/256), umbral 80 % |
| `ruff` | **79 avisos**, los mismos que antes de la feature |
| Verificador del ecosistema | **0 rechazos** sobre 13.639 ficheros, 256 consumidores |
| Puerta de tamaño | los cuatro ficheros dentro de sus topes |

### Lo que queda, por orden

1. **Relanzar la campaña de mutación.** El código cambió después de la última
   (se tocaron `_IDENT`, el cierre del comentario `--` y dos condiciones), así
   que `mutacion_F-003.md` describe un código que ya no existe.
   `python -m harness.mutacion --feature F-003 --workers 8`, unos 25 min, con el
   árbol limpio. Si salen supervivientes nuevos, analizarlos **midiendo**, no
   leyendo: aplicar cada mutante a mano y ver si la suite lo mata.
2. **Segundo encargo al reviewer**, el del papeleo: `CHECKPOINTS.md` entero, los
   informes y `tasks.md`. **Trocearlo**: una revisión se colgó por agotar su
   tiempo con un encargo demasiado grande, y la que mejor funcionó fue la
   acotada a un solo fichero con una sola pregunta.
3. Cerrar la feature y **merge a `dev`, que lo hace el humano**.

### Los 7 supervivientes de mutación, aceptados

El humano los aceptó el 2026-09-04, verificados de forma independiente por el
reviewer (0 diferencias en 4.050 entradas cada uno). **Una aceptación anterior,
de 13, quedó ANULADA** porque cuatro de aquellos análisis eran falsos. Consta
en `mutacion_F-003.md`.

### Historia de los fallos, y la lección

Cuatro rondas de revisión, **seis fallos encontrados**, tres de ellos agujeros
que **dejaban pasar**:

| # | Fallo | Cómo se encontró |
|---|---|---|
| 1 | `SELECT dbo.con.*` se rechazaba | Reviewer, pasada 1 |
| 2 | `[Client's Name]` moría con «literal sin cerrar» | Reviewer, pasada 1 |
| 3 | El arreglo de (1) **abrió** el guardia: `tempdb..#t` se colaba | Reviewer, pasada 2 |
| 4 | `SELECT 1 AS "z--", … FROM msdb.…` **se colaba** | Reviewer, pasada 3 |
| 5 | Un salto de línea en un alias delimitado **escondía la referencia** | Auditoría del reconocedor |
| 6 | Un `--` cerrado solo por CR blanqueaba la sentencia entera | Auditoría del reconocedor |

**Cinco de los seis eran la misma causa:** el neutralizador y el reconocedor
leían los identificadores delimitados con **reglas distintas**. Cada vez que
difieren en algo —un apóstrofo, un escape `]]`, un `--`, un salto de línea— el
análisis se desincroniza y una referencia puede esconderse dentro de un falso
identificador. Se parchearon caso a caso durante tres rondas hasta unificarlos,
y esa unificación debió ser el primer arreglo.

> **Si aparece un séptimo de la misma familia, no lo parchees.** La
> recomendación es reemplazar el reconocedor por un **tokenizador propio** de
> unas veinte líneas que recorra la sentencia una sola vez y clasifique cada
> tramo (literal, comentario, delimitado, identificador). Es más código, pero
> elimina la clase entera de fallos por construcción en vez de perseguirla.

### Verificación MANUAL pendiente, y la hace el humano

**T8 — solo se puede hacer DESPUÉS de desplegar.** Comprobar contra la API ya
desplegada que la lectura cruzada sigue funcionando:

```bash
cd C:/Users/pgris/PycharmProjects/albaranes-persistencia
python scripts/diagnose_sigrid_contrato_docs.py
```

Usa `LEFT JOIN {database_rep}.dbo.gra`, que es el patrón que el guardia tiene
que seguir dejando pasar. **Criterio:** devuelve lo mismo que antes, sin ningún
error de «base de datos no permitida».

## Pendiente de decisión del humano, fuera de F-003

- **`ALLOWED_DATABASES` incluye `master`** en la Function App, y ningún
  consumidor lo necesita. Quitarlo es una línea de configuración.
- **`user_rw` tiene `UPDATE`** sobre `ruesma_rep.dbo.gra`, donde vive la única
  copia de los 359.438 documentos, en una base con recuperación `SIMPLE`. No se
  probó si tiene `DELETE`. Merece una conversación con quien administre el
  motor.
- **Mejoras del arnés propuestas por el reviewer**, sin aplicar: `init.sh` no
  avisa de que falte `mutacion_F-XXX.md` en rigor `critico`; y RM5 pide
  reproducir **un** equivalente, cuando reproducirlos todos costó 15 min y
  destapó cuatro análisis falsos. Si se hacen, **hay que portarlas a
  `arnes-base`**.
- **F-004** (endpoint `sigrid/concepto-grafico`) espera a que cierre F-003. Su
  propuesta está actualizada con lo medido, y entre sus criterios está corregir
  `dedicacion.md`, `partes.md` y `remesas.md` de `azure-apps`, que siguen
  llamando «réplica que no admite escritura» a `ruesma_rep`.

## Estado de los repositorios

- `sigrid-api`: rama `feature/F-003-guardia-bases-cruzadas`, 20 commits sobre
  `dev`. `dev` está **7 commits por delante de `origin/dev`**, sin empujar.
- `azure-apps`: 1 commit local (`5967cd8`), sin empujar.
- **Nada se ha empujado a ningún remoto**, como manda el protocolo.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md` y retoma F-003. Está todo commiteado
> y en verde; falta relanzar la campaña de mutación y pasar al reviewer el
> segundo encargo, el del papeleo, troceado.
