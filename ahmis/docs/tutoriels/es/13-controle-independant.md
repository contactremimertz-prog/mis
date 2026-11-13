# 13. La inspección independiente (tareas críticas)

**Cuentas: `b1`, luego `b2`**

Algunas tareas (mandos de vuelo, fijaciones críticas, inspecciones boroscópicas…) exigen una **segunda firma**, de una persona **distinta** del ejecutante y titular de una **autorización certificadora** en el tipo.

Situación de partida: en F-HDMD, la task card **Contrôle boroscopique moteurs Arriel 2E** ha sido ejecutada por Claire DUBOIS (`b1`). Está en el estado «Ejecutada – pendiente de inspección».

## 1. El ejecutante no puede inspeccionarse a sí mismo

1. Inicie sesión con `b1` y abra la task card (menú **Task cards**, filtro «Ejecutada – pendiente de inspección»).
2. El marco Ejecución indica: «Usted ha ejecutado estos trabajos: la inspección debe firmarla otra persona». No se ofrece ningún botón de inspección.

## 2. Un mecánico no certificador no puede inspeccionar

Con `meca`, el formulario de inspección no aparece: su autorización de «mecánico no certificador» no permite la inspección.

## 3. Inspección por otra persona certificadora

1. Inicie sesión con `b2` (Karim BENALI, B2 certificador H145).
2. Abra la task card → marco **Inspección independiente**: observaciones `Images boroscopiques revues, conforme`, contraseña → **Firmar la inspección**.

**Resultado**:

- la task card queda **Cerrada**;
- las dos firmas (ejecución e inspección) aparecen con su insignia «✓ íntegra»;
- el vencimiento de la tarea de componente `145-72-500` del motor MOT 1 se recalcula con los contadores **del motor**.

## Hacer una tarea «crítica»

En el programa de mantenimiento, marque «inspección independiente requerida» en la tarea (tutorial 6). Para una task card fuera de programa, marque la misma casilla al crearla.
