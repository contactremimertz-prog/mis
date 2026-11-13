# 25. Tolerancias: realización en tolerancia, no acumulativa

**Cuenta: `camo`**

Una tolerancia permite realizar una tarea algo después de su vencimiento (por ejemplo, +10 FH o +30 días en una revisión de 100 h). **No** es acumulativa: cuando una tarea se realiza en tolerancia, el siguiente vencimiento se cuenta desde el **límite teórico**, no desde la fecha o las horas reales. Por tanto, nunca se «ganan» horas utilizando la tolerancia.

## 1. Situación de partida

Menú **Vencimientos** → aeronave **F-HDMB**: la tarea `N90-05-100 Visite 100 h / 12 mois` está **En tolerancia**. Límite teórico `3 881,6 FH`, contador actual `3 887,6 FH`, es decir, 6 FH de exceso sobre una tolerancia de 10 FH.

## 2. Registrar la realización

1. Haga clic en `N90-05-100` → **Registrar una realización (historial)**.
2. Aeronave `F-HDMB`, fecha del día, FH `3887.6`, ciclos `11623`, origen «Organización externa», referencia `CRS-EXT-001`, certificado por `Atelier externe` → **Guardar**.

**Resultado**:

- en la ficha de la tarea, la realización lleva la insignia **en tolerancia**;
- en los vencimientos, el próximo límite es **3 981,6 FH** (3 881,6 + 100), y no 3 987,6. La nota «Realizada en tolerancia: próximo vencimiento contado desde el límite teórico» lo recuerda;
- en cuanto a la fecha, la realización no iba con retraso: el siguiente vencimiento de calendario se cuenta desde la fecha real (+12 meses).

Cada criterio (FH, ciclos, fecha) se trata por separado: la base adoptada es el menor valor entre la realización real y el límite.

## 3. Realización fuera de tolerancia

Si la realización supera la tolerancia, se marca como **fuera de tolerancia**. El siguiente vencimiento parte entonces de la realización real, y el exceso permanece visible en el historial para el análisis de la CAMO.

## 4. Reglas de registro

- Las realizaciones de una misma tarea deben registrarse en orden cronológico.
- Una tolerancia está **prohibida** en una tarea ALS o CMR (limitaciones de aeronavegabilidad).
- Una tolerancia en una tarea AD exige una **referencia** (párrafo de la AD que la autoriza).
