<!-- progress/mutacion_F-005.md -->
# F-005 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-005 --workers 6` el 2026-09-06 11:38.

## Alcance

Origen del diff: **rama** (`1a0a9962aee7810865efc5f41f5e5ff330baaa00` .. `feature/F-005-grafico-sin-clase`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/attach_concepto_grafico_use_case.py` | 13 |
| `domain/models/concepto_grafico_models.py` | 5 |
| `infrastructure/security/document_write_guard.py` | 14 |
| **Total** | **32** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 6 |
| Mutantes evaluados | 6 |
| Muertos | 6 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 183.6 s |
| SHA de HEAD medido | `cfb804811843749c486e71f69beae735e641e4b8` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_0` | 89.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_1` | 88.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_2` | 86.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_3` | 85.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_4` | 91.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-005_n0c08dg_/wk_5` | 86.7 |
| Media por mutante evaluado (s) | 30.6 |
| Timeout efectivo por mutante (s) | 184 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historia: las dos campañas anteriores

Esta es la **tercera** campaña de F-005, y la segunda sobre el código final:

| # | SHA | Mutantes | Muertos | Supervivientes | Tiempo |
|---|---|---|---|---|---|
| 1 | `f36a242` (HEAD de T4) | 7 | 6 | **1** | 272,2 s |
| 2 | `d561731` (HEAD de T5) | 6 | 6 | 0 | 220,0 s |
| 3 | `cfb8048` (este informe) | 6 | 6 | 0 | 183,6 s |

La 2 y la 3 miden el mismo código: entre ambas solo se movió un comentario de
sitio. Se relanzó para que el SHA del informe sea el que se entrega.
La 1 se documenta aquí porque su superviviente es lo que llevó al cambio de T5.

### El superviviente de `f36a242`

- Fichero: `application/use_cases/attach_concepto_grafico_use_case.py:276` [booleano]
- Original: `gratipide=0, permitidas=permitidas, existe=False, fecbaj=None`
- Mutado:   `gratipide=0, permitidas=permitidas, existe=True, fecbaj=None`

En T4 el caso de uso tenía DOS llamadas a `validar_clase_de_grafico`: una en la
rama `gratipide == 0`, con `existe`/`fecbaj` escritos a mano, y otra en la rama
normal. Como el guardia vuelve antes de leer `existe` cuando la clase es 0, ese
argumento era **código muerto**: da igual lo que se le pase.

### Cómo se cerró: midiendo, no razonando

1. **No era un falso superviviente de la campaña paralela.** Aplicado el mutante
   en el árbol principal y ejecutada la suite ENTERA en serie, sin contención:
   `1502 passed, 1 skipped, 1 warning in 49.72s`. Sigue vivo.
2. **Canario (medición positiva).** Se sustituyó `existe=False, fecbaj=None` por
   un objeto cuyo `__bool__`/`__int__` lanza `AssertionError`. Si alguien leyera
   el argumento, reventaría. Resultado sobre los tres ficheros de tests que
   recorren esa rama: `108 passed`. Nadie lo lee.
3. **Control negativo (que el canario no fuera vacuo).** Con el canario puesto se
   quitó el `if gratipide == 0: return` del guardia. Resultado:
   `4 failed, 4 passed` con
   `AssertionError: CANARIO: se leyo 'existe'/'fecbaj' en la rama gratipide=0`.
   El canario sí explota cuando el argumento se lee: la medición del paso 2 vale.

Veredicto: **equivalente**, demostrado por medición. Pero en vez de pedirle al
humano que aceptara un equivalente, T5 **quitó el valor muerto**: `_leer_clase`
tiene ahora UN solo punto de llamada al guardia y lo único que cambia con el 0
es que `fila` se queda en `None` por no haber leído. `existe` y `fecbaj` salen de
la verdad, no de una constante. La campaña de este informe, sobre `d561731`, ya
no genera ese mutante: **6 de 6 muertos, 0 supervivientes**.
