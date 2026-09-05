<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004 --workers 8` el 2026-09-05 23:22.

## Alcance

Origen del diff: **rama** (`f8bb8c69bdeb472d7f2fd68033f2fdfa722276f0` .. `feature/F-004-endpoint-concepto-grafico`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/attach_concepto_grafico_use_case.py` | 571 |
| `application/use_cases/concepto_grafico_statements.py` | 340 |
| `config/settings.py` | 81 |
| `domain/models/concepto_grafico_models.py` | 165 |
| `function_app.py` | 66 |
| `infrastructure/security/document_write_guard.py` | 160 |
| **Total** | **1383** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 167 |
| Mutantes evaluados | 167 |
| Muertos | 131 |
| Supervivientes | 36 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 772.1 s |
| SHA de HEAD medido | `d4e8535baef7707927995b266b7d3b356b33429e` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_0` | 91.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_1` | 89.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_2` | 88.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_3` | 88.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_4` | 91.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_5` | 90.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_6` | 95.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_oirg7a3j/wk_7` | 89.4 |
| Media por mutante evaluado (s) | 4.6 |
| Timeout efectivo por mutante (s) | 191 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/attach_concepto_grafico_use_case.py:93` [aritmetico]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() + arranque) * 1000, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `application/use_cases/attach_concepto_grafico_use_case.py:93` [aritmetico]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) // 1000, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `application/use_cases/attach_concepto_grafico_use_case.py:93` [entero]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1001, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `application/use_cases/attach_concepto_grafico_use_case.py:93` [entero]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `application/use_cases/attach_concepto_grafico_use_case.py:94` [booleano]

- Original: `logger.info(json.dumps(traza, ensure_ascii=False, default=str))`
- Mutado:   `logger.info(json.dumps(traza, ensure_ascii=True, default=str))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `application/use_cases/attach_concepto_grafico_use_case.py:251` [entero]

- Original: `ide, tip, emp, cod, res = filas[0][:5]`
- Mutado:   `ide, tip, emp, cod, res = filas[0][:6]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `application/use_cases/attach_concepto_grafico_use_case.py:273` [logico]

- Original: `if fila is not None and not (fila[4] or "").strip():`
- Mutado:   `if fila is not None or not (fila[4] or "").strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `application/use_cases/attach_concepto_grafico_use_case.py:273` [logico]

- Original: `if fila is not None and not (fila[4] or "").strip():`
- Mutado:   `if fila is not None and not (fila[4] and "").strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `application/use_cases/attach_concepto_grafico_use_case.py:307` [entero]

- Original: `ide_negocio, cod_existente, ide_enlace, binario = fila[:4]`
- Mutado:   `ide_negocio, cod_existente, ide_enlace, binario = fila[:5]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `application/use_cases/attach_concepto_grafico_use_case.py:387` [not]

- Original: `dry_run=not request.commit,`
- Mutado:   `dry_run=request.commit,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `application/use_cases/attach_concepto_grafico_use_case.py:393` [entero]

- Original: `request, documento, cod_existente, concepto.emp, 0,`
- Mutado:   `request, documento, cod_existente, concepto.emp, 1,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `application/use_cases/attach_concepto_grafico_use_case.py:540` [booleano]

- Original: `idempotente=False,`
- Mutado:   `idempotente=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `application/use_cases/concepto_grafico_statements.py:62` [aritmetico]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio - 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 2, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 2, 1) if mes == 12 else date(anio, mes + 1, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 1, 2) if mes == 12 else date(anio, mes + 1, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 1, 1) if mes == 13 else date(anio, mes + 1, 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `application/use_cases/concepto_grafico_statements.py:64` [entero]

- Original: `ultimo = primero_del_siguiente - timedelta(days=1)`
- Mutado:   `ultimo = primero_del_siguiente - timedelta(days=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `application/use_cases/concepto_grafico_statements.py:65` [entero]

- Original: `return ultimo - timedelta(days=(ultimo.weekday() + 1) % 7)`
- Mutado:   `return ultimo - timedelta(days=(ultimo.weekday() + 1) % 8)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `domain/models/concepto_grafico_models.py:68` [entero]

- Original: `database: str = Field(..., min_length=1)          # base de NEGOCIO (ruesma)`
- Mutado:   `database: str = Field(..., min_length=2)          # base de NEGOCIO (ruesma)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `domain/models/concepto_grafico_models.py:69` [entero]

- Original: `conide: int = Field(..., ge=1)                    # con.ide del concepto`
- Mutado:   `conide: int = Field(..., ge=2)                    # con.ide del concepto`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `domain/models/concepto_grafico_models.py:70` [entero]

- Original: `contip: int = Field(..., ge=1)                    # con.tip esperado (se coteja)`
- Mutado:   `contip: int = Field(..., ge=2)                    # con.tip esperado (se coteja)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `domain/models/concepto_grafico_models.py:71` [entero]

- Original: `gratipide: int = Field(..., ge=1)                 # clase de grafico (auxgra.ide)`
- Mutado:   `gratipide: int = Field(..., ge=2)                 # clase de grafico (auxgra.ide)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `domain/models/concepto_grafico_models.py:72` [entero]

- Original: `res: str = Field(..., min_length=1, max_length=48)`
- Mutado:   `res: str = Field(..., min_length=2, max_length=48)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `domain/models/concepto_grafico_models.py:73` [entero]

- Original: `nom: str = Field(..., min_length=1, max_length=255)`
- Mutado:   `nom: str = Field(..., min_length=2, max_length=255)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `domain/models/concepto_grafico_models.py:76` [entero]

- Original: `usu: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `usu: str = Field(..., min_length=2, max_length=24)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `domain/models/concepto_grafico_models.py:77` [entero]

- Original: `contenido_base64: str = Field(..., min_length=4)`
- Mutado:   `contenido_base64: str = Field(..., min_length=5)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `domain/models/concepto_grafico_models.py:96` [logico]

- Original: `if not limpio or len(limpio) % 4 != 0 or not _BASE64_RE.fullmatch(limpio):`
- Mutado:   `if not limpio and len(limpio) % 4 != 0 or not _BASE64_RE.fullmatch(limpio):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `function_app.py:275` [entero]

- Original: `settings, repository = deps[0], deps[1]`
- Mutado:   `settings, repository = deps[1], deps[1]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `function_app.py:275` [entero]

- Original: `settings, repository = deps[0], deps[1]`
- Mutado:   `settings, repository = deps[0], deps[2]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `infrastructure/security/document_write_guard.py:36` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 5 / 3) + 4`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 4 / 4) + 4`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 4 / 3) + 5`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `infrastructure/security/document_write_guard.py:65` [comparacion]

- Original: `if len(contenido_base64) > tope_base64:`
- Mutado:   `if len(contenido_base64) >= tope_base64:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `infrastructure/security/document_write_guard.py:92` [logico]

- Original: `f"({', '.join(firmas_permitidas) or '(ninguna)'}).",`
- Mutado:   `f"({', '.join(firmas_permitidas) and '(ninguna)'}).",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

