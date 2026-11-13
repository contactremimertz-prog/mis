# 19. Cuarentena, piezas sospechosas y caducidad

**Cuenta: `magasin`**

Menú **Cuarentena**: todas las piezas bloqueadas.

## Qué contiene la demo

| Pieza | Situación |
|---|---|
| Arrancador-generador `DEMO-G1666` | **Pieza sospechosa (SUP)**: placa de identificación no conforme, certificado rechazado |
| Motor RTM322 `DEMO-E21099` | **U/S**: desmontado por exceso de temperatura |
| Lote de aceite `LOT-OIL-2502` (almacén de línea) | Utilizable pero **caducado**: figura en el recuadro naranja |

## 1. Intentar liberar una pieza sospechosa

1. Abra `DEMO-G1666` → marco «Cambiar el estado»: nuevo estado «En almacén – utilizable», ubicación `MAG-PRINC`, motivo `Test` → **Cambiar el estado**.
2. AHMIS rechaza: «No es posible volver a declarar la pieza utilizable en almacén sin un certificado de aptitud aceptado».

Una pieza sospechosa permanece en cuarentena hasta la decisión de calidad. Si la decisión es la baja, cambie el estado a **Dado de baja** con el motivo `SUP confirmée – déclaration à l'autorité`. La pieza permanece en AHMIS por trazabilidad, pero ya no podrá utilizarse nunca más.

## 2. Enviar un motor a revisión general

`DEMO-E21099` → estado «En reparación / revisión general», motivo `Envoyé à l'atelier moteur, BL 4471`. A su regreso, recíbalo con su nuevo Form 1 (tutorial 17).

## 3. Tratar un lote caducado

En el recuadro naranja, haga clic en `LOT-OIL-2502` → estado «Caducado», motivo `Date dépassée` → **Guardar**. El lote ya no se propone en la entrega, lo que ya era así: AHMIS rechaza toda entrega de un lote cuya fecha ha vencido.

## 4. Poner una pieza en cuarentena

En cualquier componente en almacén, elija el estado «Cuarentena»: si no se indica ubicación, se coloca automáticamente en `QUAR`.
