# 3. Crear un tipo y una aeronave, tomar su configuración

**Cuenta: `camo`**

Objetivo: incorporar a la flota un nuevo NH90, F-HDMX, con su primer motor.

## 1. El tipo de aeronave

El tipo NH90 ya existe. Para ver cómo se define un tipo:

1. Menú **Tipos y configuración** → haga clic en **NH90**.
2. La ficha muestra las aeronaves del tipo, el **programa de mantenimiento** (tareas activas), el personal autorizado y los P/N aplicables.

Para crear un nuevo tipo: botón **+ Crear** en la lista. El campo «denominación de los ciclos» permite mostrar «Aterrizajes» para un helicóptero.

## 2. Crear la aeronave

1. Menú **Flota** → **+ Crear**.
2. Rellene:
    - Matrícula: `F-HDMX`
    - Número de serie: `9199`
    - Tipo: `NHIndustries NH90`
    - Fecha de fabricación: hace 3 años
    - Horas totales: `1250`; ciclos: `3800`; contadores actualizados a: hoy
    - Utilización prevista: `1.5` FH/día y `4` ciclos/día
3. **Guardar**.

**Resultado**: se abre la ficha. Todas las tareas del programa NH90 aparecen ya en **Vencimientos**. Como no existe ningún historial, la mayoría se calculan desde la fabricación y figuran como **«Vencido»**. Es lo previsto: AHMIS nunca supone que una tarea se haya realizado.

> Los contadores solo pueden introducirse en la creación. Después, evolucionan únicamente mediante los registros de horas de vuelo (tutorial 4), para mantener una trazabilidad completa.

## 3. Tomar el historial de las tareas

Para cada tarea, registre la última realización conocida (obtenida del logbook):

1. En la tabla de vencimientos de F-HDMX, haga clic en la tarea **N90-05-100 Visite 100 h / 12 mois**.
2. En «Situación por aeronave», haga clic en **histórico** en la línea F-HDMX.
3. Introduzca: fecha hace 2 meses, FH `1190`, ciclos `3620`, origen «Registro histórico», referencia `Logbook p.42`, certificado por `Atelier X – CRS 1234`.
4. **Guardar**.

**Resultado**: la revisión de 100 h de F-HDMX vence ahora a 1 290 FH (1 190 + 100), es decir, quedan 40 FH.

## 4. Tomar la configuración (componentes instalados)

El componente entra primero en el almacén con su certificado y, después, la CAMO lo vincula a la aeronave:

1. Cuenta **`magasin`** → menú **Recepción**: P/N `DEMO-ARR2D-0001` (RTM322), S/N `DEMO-E2X99`, cantidad 1, ubicación `MAG-PRINC`, estado «Revisado», TSN `1250`, CSN `3800`, TSO `1250`, CSO `3800`. Certificado: EASA Form 1, n.º `F1-TEST-01`, emisor `Atelier moteur agréé`, fecha del día, estado «Revisado». Marque las 3 comprobaciones en la recepción → **Guardar**.
2. Cuenta **`camo`** → abra F-HDMX → **Toma de configuración**: componente `DEMO-E2X99`, posición `MOT 1`, fecha = puesta en servicio, referencia `Relevé de configuration d'entrée en flotte` → **Guardar**.

**Resultado**: el motor aparece en «Configuración instalada» con su TBO restante (4 000 − 1 250 = 2 750 FH). La tarea de componente **N90-72-500** (boroscopia del motor) aparece en los vencimientos como «Vencido» mientras no se tome su última realización. Hágalo como en el paso 3, eligiendo el componente `DEMO-E2X99` y sus contadores (TSN/CSN) en la fecha de la última boroscopia.

> La toma de configuración sirve únicamente para la incorporación a la flota. En explotación, todo movimiento de componente pasa por una task card (tutorial 14).
