# 6. El programa de mantenimiento (tareas)

**Cuenta: `camo`**

## Consultar

Menú **Programa de mantenimiento**: 33 tareas de demostración. Filtre por tipo (`H145`) o por origen (MSM/MPD, ALS, AD, SB, operador).

Abra **145-05-100 Visite 100 h / 12 mois**:

- **Intervalo** `100 FH / 1 año`: el **primer criterio alcanzado** activa el vencimiento.
- **Tolerancia** `10 FH / 30 d`: más allá del límite pero dentro de la tolerancia, el estado es «En tolerancia» (naranja oscuro). Más allá de la tolerancia, es «Vencido» (rojo).
- **Pasos**: cada línea se convierte en un paso que debe firmarse en la task card.
- **Piezas requeridas**: alimentan la previsión (necesidades mensuales de piezas).
- **Situación por aeronave**: última realización, límites, restantes, fecha prevista para cada H145.

## Crear una tarea

1. **+ Crear** (o desde la ficha del tipo NH90: «Añadir una tarea»).
2. Ejemplo:
    - Referencia `N90-25-180`, título `Contrôle du kit de flottaison`, tipo NH90
    - Naturaleza: Comprobación funcional; ATA `25`
    - Intervalo: `180` días; tolerancia: `15` días
    - Carga: `2` h.h; cualificación B1
    - Pasos: `Déplier le kit` / `Contrôler la pression des bouteilles` / `Replier et plomber` (uno por línea)
3. **Guardar** y, a continuación, añada una pieza requerida (p. ej., `DEMO-ORING-12` × 2).

**Resultado**: la tarea se aplica inmediatamente a todos los NH90 (F-HDMA, F-HDMB). Deje «efectividad» vacío para todas las aeronaves del tipo, o marque matrículas concretas.

## Umbral (primer vencimiento)

Un umbral distinto del intervalo se indica en «umbral FH/ciclos/días». Ejemplo: primera inspección a 1 200 FH y, después, cada 500 FH.

## Tarea controlada sobre un componente

Rellenar «P/N del componente» vincula la tarea a los contadores **del componente** y no a los de la célula. Véase **N90-72-500** (boroscopia RTM322): el vencimiento sigue al motor, aunque cambie de helicóptero.

## Tarea con inspección independiente

Marque «inspección independiente requerida» para las tareas críticas (mandos de vuelo, fijaciones de la BTP…). La task card exigirá entonces una segunda firma de otra persona certificadora (tutorial 13).

## Revisiones del programa

Cada modificación queda registrada: botón **Historial de revisiones** en la ficha de la tarea. Rellene también «revisión AMP». Una tarea no se elimina: desmarque «activa».
