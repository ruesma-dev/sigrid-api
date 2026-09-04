<!-- progress/current.md -->
# Trabajo en curso

## F-003 · El guardia valida también las bases nombradas dentro del SQL

| | |
|---|---|
| **Estado** | `in_progress` · rigor `critico` |
| **Rama** | `feature/F-003-guardia-bases-cruzadas` |
| **Spec** | `specs/F-003-guardia-bases-cruzadas/` (R1–R11) |
| **Implementación** | [`progress/impl_F-003.md`](impl_F-003.md) |
| **Revisión** | [`progress/review_F-003.md`](review_F-003.md) — **RECHAZADO en la pasada 1** |
| **Condición innegociable del humano** | «No puede fallar la escritura/lectura que se hace ahora» |

### Dónde está

El código está hecho y el reviewer confirma que **la condición del humano se
cumple**: comprobó por su cuenta que ninguna consulta legítima del ecosistema
empieza a fallar, que los tests no se engañan (26 caen al neutralizar el
detector) y que no se relajó ninguna defensa anterior. Lo que rechazó fue el
**papeleo del rigor `critico`** y dos falsos positivos no previstos.

### Atendido de los seis cambios requeridos

| # | Cambio | Estado |
|---|---|---|
| 1 | Campaña de mutación | hecho: 129 mutantes, **110 muertos, 13 supervivientes**, 6 timeouts, 8 workers, 22,7 min |
| 2 | Completar «Evidencias» del impl | hecho, §5 y §5.1 |
| 3 | Marcar `tasks.md` | hecho (T1–T7, T9–T12; T8 queda por ser MANUAL) |
| 4 | Reescribir este fichero con T8 y su comando | hecho, es esto |
| 5 | Renombrar los tests a `test_f003_rN_...` | hecho, 106 tests recogidos por `-k f003` |
| 6 | Anotar los dos falsos positivos | hecho, y además **corregidos** (ver abajo) |

**Los dos falsos positivos se corrigieron en vez de solo anotarse**, porque van
justo en la dirección de la condición del humano —que nada legítimo se rechace—
y ninguno abre un agujero:

- `SELECT dbo.con.*` se leía como tres partes. Ahora una última parte vacía se
  descarta, salvo la del medio de `base..tabla`, que sí cuenta.
- `SELECT [Client's Name] ...` moría con «literal sin cerrar», porque el
  apóstrofo dentro de un identificador entre corchetes arrancaba un literal
  falso. Ahora el neutralizador conoce el corchete como delimitador, con su
  escape `]]`.

### Verificaciones MANUAL

**T8 — comprobar contra la API ya desplegada que la lectura cruzada sigue
funcionando.** Solo se puede hacer **después** de desplegar la feature, y la
ejecuta el humano. Comando exacto:

```bash
cd C:/Users/pgris/PycharmProjects/albaranes-persistencia
python scripts/diagnose_sigrid_contrato_docs.py
```

Ese script usa `LEFT JOIN {database_rep}.dbo.gra`, que es justo el patrón que
el guardia nuevo tiene que seguir dejando pasar. **Criterio:** devuelve lo
mismo que antes del despliegue, sin ningún error de «base de datos no
permitida». Si fallara, la causa sería que `ruesma_rep` no está en
`ALLOWED_DATABASES` de la Function App, no el guardia.

### Lo siguiente, y hace falta el humano

**Los 7 supervivientes necesitan una aceptación NUEVA.** La que se dio el
2026-09-04 cubría trece, y la pasada 2 demostró que **cuatro de aquellos
análisis eran falsos**: no eran equivalentes, hacían que el guardia fallara
abierto y eran matables con un test de una línea. Esa aceptación queda anulada
por apoyarse en hechos incorrectos; los cuatro están muertos y otros dos
desaparecieron al corregir el reconocedor.

Los **siete** que quedan son exactamente los que el reviewer verificó de forma
independiente como equivalentes, con **0 diferencias en 4.050 entradas cada
uno**. Recorrido completo: **52 → 18 → 13 → 10 → 7**.

Después: tercera revisión, y el merge a `dev`, que hace el humano.

### Pendiente de decisión del humano, fuera de F-003

- **`ALLOWED_DATABASES` incluye `master`** en la Function App desplegada, y
  ningún consumidor lo necesita. Quitarlo es una línea de configuración.
- **`MAX_ALLOWED_ROWS = 500000`** desplegado, frente a los 1.000 que documenta
  `azure-apps/sigrid_api.md`. Uno de los dos está mal.
- **`user_rw` tiene `UPDATE` sobre `ruesma_rep.dbo.gra`**, donde vive la única
  copia de los 359.438 documentos, en una base con recuperación `SIMPLE`. No se
  probó si tiene `DELETE`. Merece una conversación con quien administre el
  motor.
- **`azure-apps/sigrid_api.md` está modificado y sin commitear** en su
  repositorio: §2.1 y §5.1, corregidas por esta feature.
- **Mejora del arnés propuesta por el reviewer**: `init.sh` no avisa de que
  falte `progress/mutacion_F-XXX.md` en rigor `critico` o `estandar`. Este
  rechazo se habría evitado con ese aviso. Si se hace, hay que portarlo a
  `arnes-base`.
