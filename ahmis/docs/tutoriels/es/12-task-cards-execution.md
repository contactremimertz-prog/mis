# 12. Ejecutar una task card

**Cuenta: `meca`**

Situación de partida: en F-HDMD (H145), la task card **Visite 100 h / 12 mois** está en curso. 3 pasos de 6 están firmados, se ha retirado una llave dinamométrica y una solicitud de tapón magnético espera al almacén.

## 1. Abrir la task card

Menú **Task cards** → filtro Estado «En curso» → **Visite 100 h / 12 mois** (WP «Visite 100 h + boroscopie moteurs»).

## 2. Firmar los pasos restantes

Para los pasos 4, 5 y 6:

1. Introduzca un valor medido si es necesario (p. ej., `Niveau OK`); marque N/A si el paso no se aplica.
2. Introduzca su contraseña → **Firmar**.

Cada paso firmado muestra su nombre, su visado (`LM1`) y la marca de tiempo.

**Pruebe** con una contraseña incorrecta: «Contraseña o código de firma incorrecto: firma rechazada».

## 3. Intentar firmar los trabajos

Informe `Visite effectuée, RAS`, tiempo empleado `7.5`, contraseña → **Firmar los trabajos**.

AHMIS **rechaza**: «Todavía hay solicitudes de piezas pendientes». Es lo previsto: no se cierra una tarea con una pieza pendiente.

## 4. Desbloquear

1. **Pieza**: el almacenero entrega la solicitud (tutorial 18). Si no la necesita, solicite su anulación al almacén.
2. **Herramientas**: en el marco Herramientas, haga clic en **Devolver** en `CLE-DYN-01`. Mientras haya una herramienta retirada, la firma también está bloqueada.

## 5. Firmar los trabajos

Repita el paso 3. La task card pasa a **Cerrada**, porque esta tarea no requiere inspección independiente.

## Qué hace AHMIS al cerrar

- Registra la **realización** de la tarea con los contadores actuales de la aeronave.
- **Recalcula** el vencimiento: la revisión de 100 h de F-HDMD vuelve a «OK», con 100 FH por delante (compruébelo en **Vencimientos**).
- Si la tarea controla una AD, actualiza el estado de la directiva (tutorial 8).
- Si la task card rectifica un defecto, cierra el defecto (tutorial 15).

## Comprobaciones automáticas en la firma

| Regla | Mensaje |
|---|---|
| Ficha de personal vinculada a la cuenta | «Su cuenta no está vinculada a ninguna ficha de personal» |
| Autorización válida en el tipo | «… no tiene autorización válida en el tipo H145» |
| Todos los pasos firmados | «3 paso(s) sin firmar» |
| Informe cumplimentado | «El informe de los trabajos es obligatorio» |
| Ninguna solicitud de pieza pendiente | «Todavía hay solicitudes de piezas pendientes» |
| Herramientas devueltas | «Herramientas no devueltas: CLE-DYN-01» |

## Hallazgo durante la revisión

El marco **Notificar un hallazgo** crea con un solo clic un **defecto** y una **task card de rectificación** en el mismo WP, vinculada a la task card de origen. Pruebe: `Légère corrosion sur ferrure de capot BTP`.

## Aplazar o anular

- **Aplazar** (motivo obligatorio): la task card se aplaza y el aplazamiento aparece en el CRS.
- **Anular**: solo si no hay ningún paso firmado.
