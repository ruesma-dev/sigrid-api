<!-- progress/mutacion_F-003_remuestreo.md -->
# F-003 · Remuestreo EN SERIE de la campaña de mutación

Encargo de MEDICIÓN: reevaluar EN SERIE, sin contención, los mutantes de la
campaña paralela de `progress/mutacion_F-003.md` y comparar veredicto a
veredicto. Empezó como muestra de 35 y terminó **cubriendo los 138**. Sin tocar
código de producción, `harness/`, tests ni el informe de la campaña.

## Método

- **HEAD medido**: `e1ac0ddd3c75dc2aa8e472238efbbc913dfad8a2`, el mismo que
  declara la campaña paralela. Alcance recalculado con `harness.alcance`:
  origen `rama`, `f1946d92…` .. `feature/F-003-guardia-bases-cruzadas`, 607
  líneas en 4 ficheros. Idéntico al del informe.
- **Generación idéntica**: `harness.mutacion.generar_mutantes` sobre esas
  líneas → **138 mutantes**, el mismo número. Los 9 supervivientes y los 6
  timeouts publicados se localizan uno a uno ahí (fichero, línea, operador y
  texto mutado): ninguno falta ni queda ambiguo. Los 123 restantes son, por
  definición, los muertos del informe.
- **Selección: EXHAUSTIVA, los 138**. Se hizo en dos vueltas. La 1.ª, de
  muestra: 9 supervivientes + 6 timeouts + **20 muertos al azar** con
  `random.Random(20260905).sample(...)` sobre los 123 ordenados por
  `(fichero, línea, columna, operador)` —**semilla 20260905**, 35 mutantes—. La
  2.ª, a petición del humano para cerrar la incógnita de los falsos muertos:
  **los 103 muertos restantes**, sin muestreo ni semilla. 35 + 103 = **138**.
- **Ejecución**: `git worktree add --detach <scratchpad>/wt_serie HEAD` y
  `ejecutar_campania(..., mutantes=<la tanda>, workers=1)` desde un script
  temporal del scratchpad (no entra en el repositorio), con el `.env` del árbol
  principal volcado al entorno igual que hace la campaña paralela. El árbol
  principal no se mutó nunca y no había nada más corriendo en ninguna vuelta.
- **Reloj**: línea base del worktree **33,3 s** (1.ª vuelta) y **40,4 s** (2.ª),
  las dos en verde; la paralela midió 80,5–88,1 s por worker, y eso es la
  contención. Timeout efectivo en serie **120 s**, el suelo de `rigor.json`; la
  paralela concedió 177 s. Líneas base de cierre también verdes
  (`aviso_base = None` en las dos). Total **1.339,2 s + 1.258,2 s ≈ 43 min**.

## Resultado

**Coinciden 136 de 138**: **123 muerto→muerto** (los 20 de la muestra más los
103 de la 2.ª vuelta, sin una sola excepción), 7 superviviente→superviviente y
6 timeout→timeout. Las dos únicas discrepancias van en la misma dirección:

| Mutante | Paralela | Serie |
|---|---|---|
| `database_reference_guard.py:263` [aritmetico] `fin = indice + 1` → `fin = indice - 1` | superviviente | **timeout** (120 s agotados) |
| `database_reference_guard.py:266` [entero] `if fin + 1 < total` → `if fin + 2 < total` | superviviente | **muerto en 1,9 s** |

- **Falsos muertos (muerto en paralelo, superviviente en serie): 0 de 123.**
  Ni uno. **Ningún muerto de la campaña paralela sobrevive en serie**, así que
  no hay ninguna línea del guardia que la campaña dé por cubierta sin estarlo.
- **Falsos supervivientes: 2**, exactamente los dos ya medidos a mano en las
  secciones «### 6.» y «### 7.» de `progress/mutacion_F-003.md`. El remuestreo
  los reproduce con el mecanismo del propio arnés, no con un experimento aparte.
- Los 6 timeouts vuelven a agotar el reloj sin contención (cuelgues reales) y
  los 7 supervivientes aceptados por el humano siguen sobreviviendo en serie.

## Conclusión sobre C4 bis

**La campaña sirve como evidencia, con la corrección ya escrita en el informe.**
El número que lo sostiene ya no es una cota estadística sino una medición
completa: **0 falsos muertos sobre los 123 muertos, reevaluados TODOS en
serie**, y **136 de 138 veredictos reproducidos**. El sesgo que introduce el
paralelismo es **pesimista**: convierte en «superviviente» lo que se cuelga o
muere. Un sesgo pesimista no esconde huecos de tests, los inventa, y por eso
**ninguna línea del guardia queda sin test por culpa de la campaña**.

**Ya no queda cota que estimar.** La versión anterior de este informe acotaba
los falsos muertos ocultos a «≤ 17 de 123 al 95 %» porque solo se habían
reevaluado 20; esa frase queda **sustituida por el dato medido: 0 de 123**. Lo
único que la campaña paralela hace mal en F-003 es sobrar dos supervivientes, y
los dos están ya identificados y explicados en su informe.

## Rastro

Worktree retirado tras cada vuelta (`remove --force` + `prune`): `git worktree
list` solo muestra el árbol principal y no queda centinela. `git status --porcelain`:
`mutacion_F-003.md` modificado y cuatro `review_F-003_*.md` sin trackear —el
cuarto, `review_F-003_c4bis_red_cobertura.md`, apareció durante esta medición y
no lo ha escrito este encargo—. Ningún fichero de código tocado.
