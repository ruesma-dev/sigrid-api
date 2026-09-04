<!-- progress/review_F-003.md -->
Revisión incremental desde `b70a689` (pasada 2) · delta `b70a689..936432c`, 7 commits

# F-003 · Informe de revisión

**Veredicto: RECHAZADO (CHANGES_REQUESTED).**

**Rigor `critico`** (declarado en `features.json`): C1–C5, fase RED, cobertura,
mutación con cero supervivientes *o* justificación aceptada por el humano, y las
`MANUAL` con su comando.

**Lo que se rechaza es UNA línea de código, no el trabajo.** Los seis cambios que
exigí están atendidos, varios muy bien: campaña hecha y verificable (§2),
«Evidencias» completa, `tasks.md` marcado (T8 fuera por MANUAL), `current.md`
reescrito con T8 y su comando, **0 tests fuera de la convención `test_f003_rN_`** y
los dos falsos positivos corregidos con tests. Pero uno de esos arreglos **abrió el
guardia más de lo que dice abrirlo**, y lo que se cuela viola R11.

**De la pasada 1** (detalle en el commit `7d5d9ba` de este fichero): rechacé el
papeleo, no la defensa. Sigue siendo cierto, y no lo repito, que ninguna consulta
legítima falla, que los tests no se engañan (26 caen al neutralizar el detector), que
el orden de las defensas anteriores está intacto y que `sigrid/*` no pasa por aquí.

## 1 · Lo que bloquea: el descarte de la parte vacía viola R11

`database_reference_guard.py:104` descarta la última parte vacía para dejar pasar
`dbo.con.*`. El caso está bien visto, pero la condición no mira **qué** sigue al punto
final: descarta siempre. Comparando el fichero de `b70a689` con el de `HEAD` sobre 26
formas hostiles, **ocho pasan de `rechaza` a `PASA`**: `tempdb..#t`,
`tempdb.dbo.##global`, `ruesma_rep.dbo.#t`, `...dbo.$x`, `...dbo.9tabla`, `...dbo.*`,
`...dbo. ` y `dbo.con.*` (este último, el correcto).

`tempdb..#t` y `tempdb.dbo.##global` son **T-SQL válido** y `tempdb` no está en
`ALLOWED_DATABASES`; `SqlQueryGuard` no tiene lista de prefijos de tabla, así que con
`database:"ruesma"` esa lectura llega hoy al motor. No es la vulnerabilidad que F-003
vino a cerrar —`ruesma_rep` sigue bloqueada en todas las formas que probé: `..`,
corchetes, comillas, `.*`, subconsulta, CTE, comentario intercalado—, pero **es lo
que R11 prohíbe**: ante un tercer elemento que el analizador no sabe leer, el guardia
deja pasar. La docstring dice lo contrario, y el §7 del informe afirma que los
arreglos «reducen los rechazos **sin ampliar lo que pasa el filtro**».

Arreglo: **descartar la parte vacía final solo si lo que sigue al punto es `*`**; si
no, se rechaza. Comprobado: `dbo.con.*` sigue pasando y las otras siete rechazan.

## 2 · La campaña de mutación, verificada de forma independiente

- **Totales recalculados** con `harness.alcance` + `generar_mutantes` (cálculo puro):
  4 ficheros, **513 líneas** (237/18/17/241), **129 mutantes**, idénticos a los del
  informe. Los 13 supervivientes y los 6 timeouts existen como mutantes reales, mismo
  operador y texto original→mutado.
- **Campaña NO reejecutada: 1.363,6 s (22,7 min) según el informe**, por encima del
  umbral de 60 s; aplico recálculo puro + RM1–RM6, como manda el protocolo.
- **RM1** [x] SHA medido `539f1f6`; de ahí a HEAD solo cambian `progress/` y
  `tasks.md`. Ni un fichero de alcance ni un test: los veredictos siguen valiendo.
- **RM2** [x] Media 10,6 s × 8 workers = **84,8 s por mutante**, por encima de la
  línea base (51,6–54,6 s). Lejísimos del segundo que haría sospechar.
- **RM3** [x] Ningún equivalente sale muerto. **RM6** [x] N/A: no se mató ningún
  mutante quitando código defensivo; esta pasada **añadió** una guarda.
- **RM5** [x] Reproduje **los 13**, no la muestra de uno: cada mutación aplicada a una
  copia en scratchpad y comparada con el original sobre 50 entradas dirigidas + 4.000
  aleatorias. **Cuatro análisis no se sostienen** (§3).
- Sin cabecera «CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.

## 3 · Los supervivientes: la decisión del humano vale, el análisis no

El humano aceptó por escrito cerrar con los 13 y el rigor `critico` lo admite: **no
discuto la decisión**, sino los hechos con que se pidió. «Siete de aritmética de
escapes cuyo resultado observable no cambia», dice el informe: falso para cuatro.

