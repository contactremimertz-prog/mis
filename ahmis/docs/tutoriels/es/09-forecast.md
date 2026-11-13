# 9. La previsión (previsión de mantenimiento)

**Cuenta: `camo` o `planif`**

Menú **Previsión**.

## Principio

La previsión **despliega** todos los vencimientos sobre un horizonte dado:

- una tarea repetitiva genera varias ocurrencias (p. ej., la lubricación de 50 FH de un H145 a 2 FH/día se repite cada 25 días);
- LLP, TBO, ARC y defectos aplazados aparecen una sola vez;
- los elementos ya vencidos se sitúan en la fecha de hoy, con la insignia «vencido».

## Lectura

- Indicadores: número de vencimientos, **carga total en horas-hombre**, número de desmontajes en límite.
- **Carga mensual**: un histograma por mes, con el desglose por aeronave.
- El detalle de cada mes se abre al hacer clic: ocurrencias, criterio, carga, **piezas previstas** y necesidad de piezas del mes (procedente de las «piezas requeridas» de las tareas).

## Ejercicios

1. Horizonte `365` días, toda la flota → **Calcular**. Localice el mes de la **revisión C del ATR** (600 h.h): un pico de carga que conviene anticipar.
2. Aeronave `F-HDMD`, horizonte `180` días: la carga propia del H145.
3. **Simulación**: toda la flota, utilización `130` % → **Calcular**. Los vencimientos en horas y en ciclos se adelantan; los de calendario no se mueven. Compare con el 100 %.
4. **Exportación CSV**: la lista completa de ocurrencias, para una hoja de cálculo o una herramienta de planificación.

> La previsión es una proyección basada en la «utilización prevista» de cada aeronave. Mantenga estos valores actualizados (ficha de la aeronave) para obtener una previsión fiable.
