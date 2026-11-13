# 8. Directivas de aeronavegabilidad (AD) y boletines de servicio (SB)

**Cuenta: `camo`**

## El ciclo de vida de una directiva

1. **Registrar** la directiva: número, emisor, fecha de entrada en vigor, tipos y/o P/N afectados.
2. AHMIS crea automáticamente un estado **«Por evaluar»** para cada aeronave potencialmente afectada (mismo tipo, o P/N afectado instalado).
3. La CAMO **evalúa** cada aeronave:
    - **No aplicable**: la justificación es obligatoria;
    - **Aplicable – por realizar**: se necesita una **tarea de seguimiento**;
    - **Incorporada**: la fecha de cumplimiento es obligatoria.
4. La tarea de seguimiento aparece en los vencimientos. El plazo se cuenta **a partir de la fecha de entrada en vigor**.
5. Al cerrar la task card, el estado pasa a **Incorporada** (directiva única) o **Repetitiva en curso**.

## Ejercicio 1: evaluar la AD del ATR

1. Menú **AD / SB** → `DEMO-AD-2026-0177` (ATR 72, herrajes de flap).
2. Línea F-HDMF: estado **Por evaluar** → **Evaluar**.
3. Estado «Aplicable – por realizar», justificación `MSN 1801 dans la plage d'applicabilité` → **Guardar**.
4. Botón **Crear la tarea de seguimiento (ATR72-600)**: la referencia, el título y la acción requerida aparecen rellenados.
5. Indique el **umbral ciclos** `3000` (plazo desde la entrada en vigor) y la carga `4`, y guarde.

**Resultado**: en **Vencimientos**, F-HDMF tiene una nueva línea con un límite de ciclos igual a los ciclos en la entrada en vigor + 3 000.

## Ejercicio 2: declarar una no aplicabilidad

1. `DEMO-SB-145-24-010` (SB opcional H145) → F-HDMD → **Evaluar**.
2. Elija «No aplicable» **sin** justificación → **Guardar**: rechazado.
3. Añada `SB optionnel non retenu par l'exploitant – décision CAMO du jj/mm` → **Guardar**.

## Ejercicio 3: controlar una AD repetitiva

`DEMO-AD-2026-0101` (barras de suspensión BTP NH90) se controla mediante una tarea con un umbral de 50 FH y un intervalo de 110 FH:

- en **F-HDMA**, se ha realizado: estado «Repetitiva en curso», próximo vencimiento 110 FH después;
- en **F-HDMB**, nunca se ha realizado: **Vencido**. El tutorial 24 la trata.

## Vista de conjunto

Botón **Estado por aeronave** en la lista AD/SB: todas las evaluaciones, con filtros por estado y por aeronave. Es el documento base de la revisión de aeronavegabilidad.
