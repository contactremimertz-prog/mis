# 26. Registro de modificaciones y reparaciones

**Cuentas: `camo`, `b1`**

M.A.305 exige conocer en todo momento el estado de las modificaciones y reparaciones de cada aeronave, con su base de aprobación y las instrucciones de aeronavegabilidad continuada (ICA) que se derivan de ellas.

## 1. Registrar una modificación

1. Cuenta `camo` → menú **Modificaciones y reparaciones** → **+ Crear**.
2. Aeronave `F-HDMA`, naturaleza «Modificación», clasificación «Menor», título `Installation d'un kit caméra externe`, ATA `25`.
3. Base de aprobación «Aprobación DOA / Part-21J», referencia `DOA-MIN-2026-118 (DEMO)`.
4. Estado «Incorporada», incorporada el: fecha del día, ICA: `Supplément MSM 25-10 (DEMO)`. Marque «modifica la masa y el centrado» → **Guardar**.

**Resultado**: la modificación recibe un número `MOD-AAAA-NNNN`. Su ficha señala dos **puntos pendientes de cierre**: «ICA aún no integradas en el programa de mantenimiento» y «ficha de pesada / centrado por actualizar». También aparecen en los **Vencimientos** de F-HDMA, naturaleza «Modificación / reparación».

## 2. Cerrar el seguimiento

1. **Modificar** la modificación: marque «ICA integradas en el programa de mantenimiento» y «acciones de seguimiento realizadas».
2. **Guardar**: los puntos pendientes desaparecen de los vencimientos.

Para integrar las ICA, cree la tarea correspondiente en el programa (tutorial 6) y, a continuación, registre la nueva revisión en la revisión del programa (tutorial 27).

## 3. Desde una task card

Cuenta `b1` → una task card → enlace **+ Registrar una modificación o reparación realizada en esta task card**. El formulario aparece rellenado (aeronave, componente, título, ATA, fecha) y la task card queda vinculada.

## 4. Comprobaciones

| Regla | Mensaje |
|---|---|
| Mayor: aprobación EASA, STC o DOA | «Una modificación o reparación mayor exige una aprobación EASA, un STC o una aprobación DOA.» |
| Cambio estándar: CS-STAN | «Un cambio estándar debe referirse a CS-STAN.» |
| Incorporada: fecha obligatoria | «Fecha de incorporación obligatoria.» |
| Incorporada: ICA o «sin ICA asociadas» | «Indique las ICA, o marque «sin ICA asociadas».» |
| Retirada / anulada: motivo | «Motivo obligatorio.» |

Una modificación no se elimina: pásela al estado «Retirada / anulada» con un motivo.
