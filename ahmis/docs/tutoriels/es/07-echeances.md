# 7. Los vencimientos (límites)

**Cuenta: `camo`**

Menú **Vencimientos**: la lista consolidada de todo lo que vence en la flota.

## Las naturalezas de vencimientos

| Naturaleza | Origen |
|---|---|
| Tarea | Programa de mantenimiento (célula) |
| Tarea de componente | Tarea controlada sobre los contadores de un componente |
| LLP / TBO | Límites de los componentes instalados |
| ARC | Caducidad de la revisión de aeronavegabilidad |
| Defecto aplazado | Límite MEL/CDL de un defecto aplazado |
| Directiva | AD/SB por evaluar, o aplicable sin tarea de seguimiento |

## Los estados

| Estado | Significado |
|---|---|
| **Vencido** (rojo) | Límite superado más allá de la tolerancia |
| **En tolerancia** | Límite superado pero dentro de la tolerancia autorizada |
| **Por planificar** (naranja) | Fecha prevista dentro de los 30 días (parámetro `AHMIS_ALERT_DAYS`) |
| **OK** | Posterior |

## Leer una línea

- **Última realización**: fecha y contadores.
- **Límite** FH / ciclos / fecha.
- **Restante** FH / ciclos (negativo en rojo).
- **Fecha prevista**: la más próxima de las fechas obtenidas para cada criterio, proyectando la utilización prevista.
- **Criterio**: el que activa el vencimiento (FH, ciclos o calendario).

## Ejercicios

1. Filtro **Aeronave = F-HDMB**.
    - `DEMO-AD-2026-0101`: **Vencido**, −27,6 FH. La AD entró en vigor hace 200 días con un plazo de 50 FH, y nunca se ha realizado.
    - `N90-05-100`: **En tolerancia** (−6 FH sobre una tolerancia de 10 FH).
    - LLP cubo del rotor: **Por planificar**.
2. Filtro **Naturaleza = LLP** y, a continuación, **Estado = Por planificar**.
3. Filtro **Vence en = 90 días** y, a continuación, **Exportación CSV**: el archivo se abre en Excel (separador «;»).

## Planificar desde los vencimientos

**Cuenta: `planif`** (la CAMO identifica las necesidades; el planificador las sitúa en un paquete de trabajo). Cuando se selecciona una aeronave, aparecen casillas de verificación:

1. Filtro **F-HDMB**.
2. Marque `DEMO-AD-2026-0101`, `N90-05-100` y la LLP cubo del rotor.
3. Paquete de trabajo: elija **WP … Visite 100 h** (ya planificado dentro de 5 días).
4. **Crear las task cards**.

**Resultado**: accederá al paquete de trabajo con 3 task cards generadas: los pasos de la tarea y una task card de «desmontaje/montaje» para la LLP. La continuación está en el tutorial 11.