| Sup. | Medido |
|---|---|
| **12** | **NO equivalente**: `SELECT a*/*ruesma_rep.dbo.gra*/b` —un `*` de multiplicar pegado al comentario, T-SQL corriente— da `[]` en el original y **rechazo** en el mutante. El motivo escrito es incorrecto: no hace falta un comentario delante, basta un operador |
| **7, 8, 9** | **NO**: `SELECT [a]] FROM x` → el original **rechaza** (corchete sin cerrar), el mutante devuelve `[]`. Falla **abierto**. El 7, igual con `SELECT * FROM [gra]]`. El **10** difiere en 27 de 4.000 entradas aleatorias |
| **6** | **Cuelga** (bucle infinito) con `SELECT [a][b] FROM x`. No es matable con un test limpio, pero la razón escrita no es la real |
| 1–5, 11, 13 | **Equivalentes, confirmado**: 0 diferencias en 4.050 entradas |

Los cuatro se matan con tests de una línea que fijan el **fallo cerrado** ante un
delimitador mal formado —R11, no acoplamiento a un índice—: eran fáciles de escribir.

**El test de propiedad SÍ cubre lo que dice**: sus **605** casos rechazan **nombrando
`otra_base`** (ninguno por un motivo colateral), y la variante con el contexto
**delante** de la referencia —el `antes` se concatena en realidad detrás— no da un
solo falso negativo más. La pega es de nombre, no de fondo.

## 4 · Checkpoints

**C1** [x] `init.sh` en `ENTORNO LISTO`: **1.210 pasan**, 1 skip; cobertura **99,2 %**
(244/246). [x] Ficheros exigidos. **C2** [x] Una sola `in_progress`, rama correcta,
`history.md` al día, `current.md` reescrito con T8 y su comando.

**C3** [x] Hexagonal: el detector no importa `Settings` ni dominio. [x] Ruta en
primera línea. [x] Sin prints, secretos ni dependencias nuevas. [x] `ruff`: 79 avisos,
los mismos de antes de la feature.
- [ ] **Regla «ante la duda, rechaza» rota** por `guard.py:104` (§1). `ruesma` y
  `ruesma_rep` siguen bien protegidas; lo que se abre es `tempdb`.

**C4** [x] R1–R11 con test trazable y en verde. [x] Ningún test toca red ni BBDD.
[x] T8 en `current.md` con su comando exacto. Trazabilidad: el nombre la lleva —r1:6,
r2:3, r3:10, r4:3, r5:8, r6:3, r7:3, r8:4, r10:22, r11:8, **869 casos** con `-k
f003`—. R9, por construcción del conjunto.

**C4 bis** [x] `rigor` declarado. [x] Fase RED con traza real. [x] Cobertura `[OK]`.
[x] Mutación verificada de forma independiente (§2). [x] Muertos: campaña no
reejecutada por pasar de 60 s, dicho por escrito. [x] Coste/mutante 84,8 s ≫ 1 s.
[x] RM1, RM2, RM3, RM6. [x] Supervivientes analizados y aceptados por escrito.
- [ ] **RM5: cuatro «equivalentes» no lo son**, y se demuestra con una línea cada uno
  (§3). El checkbox pide demostración ejecutable; la reproduje y falla.

**C3 bis / C4 ter** — **N/A justificados**: la feature no toca `docs/referencia/`
(nada que barrer) y no existe `harness/rutas_sensibles.json`, solo el ejemplo.

**C5** [x] `tasks.md` completo. [x] Árbol limpio. [x] `features.json` coherente. Los
commits de esta pasada llevan `F-003 Tn:`; los dos primeros no, pero eso fue lo que
pedí en la pasada 1. **El fichero mutado no está en ningún commit**: comprobado en los
8 de la rama uno a uno y con `git log -S` sobre todo el historial, `insert(0)`.

**La condición del humano se sigue cumpliendo.** Reejecuté
`scripts/verificar_sql_ecosistema.py`: **13.637 ficheros, 256 consumidores, 0
rechazos, exit 0**. Y de las 26 formas hostiles del §1, ninguna que hoy funcione
empieza a fallar: los ocho cambios dejan pasar más, no menos.

## 5 · Cambios requeridos

1. **`database_reference_guard.py:104`**: descartar la parte vacía final **solo si lo
   que sigue al punto final es `*`**; si no, tratarlo como referencia de tres partes.
2. **Tres tests** que lo fijen: `SELECT * FROM tempdb..#t` rechaza,
   `SELECT * FROM ruesma_rep.dbo.#t` rechaza, `SELECT dbo.con.*` sigue pasando.
3. **Corregir el §7 del informe**: «sin ampliar lo que pasa el filtro» es falso; decir
   qué se amplió y por qué queda acotado.
4. **Corregir los análisis 6, 7, 8, 9, 10 y 12** de `mutacion_F-003.md` con lo medido
   en §3, y añadir los tests de una línea que matan 7, 8, 9 y 12 (fallo cerrado ante
   `[a]]` sin cerrar; comentario pegado a un `*`). No hace falta relanzar la campaña.
5. Menor: «Evidencias» dice 98,4 % de cobertura y la puerta mide 99,2 %; y T13 se marcó `[x]` rezando «cero supervivientes». Ajustar ambos.

## 6 · Automejora (propuesta, no aplicada)

1. De la pasada 1: `init.sh` no avisa de que falte `mutacion_F-XXX.md` en `critico`.
2. **RM5 se queda corta en `critico`**: pide reproducir **uno** de los equivalentes.
   Reproducirlos todos costó ~15 min y destapó cuatro análisis falsos que la muestra
   de uno se habría saltado con probabilidad 9/13. Propongo, en `critico`, todos.
