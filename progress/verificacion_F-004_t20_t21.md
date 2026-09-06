<!-- progress/verificacion_F-004_t20_t21.md -->
# F-004 · T20 y T21: primer `commit:true` real y su repetición (2026-09-06)

**Autorización expresa del humano** para esta llamada concreta: reclamación
**2811179** (`RS26.08/0123`), usuario **`prueba`** (ide 90, «Usuario de
prueba», elegido por el humano en vez de `pgris`). Ventana:
`SIGRID_DOCUMENT_WRITE_ENABLED=true` puesta a las 09:32, **vuelta a `false`**
tras T21. Script: `t20_t21_commit.py` del scratchpad (no se versiona).

## T20 — la primera escritura en `ruesma_rep` por esta vía

Petición: `contip 708`, `gratipide 35`, `res "PRUEBA API - BORRAR"`,
`nom prueba_f004.pdf`, PDF mínimo de 303 bytes, `sha256`
`9bd10a9b…3571b144` enviado, `commit:true`.

Respuesta **200**: `ok:true committed:true dry_run:false idempotente:false
filas_afectadas:3`. `grafico`: documental **359573**, negocio **298418**, `cod`
**`202609060933388219.prueba`** (sello 09:33 hora de Madrid), `fec` 20260906,
`bytes` 303. `enlace`: `{ide 298858, con 2811179, gra 298418, pos 128, cla 0,
feclee 0, fecalt 0}`. Aviso: «Escritas las tres filas y releídas dentro de la
transacción».

**Comprobación desde fuera, todo lectura:**

| Qué | Resultado |
|---|---|
| `documents/read` (`ruesma_rep`, `gra`, `id_column=cod`) | 303 bytes, `sha256` **idéntico** al enviado |
| 1) negocio `WHERE cod = ?` | 1 fila: ide 298418, emp 1, `res` PRUEBA API - BORRAR, `gratipide` 35, `vin` 3, `ima` NULL, usu prueba, fec 20260906 |
| 2) documental `WHERE cod = ?` | 1 fila: ide 359573, emp 1, `res` `''`, `gratipide` 0, `vin` 3, `DATALENGTH(ima)` 303 |
| 3) enlace por `g.cod` | 1 fila: rcg 298858, con 2811179, gra 298418, pos 128 |
| 4) huérfanos con `res = 'PRUEBA API - BORRAR'` | **ninguna fila** |
| Enlaces del concepto | 296221 (pos 64, `PARTE FIRMADO`) y 298418 (pos 128, la prueba) |

Los `ide` reales coinciden con los provisionales del dry-run de T19 (359573 /
298418 / 298858): nadie escribió entre medias. **El riesgo vivo de `bytes` →
columna `image` queda despejado**: el motor aceptó el parámetro sin `CAST`.

## T21 — idempotencia

La **misma** llamada, `commit:true`: **200**, `ok:true committed:false
idempotente:true filas_afectadas:0`, devuelve el gráfico existente (298418,
mismo `cod`) y avisa «ese documento ya estaba adjunto… el cod que se habría
generado era 202609060934208219.prueba». `COUNT` de enlaces con ese `cod`:
**1**; filas de negocio de la prueba: **1**.

**Criterios de T20 y T21: cumplidos.** El humano abrió el gráfico desde la
ficha de `RS26.08/0123` en Sigrid (obra 0677, unidad «0677.03VILLA 5.») el
2026-09-06: se ve `prueba_f004.pdf` y abre como PDF en blanco, que es lo que se
envió (una página vacía de 303 bytes). **La relación por `(emp, cod)` funciona
de punta a punta.** Queda a su criterio borrar el adjunto de prueba desde la UI.

## Observación menor (no bloquea)

En la respuesta idempotente, `grafico.fec` vale `0` y `grafico.ide_documental`
es `null`, y `enlace.pos` es `null`: la búsqueda de idempotencia (L5) no
devuelve esas columnas. Cosmético; si molesta a un consumidor, L5 puede
devolver `fec`, `d.ide` y `r.pos` sin cambiar nada más.
