# 0. Presentación de AHMIS

AHMIS (**A**ircraft & **H**elicopter **M**aintenance **I**nformation **S**ystem) cubre tres áreas de actividad sobre una única base de datos:

| Módulo | Para quién | Funciones principales |
|---|---|---|
| **Aeronavegabilidad (CAMO)** | Ingeniero CAMO | Flota, configuración, horas de vuelo, programa de mantenimiento y su revisión anual, AD/SB, modificaciones y reparaciones, LLP/TBO, vencimientos, previsión, ARC, prórroga de aplazamientos, transferencia de expedientes |
| **Mantenimiento (Part-145)** | Planificador, mecánicos, personal certificador | Planificación, paquetes de trabajo, task cards, firmas, inspección independiente, defectos/MEL, cambio de componente, CRS, experiencia reciente y formaciones bloqueantes, notificaciones de sucesos |
| **Logística** | Almacenero | Recepción con Form 1 según la clase de artículo, almacén, caducidad, cuarentena, baja y mutilación, solicitudes de piezas, herramientas y calibración |
| **Calidad** | Responsable de calidad | Registro de auditoría, firmas electrónicas, personal y autorizaciones, notificaciones de sucesos, conservación de los registros |

## Los datos de demostración

La demo carga una flota mixta de 6 aeronaves en explotación, predominantemente de **Airbus Helicopters**, más un helicóptero retirado del servicio:

| Matrícula | Tipo | Situación de partida (para los tutoriales) |
|---|---|---|
| F-HDMA | NH90 | Revisión de 100 h y AD por planificar, BTP próxima a su TBO |
| F-HDMB | NH90 | **AD vencida**, revisión de 100 h en tolerancia, cubo del rotor (LLP) próximo a su límite, WP planificado vacío |
| F-HDMC | H135 (HEMS) | Defecto aplazado MEL cat. C, boletín ASB abierto, cubo del rotor (LLP) controlado en ciclos |
| F-HDMD | H145 (HEMS) | **En mantenimiento**: paquete de trabajo en curso con task cards en todas las fases |
| F-HDME | Super Puma | ARC que caduca en 20 días |
| F-HDMF | ATR 72-600 | AD por evaluar, tarea calendario vencida |
| F-HDMZ | NH90 | **Retirado del servicio** hace 20 meses, expediente transferido al adquirente (tutorial 30) |

También contiene: revisiones del programa en todos los estados (tutorial 27), tres notificaciones de sucesos (tutorial 29), una pieza dada de baja (tutorial 31) y un antiguo empleado cuyo expediente ha llegado al final del periodo de conservación (tutorial 30).

> ⚠️ **Todas las referencias (tareas, P/N, AD, intervalos, límites) son ficticias** y llevan el prefijo «DEMO». Sirven únicamente para ilustrar el software. En explotación, los datos proceden de los documentos del fabricante (MSM, MRI, ALS…) y de las autoridades.

## Cuentas de demostración

Contraseña común: **`Ahmis2026!`**

| Identificador | Persona | Rol | Puede firmar |
|---|---|---|---|
| `admin` | — | Administrador (todos los derechos) | No (sin ficha de personal) |
| `camo` | Julien MOREAU | Ingeniero CAMO | — |
| `planif` | Nadia ROUX | Planificador | — |
| `meca` | Lucas MARTIN | Mecánico no certificador | Ejecución (helicópteros) |
| `b1` | Claire DUBOIS | Personal certificador B1 | Ejecución, inspección, CRS, aplazamiento de defectos |
| `b2` | Karim BENALI | Personal certificador B2 | Ídem (helicópteros) |
| `certc` | Sophie LAMBERT | Personal certificador C | Ídem + CRS de gran revisión |
| `magasin` | Thomas PETIT | Almacenero | — |
| `qualite` | Isabelle GARNIER | Responsable de calidad | — |

Los derechos de **acceso a las pantallas** dependen del rol. Los derechos de **firma** dependen además de las autorizaciones individuales de la persona (tipo de aeronave, categoría, validez): AHMIS las verifica en cada firma.

## Orden recomendado de los tutoriales

1. Instalación (tutorial 1) y, a continuación, primeros pasos (2).
2. Lado CAMO: 3 a 10.
3. Lado taller: 11 a 16.
4. Lado almacén: 17 a 20.
5. Calidad y aspectos técnicos: 21 a 23.
6. El **tutorial 24** encadena todo en un escenario completo, desde el vencimiento hasta el CRS.
7. Reglas de gestión reglamentarias: **25 a 31** (tolerancias, modificaciones, revisión del programa, experiencia reciente, notificaciones de sucesos, conservación y transferencia, prórroga de aplazamientos, baja de piezas, clases de artículos).
8. La **matriz de cumplimiento** (32) relaciona cada requisito de EASA con las funciones de AHMIS.

Consejo: para volver a empezar de cero en cualquier momento, ejecute `reinitialiser_demo` (véase el tutorial 1).
