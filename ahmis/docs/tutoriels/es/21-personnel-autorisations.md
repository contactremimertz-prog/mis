# 21. Personal, licencias y autorizaciones

**Cuenta: `qualite`**

AHMIS distingue dos cosas:

- la **cuenta de usuario**, con su rol, que determina las pantallas accesibles;
- la **ficha de personal**, con su licencia Part-66 y sus autorizaciones, que determina lo que la persona puede **firmar**.

## 1. Consultar una ficha

Menú **Personal y autorizaciones** → **Claire DUBOIS**:

- licencia `FR.66.DEMO.0002`, categorías B1.3 / B1.1, fecha de validez;
- **autorizaciones** de la organización Part-145: n.º, tipo, categoría, certificadora o no, alcance, validez, estado;
- **formaciones** de validez limitada: factores humanos, EWIS…;
- sus últimos trabajos firmados e inspecciones.

**A comprobar**: su autorización **Super Puma** caduca en 45 días. Se contabiliza en el indicador «autorización(es) que caducan en 60 d» del panel de control.

## 2. Suspender una autorización

1. Añada a Claire DUBOIS una autorización (formulario al final de la página): n.º `AUT-TEST`, tipo `ATR72-600`, categoría B2, certificadora, fechas del día a +1 año, marque **suspendida** → **Añadir**. Aparece «Suspendida».
2. Para una suspensión real, modifique la autorización existente desde la administración (cuenta `admin` → Administración → Autorizaciones) y marque «suspendida». La persona ya no puede firmar en ese tipo, de forma inmediata.

## 3. Qué verifica cada firma

| Acción | Requisito |
|---|---|
| Iniciar, firmar un paso, firmar los trabajos | Autorización válida (cualquier categoría) en el tipo + formaciones obligatorias de todo el personal al día |
| Inspección independiente | Autorización **certificadora** válida + licencia válida + persona distinta del ejecutante + formaciones del personal certificador + experiencia reciente |
| Aplazamiento de defecto | Autorización certificadora válida + formaciones + experiencia reciente |
| CRS | Autorización certificadora B1/B2/B3/C (solo C para una gran revisión) + licencia válida + formaciones + experiencia reciente |

Todas las razones que impiden una firma se enumeran de una vez, en la task card y en la ficha de personal (tutorial 28).

## 4. Crear una persona

1. Cuenta `admin` → **Administración** → Usuarios → cree la cuenta y añádala al grupo deseado («Mecánico», «Certificador»…).
2. Cuenta `qualite` → **Personal** → **+ Crear**: vincule la cuenta, introduzca n.º de empleado, nombre, visado, licencia.
3. Añada sus autorizaciones y formaciones.

> Solo las formaciones de las **categorías obligatorias** bloquean la firma (por defecto: factores humanos para todos, más la formación continua para el personal certificador). Otra formación caducada, como «Sûreté / zones réservées» de Lucas MARTIN, se señala en rojo sin bloquear. El tutorial 28 detalla la experiencia reciente y las formaciones obligatorias.
