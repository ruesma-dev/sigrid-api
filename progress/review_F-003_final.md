<!-- progress/review_F-003_final.md -->
# F-003 · Revisión FINAL: mutación, reglas RM y veredicto consolidado

Revisión sobre `e1ac0ddd…` (HEAD al medir) y **cierre tras `c15f6b7`**. Ámbito:
la puerta de **mutación** de C4 bis con sus RM, y el veredicto consolidado.

- **Puerta de mutación + RM1–RM6: APROBADA.**
- **Veredicto consolidado: APROBADO.** Emití CHANGES_REQUESTED por un único
  defecto documental; corregido en `c15f6b7` y verificado abajo.
- Rigor `critico`: cero supervivientes salvo justificación aceptada por el
  humano. Los 7 la tienen, y la doy por buena.

## Verificación independiente (no me creí el informe)

Recalculado con `harness.alcance` y `generar_mutantes` (cálculo puro): **607
líneas** en 4 ficheros y **138 mutantes**, idénticos al informe; los **9**
supervivientes existen como mutantes reales con el mismo operador y texto
original→mutado (muestreé 137, 166×2, 224, 225, 263, 266, 286 y 40). **Campaña
NO reejecutada**, y consta: 1.681,8 s, muy por encima del umbral de 60 s. Coste por mutante = 1.681,8 × 8 ÷ 138 = **97,5 s** contra línea base
80,5–88,1 s: coherente, y mayor porque 7 mutantes agotan los 177 s.

## Checkpoints de mi ámbito

- [x] Totales verificados; sin «⚠ CAMPAÑA NO VÁLIDA»; base rota = 0.
- [x] **Muertos comprobados**: campaña > 60 s → recálculo puro + RM, y el
      remuestreo EN SERIE de los 138 da **0 falsos muertos** sobre 123.
- [x] **RM1** SHA declarado = HEAD y alcance medido = alcance revisado. **RM2**
      media 12,2 s × 8 workers = 97,6 s ≈ base 84 s. **RM3** ningún equivalente
      sale MUERTO: 263 y 266, los reclasificados, se declaran NO equivalentes.
      **RM6** no se quitó código defensivo; el diff de `infrastructure/` no borra
      ninguna guarda.
- [x] **RM5** (obligatoria en `critico`) · Reproduje **uno** a mi elección, el
      superviviente 4 (224, `and`→`or`), en un `git worktree` desechable: base
      **1.262 pasan** en 32,2 s y, con el mutante, **1.262 pasan** en 33,1 s →
      superviviente real. Diferencial propio de **1.900 entradas**: **0
      diferencias** por la API pública; las 276 que salen son del privado
      `_normalizar_identificador` con cadenas que `_IDENT` nunca produce.
- [x] **«Evidencias» del implementer**: estaba con los números **previos a
      T16**; `c15f6b7` la reescribe sobre `e1ac0dd`. Verificado abajo.

## Fondo, no formulario

**¿Legítimo cerrar con una herramienta que clasifica mal?** Sí: su sesgo es
**pesimista** —hace superviviente lo que se cuelga o muere—, así que inventa
huecos en vez de esconderlos, y la puerta no descansa en la campaña
paralela sino en el remuestreo EN SERIE de los 138, con **0 falsos muertos sobre
123**. Medición completa, no cota: **ninguna línea del guardia queda dada por
cubierta sin estarlo**, y los 7 timeouts tampoco son hueco (bucles que
`..._no_cuelgan` caza). La nota de corrección de Totales es fiel a lo medido:
124+7+7 = 138, «263 se cuelga» = el `EXIT=124`, «266 muere en 1,9 s» = el
remuestreo. **Reaudité el análisis que olía mal**, el del superviviente 8 (286,
`''`), equivalente con motivo flojo cuando su gemelo del 266 (`]]`) resultó NO
equivalente: **0 diferencias en 588 entradas** al borde exacto, luego acierta;
la razón que falta es que `'` abre y cierra, y `]` solo cierra.

## El defecto pedido, corregido y verificado (`c15f6b7`)

§5 citaba 132 mutantes / 118 muertos / 1.724,0 s, suite de 1.241 y cobertura
244/246 —**previos a T16**—, y §5.1 decía «seis campañas». `c15f6b7` la reescribe
sobre `e1ac0dd` y **cuadra línea por línea** con lo que medí y con los dos
informes de mutación: 138 mutantes, **124 muertos / 7 supervivientes / 7
timeouts** tras la corrección medida (la campaña publicó 123/9/6), 1.681,8 s con
8 workers, suite **1.262 pasan**, cobertura **254/256**, siete campañas y una
fila nueva con el remuestreo (**0 falsos muertos sobre 123**). **Nada contradice**
`mutacion_F-003.md` ni el remuestreo. El título de la sección lleva ya el SHA
medido: mi automejora nº 3, aplicada. Fichero en **220/220**.

## Para cerrar

1. F-003 a `done` y regenerar `BACKLOG.md`; **el merge a `dev`, el humano**. T8
   (MANUAL, post-despliegue) no bloquea el cierre: deuda ya anotada.

## Automejora propuesta (no aplicada)

1. **Dar reloj al test anti-cuelgue** (`pytest-timeout`): los 7 timeouts serían
   muertos limpios. Portable a `arnes-base`.
2. **Diagnosticar `harness/mutacion_paralela.py`**; el arreglo, a `arnes-base`.
3. **C4 bis: que «Evidencias» declare el SHA de su campaña** (RM1 sobre el
   informe del implementer). Ya aplicada a mano en `c15f6b7`.
