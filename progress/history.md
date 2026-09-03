<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-002 · Spike: viabilidad de escribir en la base documental `ruesma_rep`

**Cerrada el 2026-09-03.** Rigor `critico`. Sin rama de feature: se ejecutó
como exploración de solo lectura durante la instalación del arnés, a petición
directa del humano.

**Pregunta:** ¿se puede escribir en `ruesma_rep`, y con qué garantías?

**Respuesta: sí, y sin ningún trámite previo.**

- `ruesma_rep` es `READ_WRITE`, `ONLINE`, **sin replicación** ni grupos de
  disponibilidad, en la **misma instancia** que `ruesma` y creada tres minutos
  después que ella. No es una réplica: el sufijo `_rep` es «repositorio».
- El ERP le escribe **entre 94 y 248 filas por día laborable**. Una réplica de
  solo lectura no puede recibir eso.
- **`user_rw` ya tiene permiso de `INSERT`** sobre su única tabla, `dbo.gra`.
  No hace falta `CREATE USER` ni `GRANT`.
- Tiene **una sola tabla**, con índice único por `(emp, cod)` —idempotencia
  gratis— y el binario en columna `image`.
- El motor es **SQL Server 2012**: `HASHBYTES` no admite un PDF completo, así
  que el `sha256` va calculado en Python.

**Método:** solo lecturas por `sql/read`, más tres `INSERT ... SELECT ...
WHERE 1 = 0` por `sql/write` (autorizados expresamente por el humano) que no
pueden insertar ninguna fila. Con control negativo: el mismo patrón contra
`master.dbo.spt_monitor` devuelve `229 · permiso INSERT denegado`, lo que
demuestra que el motor comprueba permisos aunque no inserte. **Ninguna fila
escrita en Sigrid.**

**Hallazgo colateral, y es el que más importa:** `SqlWriteGuard` valida el
campo `database` de la petición pero **no las bases nombradas dentro del SQL**.
La política «`ruesma_rep` no se escribe» no está aplicada de verdad. De ahí
sale **F-003**, que va antes que el endpoint.

**Informe:** [`progress/explore_ruesma_rep.md`](explore_ruesma_rep.md).
**Consecuencia:** F-003 (cerrar el guardia) y F-004 (endpoint de dominio),
decidido por el humano el 2026-09-03 frente a la alternativa de abrir
`ALLOWED_WRITE_DATABASES`.

---
