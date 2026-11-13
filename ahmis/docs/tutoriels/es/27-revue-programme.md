# 27. Revisión anual del programa de mantenimiento

**Cuenta: `camo`**

M.A.302(g) exige revisar periódicamente cada programa de mantenimiento (al menos una vez al año) y enmendarlo si es necesario: eficacia (fiabilidad, defectos repetitivos), nuevas instrucciones (revisiones MSM/MPD, AD, SB, ICA de las modificaciones).

## 1. Estado de las revisiones

El **panel de control** muestra un aviso «Revisión del programa de mantenimiento» para cada tipo explotado cuya revisión falta, está vencida o debe hacerse en los próximos 30 días. Menú **Revisión del programa**:

| Tipo | Situación de la demo |
|---|---|
| ATR72-600 | Ninguna revisión registrada |
| Super Puma | Revisión vencida (última revisión hace 13 meses) |
| H135 | Revisión por hacer en los próximos 30 días |
| NH90, H145 | Al día (NH90 enmendado a «DEMO rév. 4») |

La ficha del **tipo de aeronave** (Flota → Tipos y configuración) muestra también el estado y las últimas revisiones.

## 2. Registrar una revisión sin cambios

1. Línea **Super Puma** → **Nueva revisión**. El programa y la revisión examinada se toman de la revisión anterior.
2. Realizada por `Julien MOREAU (CAMO)`. Marque **las dos** casillas de examen (fiabilidad y nuevas instrucciones).
3. Hallazgos `Aucun défaut répétitif, pas de nouvelle révision MSM`; resultado «Programa confirmado sin cambios» → **Guardar**.

**Resultado**: Super Puma pasa a «Al día», próxima revisión dentro de 12 meses.

## 3. Registrar una enmienda

1. Línea **ATR72-600** → **Nueva revisión**: programa `AMP-ATR72-DEMO`, revisión examinada `DEMO rév. 3`.
2. Resultado «Programa enmendado», nueva revisión `DEMO rév. 4`, cambios `Ajout des ICA de la modification MOD-...`.
3. Modo de aprobación «Aprobación indirecta (procedimiento CAME/CAE)», referencia `PAI-2026-020`, fecha → **Guardar**.

**Resultado**: todas las tareas activas del tipo pasan a «revisión AMP: DEMO rév. 4».

## 4. Comprobaciones

- Revisión incompleta (fiabilidad o instrucciones no examinadas): rechazada.
- Enmienda sin nueva revisión, con una revisión idéntica, sin descripción de los cambios o sin aprobación: rechazada.
- Próxima revisión fijada más allá de 12 meses: rechazada. La periodicidad se ajusta con `AHMIS_AMP_REVIEW_MONTHS`.
- Revisión con fecha futura: rechazada.
