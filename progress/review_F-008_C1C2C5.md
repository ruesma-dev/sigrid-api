<!-- progress/review_F-008_C1C2C5.md -->
Revisión completa (pasada 1) · trozo C1C2C5 · `ccfb334..2879ddb` (HEAD `2879ddb9c6ba2b05a6974fd5c13216450065228e`)

# Review F-008 · trozo C1, C2, C5 + Evidencias + barrido de datos reales

**Veredicto: CHANGES_REQUESTED**

**Nivel de rigor:** `critico`, declarado en `harness/features.json` (entrada F-008). Este trozo no juzga las puertas de
C4 bis (mutación, fase RED); solo comprueba que la cobertura y los totales de la suite que cita el informe coinciden con
lo medido aquí.

**Fuera del trozo:** la lógica, C3, C3 bis, C4 y C4 bis, y los documentos. Los revisan otros revisores.

## Medición propia (un único `bash harness/init.sh`, exit 0, en `2879ddb`)

- `4204 passed, 1 skipped, 1 warning in 110.74s`
- `PUERTA COBERTURA: 99.2% de 1195 líneas cambiadas cubiertas (1186/1195, umbral 80%, nivel critico)` `[OK]`
- `PUERTA TAMAÑO: F-008 dentro de los topes (requirements 149/150, design 229/250, impl 146/220)` (también con
  `python -m harness.tamano --feature F-008`, exit 0)
- `[OK] BACKLOG.md al día`; `python harness/backlog.py --comprobar` da exit 0
- `ENTORNO LISTO. Puedes trabajar.`
- `pytest tests -k f008 --collect-only -q`: `411/4205 tests collected` (recogidos, no ejecutados de nuevo; la suite
  entera ya pasó)

## Sección «Evidencias» de `progress/impl_F-008.md:130-146`

| Número del informe | Medido aquí | ¿Coincide? |
|---|---|---|
| 4204 passed, 1 skipped | 4204 passed, 1 skipped | sí |
| 411 de F-008 | 411 recogidos con `-k f008` | sí |
| 99,2 % de 1195 líneas (1186/1195) | idéntico | sí |
| 84,90 s | 110,74 s | sí, salvando la variación de reloj: había seis revisores trabajando en paralelo sobre la misma máquina |

**¿Son de este HEAD?** Sí. El último commit con código es `192b3eb` (T20). `2879ddb` solo toca `progress/current.md` y
`progress/impl_F-008.md`, así que el código no ha cambiado desde que se midió. Las cifras de la línea `:137`
(568/467/101, HEAD `eba243e`) son de la campaña de mutación (C4 bis) y las juzga otro revisor; el propio informe ya
avisa en `:145-146` de que la campaña es anterior a T20.

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` termina con exit 0 (ver arriba).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`, `progress/history.md`,
      `docs/ARCHITECTURE.md` y `docs/CONVENTIONS.md`: `init.sh` los da por presentes y ninguno sale del diff.

### C2 — El estado es coherente
- [x] Hay una sola feature `in_progress`, que es F-008.
- [x] La rama es `feature/F-008-registrar-factura`, la misma que dice `features.json`.
- [ ] `progress/current.md` describe la sesión activa sin restos que la contradigan → **H2**.
- [x] Toda feature `done` tiene su resumen en `history.md`: ningún id `done` falta en ese fichero.
- [x] Lo que pedía el encargo: `tasks.md` tiene T0-T20 `[x]` y T21-T25 `[ ]`; `BACKLOG.md` está regenerado (pasa
      `--comprobar` y su diff es solo el cambio de estado a «en curso»); los topes de tamaño están dentro.

### C5 — La sesión se cerró bien
- [ ] Un commit `F-XXX Tn:` por tarea → **H1**.
- [x] Todas las tareas `[x]`: **N/A justificado para T21-T25.** T21 es esta misma revisión; T22-T24 son tareas
      MANUAL (humano) que, según `tasks.md:28-30` y `current.md:12`, van detrás de la revisión; T25 es el `init.sh`
      final. Las 21 tareas de implementación (T0-T20) están `[x]`.
