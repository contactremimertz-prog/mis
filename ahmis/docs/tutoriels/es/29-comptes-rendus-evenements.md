# 29. Notificaciones de sucesos (Reglamento 376/2014)

**Cuentas: `meca`, `qualite`, `camo`**

Todo suceso que comprometa o pueda comprometer la seguridad debe notificarse a la autoridad **en un plazo de 72 horas** desde que la organización tuvo conocimiento de él (Reglamento (UE) n.º 376/2014, 145.A.60, CAMO.A.160). Un análisis de seguimiento se transmite **en un plazo de 30 días**. Se informa al titular del diseño si el estado de la aeronave o de un componente está en causa.

AHMIS aplica la **cultura justa**: todo el personal puede notificar, pero solo calidad y la CAMO ven el conjunto de las notificaciones. La identidad de un notificante confidencial solo es visible para el responsable de calidad.

## 1. Notificar (todo el personal)

1. Cuenta `meca` → menú **Notificaciones de sucesos** → **+ Crear**. Otro acceso: botón **Notificar un suceso** en un defecto o una task card, que rellena previamente el formulario.
2. Título `Lampe torche retrouvée en zone moteur`, categoría «Objeto extraño (FOD) / objeto olvidado», fase «En mantenimiento», aeronave `F-HDMD`.
3. Fechas del suceso y de conocimiento: ahora. Descripción factual, medidas inmediatas `Zone inspectée, inventaire outillage`. Marque **notificación confidencial** → **Guardar**.

**Resultado**: la notificación `OCC-AAAA-NNNN` está en **Borrador**, con el plazo de 72 h mostrado. El mecánico solo ve sus propias notificaciones.

## 2. Controlar los plazos (calidad)

Cuenta `qualite` → **panel de control**: aviso «Notificaciones de sucesos: N abierta(s), de las cuales N por notificar». Pasa a rojo si hay un incumplimiento de plazo. La demo contiene:

| N.º | Situación |
|---|---|
| Vibraciones en el pedal (F-HDMD) | Borrador: quedan unas 20 h de 72 |
| Pasador de freno de tuerca no montado (F-HDMB) | Notificado hace 40 días: **seguimiento a 30 días con retraso** |
| Pieza sin certificado de aptitud | Cerrado |

En la notificación confidencial, el notificante (Sophie LAMBERT) es visible para `qualite`, pero se muestra como «Confidencial» para `camo`.

## 3. Notificar, hacer el seguimiento, cerrar

Cuenta `qualite` → abra la notificación → **Tratar**:

1. **Notificación**: estado «Notificado a la autoridad», autoridad `DSAC / ECCAIRS 2`, referencia ECCAIRS, fecha de notificación. Pasadas las 72 h, el **motivo del retraso** es obligatorio. Marque «titular del diseño informado» si es necesario.
2. **Seguimiento**: estado «Seguimiento enviado», análisis (causas, factores humanos), fecha de transmisión.
3. **Cierre**: acciones correctoras y fecha de cierre.

Un suceso que no figure en la lista del Reglamento 2015/1018 puede «Clasificarse como no notificable», con una justificación. Un incidente grave o un accidente no puede serlo.

## 4. Conservación

Las notificaciones cerradas se conservan al menos 36 meses (tutorial 30). No se incluyen en los expedientes de transferencia de aeronaves.
