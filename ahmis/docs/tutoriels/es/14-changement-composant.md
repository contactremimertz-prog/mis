# 14. Cambiar un componente (desmontaje / montaje)

**Cuentas: `planif`, luego `b1`**

Situación de partida: en F-HDMD (H145), el defecto «Vibrations anormales ressenties au palonnier» tiene una task card de rectificación. El almacén ya ha **reservado** para ella una caja Fenestron revisada, `DEMO-145FEN-01` S/N `DEMO-F1459` (solicitud AOG entregada).

## 1. Iniciar la task card

1. Cuenta `b1` → menú **Task cards** → **Rectification DEF-… : Vibrations anormales…**.
2. **Iniciar la task card**.

## 2. Probar una pieza no conforme

En el marco **Cambio de componente**:

- Componente desmontado: `DEMO-145FEN-01 S/N DEMO-F1451` (posición BTA)
- Motivo: `Vibrations – dépose pour expertise`
- Componente montado: `DEMO-350TGB-01 S/N DEMO-T3599` (una BTA de **NH90**)
- Contraseña → **Registrar el cambio**

AHMIS rechaza: «Montaje rechazado: P/N no aplicable al tipo H145». **No se ha modificado nada**: la caja original sigue en su sitio.

## 3. Cambio conforme

Repita con componente montado: `DEMO-145FEN-01 S/N DEMO-F1459`, la pieza reservada. La posición queda vacía: AHMIS toma la del componente desmontado.

**Resultado**:

- **Configuración** de F-HDMD: en la posición BTA, la caja S/N DEMO-F1459 está instalada, con su TSO y su TBO restante.
- **Ficha de la caja desmontada** (DEMO-F1451): estado «No utilizable (U/S)», motivo del desmontaje y, en su trazabilidad «back-to-birth», las fechas y contadores de la aeronave en el montaje **y** en el desmontaje, con la task card.
- **Ficha de la caja montada**: un nuevo montaje, con los contadores en el montaje.
- Una firma electrónica describe el movimiento.

## 4. Cerrar

Informe `Remplacement de la boîte Fenestron, essais vibratoires conformes`, tiempo empleado `5` → **Firmar los trabajos**.

El defecto pasa a **Rectificado**, con la acción correctora tomada del informe.

## Comprobaciones realizadas en cada montaje

| Comprobación | Ejemplo de rechazo |
|---|---|
| Estado de la pieza | Pieza en cuarentena, U/S o reservada para otra task card |
| Certificado de aptitud aceptado | Pieza sin EASA Form 1 / 8130-3 |
| Potencial restante | Límite de vida o TBO alcanzado |
| Aplicabilidad | P/N no aplicable al tipo |
| Posición libre | Posición ya ocupada por el mismo P/N |

La pieza desmontada puede salir como «U/S» (avería), «Cuarentena» (peritaje) o «Utilizable» (desmontaje de conveniencia). Conserva todos sus contadores.