- [x] No hay ficheros temporales sin trackear: `git status` está limpio. Entre los ignorados, el único posterior al
      2026-10-29 es `.coverage`, que genera la propia puerta de cobertura. Los `*.txt` y `*.csv` ignorados de la raíz
      son de 2026-06 y no tienen que ver con esta feature.
- [x] `features.json` refleja el estado real: `in_progress`, rigor `critico`, la rama correcta.
- [x] Los 25 commits del rango están en español (sin tildes, pero legibles) y todos llevan `Co-Authored-By`.

## Barrido de datos reales en todo el diff (8.904 líneas añadidas)

Limpio. Lo que hay:
- **CIF y NIF:** solo ficticios (`B00000000`, `B00000001`, `B00000002`, `B99999999`), en los tests.
- **Razones sociales:** solo `PROVEEDOR SL`, `PROVEEDOR UNO SL` y `PROVEEDOR DOS SL`, en los tests.
- **IBAN y cuentas bancarias:** solo de ceros, de unos o de cuatros (`ES0000…`, `ES1111…`, `4444444444`).
- **Personas:** ningún nombre propio. Las apariciones de «ruesma» son el nombre de la base `ruesma_rep`.
- **Emails, IPs o claves:** ninguno.
- **Códigos internos que sí aparecen:**
  - `obra 0404` y `CTSU16/0206` son las obras de prueba ya pactadas en features anteriores.
  - `FRGG26/2731` (`explore_F-008.md:252`) es un máximo agregado de la serie.
  - Ninguno de los tres identifica a una persona ni a un proveedor.

## Cambios requeridos

1. **H1 · C5, falta un commit por tarea.**
   - `517ddd2` agrupa T9 y T10, y `1da3d67` agrupa T12, T13 y T14. Son 18 commits para 21 tareas.
   - Además, `progress/impl_F-008.md:26` afirma «un commit por tarea T0-T20», y eso es falso.
   - **Qué pido:**
     - No reescribir la historia.
     - Corregir `impl_F-008.md:26` y declarar las dos agrupaciones como desviación, con su motivo. Por ejemplo, que
       T12-T14 forman una sola transacción y sus tests en rojo son comunes, como ya muestran `:101-102`.
     - Que el líder lleve esa desviación al humano para que la acepte por escrito.
2. **H2 · C2, `progress/current.md` tiene partes que hoy no son verdad o contradicen la spec v3.1.** Hay precedente:
   el mismo motivo rechazó F-016 en su trozo C1C2C5, y era la quinta feature seguida.
   - **`current.md:10-11`** dice a la vez «**Implementer en curso con T0-T20**» e «**Implementer terminado
     (T0-T20)**». Hay que quitar la primera frase.
   - **`current.md:47-51`, sección «F-008 espera (2026-10-19)».** Es un resto anterior a la spec. Pide «forma de pago y
     vencimiento por defecto del contrato o `prv`», que choca con los vencimientos del llamante de la spec v2/v3.1 y
     con T15, «ningún cálculo de vencimiento». Hay que borrar la sección o fundirla en la de `:8`.
   - **`current.md:187-190`, «Prompt para retomar».** No nombra F-008, que es la única `in_progress`. Hay que añadir
     qué está en curso: F-008 en revisión (T21) y después T22-T24 manuales con autorización expresa.

## Propuesta de automejora (no aplicada)

H2 se repite feature tras feature (la revisión de F-016 ya contaba cinco seguidas). Se podría hacer que `harness/tamano.py`, o una sección de `init.sh`, avise
cuando la feature `in_progress` no aparezca en el bloque «Prompt para retomar» de `current.md`. Es una comprobación
barata que caza el fallo más repetido de C2.
