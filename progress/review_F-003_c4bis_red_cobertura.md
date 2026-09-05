<!-- progress/review_F-003_c4bis_red_cobertura.md -->
# F-003 · Review acotada C4 bis: fase RED + cobertura

**Ámbito de este informe:** SOLO las puertas de fase RED y cobertura de C4
bis. **La puerta de mutación y las reglas RM1-RM6 quedan explícitamente FUERA
de este encargo** (hay una campaña de mutación en curso, medida por otro
encargo aparte). No se ha ejecutado `bash harness/init.sh` ni la suite
completa, por la misma razón: se ha reutilizado el `coverage.json` ya
generado en esta sesión (mtime posterior a HEAD) con
`python -m harness.cobertura --base dev --cov coverage.json`.

## Veredicto: APPROVED (solo este ámbito)

## Rigor aplicado

`F-003` declara `rigor: "critico"` en `harness/features.json` (no es
por-defecto). Exige fase RED en requisitos centrales y cobertura ≥ 80 % de
las líneas cambiadas.

## 1 · Fase RED

`progress/impl_F-003.md` §2 trae traza real de fallo antes de existir el
código, para los tres bloques centrales (`tasks.md` T1/T3/T5):

- T1 (R3, R4, R5, R11 — reconocedor): `ModuleNotFoundError` porque el módulo
  no existía.
- T3 (R1, R2, R6 — guardia de escritura): `10 failed, 11 passed`, y fallan
  **exactamente** los que exigen rechazo.
- T5 (R7, R8 — guardia de lectura): `13 failed`, con un fallo de andamiaje
  documentado (doble sin `max_rows`) distinguido del fallo real del guardia.

Es traza real, no una afirmación de «se hizo TDD», y cubre los requisitos
centrales R1-R8. **[x] Fase RED.**

## 2 · Cobertura

`bash harness/init.sh` midió en esta sesión: **99,2 % de 256 líneas
cambiadas (254/256), umbral 80 %, nivel critico** → `[OK]`.

Repetido de forma independiente con
`python -m harness.cobertura --base dev --cov coverage.json`: mismo
resultado exacto, `254/256`. Cruzando `harness.alcance` con
`coverage.json` (`executed_lines`/`missing_lines`) identifico las **2
líneas** sin cubrir, ambas en el mismo fichero:

- `scripts/verificar_sql_ecosistema.py:40` — `sys.path.insert(0,
  str(RAIZ_PROYECTO))`, dentro del guardado `if ... not in sys.path:` que
  hace el script ejecutable como standalone.
- `scripts/verificar_sql_ecosistema.py:241` — `raise SystemExit(main())`
  bajo `if __name__ == "__main__":`.

Ninguna de las dos toca lógica de seguridad: son boilerplate de arranque de
script, no ejecutable al importar el módulo desde los tests. Los tres
ficheros de seguridad que F-003 realmente modifica o crea
(`database_reference_guard.py`, `sql_write_guard.py`, `sql_query_guard.py`)
están al 100 % dentro del alcance medido — el hueco entero cae en el script
de verificación del ecosistema, que ya tiene su propia suite
(`test_verificar_sql_ecosistema.py`, 20 casos) cubriendo su lógica real.

Aceptable. Observación menor, no bloqueante: por consistencia con el propio
repo (`harness/cobertura.py:245` usa `# pragma: no cover` para el mismo
patrón `if __name__ == "__main__":`), convendría el mismo pragma aquí.
**[x] Cobertura.**

## N/A de este encargo

- Mutación, RM1-RM6, «campaña tardó lo que tenía que tardar», SHA de HEAD
  medido: **fuera de ámbito por instrucción explícita del encargo** (hay una
  medición de la campaña en curso en paralelo). No se juzgan aquí.

## Comunicación

APROBADO (C4bis RED+cobertura) -> progress/review_F-003_c4bis_red_cobertura.md
