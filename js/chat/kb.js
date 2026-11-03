/**
 * @file Knowledge base of the MIS assistant (validated questions and answers).
 *
 * The site is static, so the assistant does not generate text: it only shows
 * the 20 answers validated by the product owner, in the 4 UI languages.
 * Each entry:
 *   id       stable identifier
 *   screen   MIS screen the answer links to (shown only if the profile may see it)
 *   refusal  true for an out-of-scope answer (the assistant never acts on data)
 *   fr/en/es/de: { q: question, a: [paragraphs], src: [sources], kw: keywords }
 * Keywords are matched without accents or case; a question typed in any of
 * the 4 languages is understood, the answer follows the UI language.
 *
 * EASA references: only the extracts confirmed against the official text by
 * the EASA controller team are cited (145.A.42, 145.A.50, 145.A.55(c),
 * M.A.301, M.A.303). Part-CAMO articles are not verified and are not cited.
 * Statements such as "not airworthy" describe MIS rules, and the alert
 * thresholds (25 h, 30 days, 30 cycles) are MIS settings, not EASA limits.
 */
(function () {
  "use strict";

  const KB = [
    {
      id: "login", screen: null,
      fr: { q: "Comment me connecter ?",
        a: ["Choisissez votre profil, puis saisissez votre code personnel. Il vous est remis séparément ; tirets et majuscules sont facultatifs. Le code n'est jamais affiché ni stocké en clair."],
        src: ["Guide MIS · Connexion"], kw: "connecter connexion login code personnel mot passe profil identifier" },
      en: { q: "How do I sign in?",
        a: ["Choose your profile, then type your personal code. It is handed to you separately; dashes and capitals are optional. The code is never displayed or stored in clear."],
        src: ["MIS guide · Sign-in"], kw: "sign login log connect personal code password profile" },
      es: { q: "¿Cómo inicio sesión?",
        a: ["Elija su perfil y escriba su código personal. Se le entrega por separado; los guiones y las mayúsculas son opcionales. El código nunca se muestra ni se guarda en claro."],
        src: ["Guía MIS · Inicio de sesión"], kw: "iniciar sesion conectar codigo personal contrasena perfil acceso" },
      de: { q: "Wie melde ich mich an?",
        a: ["Wählen Sie Ihr Profil und geben Sie Ihren persönlichen Code ein. Er wird Ihnen separat ausgehändigt; Bindestriche und Großbuchstaben sind optional. Der Code wird nie angezeigt und nie im Klartext gespeichert."],
        src: ["MIS-Leitfaden · Anmeldung"], kw: "anmelden anmeldung einloggen persoenlicher code passwort profil" }
    },
    {
      id: "locked", screen: null,
      fr: { q: "Pourquoi mon profil est-il bloqué ?",
        a: ["Après 5 codes faux en 10 minutes (connexion ou signature), le profil est bloqué 5 minutes, même après rechargement de la page. Attendez la fin du décompte affiché."],
        src: ["Guide MIS · Connexion > Verrouillage"], kw: "bloque blocage verrouille verrouillage trop echecs tentatives attendre" },
      en: { q: "Why is my profile locked?",
        a: ["After 5 wrong codes within 10 minutes (sign-in or signature), the profile is locked for 5 minutes, even after reloading the page. Wait until the countdown shown ends."],
        src: ["MIS guide · Sign-in > Lock-out"], kw: "locked lock blocked too many failures attempts wait" },
      es: { q: "¿Por qué está bloqueado mi perfil?",
        a: ["Tras 5 códigos erróneos en 10 minutos (inicio de sesión o firma), el perfil se bloquea 5 minutos, incluso si recarga la página. Espere a que termine la cuenta atrás."],
        src: ["Guía MIS · Inicio de sesión > Bloqueo"], kw: "bloqueado bloqueo demasiados intentos fallos esperar" },
      de: { q: "Warum ist mein Profil gesperrt?",
        a: ["Nach 5 falschen Codes innerhalb von 10 Minuten (Anmeldung oder Signatur) wird das Profil 5 Minuten gesperrt, auch nach dem Neuladen der Seite. Warten Sie, bis der angezeigte Countdown abläuft."],
        src: ["MIS-Leitfaden · Anmeldung > Sperre"], kw: "gesperrt sperre blockiert fehlversuche versuche warten" }
    },
    {
      id: "switch", screen: null,
      fr: { q: "Comment changer de profil ?",
        a: ["Choisissez le profil dans la liste en haut à droite, puis saisissez le code personnel de ce profil. Tant que le code n'est pas validé, vous restez sur le profil actuel."],
        src: ["Guide MIS · Connexion > Changer de profil"], kw: "changer profil utilisateur basculer autre profil" },
      en: { q: "How do I switch profile?",
        a: ["Choose the profile in the list at the top right, then type that profile's personal code. Until the code is accepted, you stay on the current profile."],
        src: ["MIS guide · Sign-in > Switch profile"], kw: "switch change profile user another" },
      es: { q: "¿Cómo cambio de perfil?",
        a: ["Elija el perfil en la lista de arriba a la derecha y escriba el código personal de ese perfil. Mientras el código no se valide, sigue en el perfil actual."],
        src: ["Guía MIS · Inicio de sesión > Cambiar de perfil"], kw: "cambiar perfil usuario otro" },
      de: { q: "Wie wechsle ich das Profil?",
        a: ["Wählen Sie das Profil in der Liste oben rechts und geben Sie den persönlichen Code dieses Profils ein. Bis der Code bestätigt ist, bleiben Sie im aktuellen Profil."],
        src: ["MIS-Leitfaden · Anmeldung > Profil wechseln"], kw: "wechseln profil benutzer anderes" }
    },
    {
      id: "denied", screen: "users",
      fr: { q: "Pourquoi je vois « Accès refusé » ?",
        a: ["Chaque rôle ne voit que ses écrans. Un accès direct à un autre écran est refusé et enregistré au journal. La matrice des accès est dans l'écran Utilisateurs et rôles."],
        src: ["Matrice des droits par rôle"], kw: "acces refuse droits role ecran interdit autorisation voir menu" },
      en: { q: "Why do I see “Access denied”?",
        a: ["Each role only sees its own screens. Direct access to another screen is refused and written to the audit log. The access matrix is on the Users and roles screen."],
        src: ["Role permission matrix"], kw: "access denied rights role screen forbidden permission menu" },
      es: { q: "¿Por qué veo «Acceso denegado»?",
        a: ["Cada rol solo ve sus pantallas. El acceso directo a otra pantalla se rechaza y se registra en el diario. La matriz de accesos está en la pantalla Usuarios y roles."],
        src: ["Matriz de permisos por rol"], kw: "acceso denegado derechos rol pantalla prohibido permiso menu" },
      de: { q: "Warum sehe ich „Zugriff verweigert“?",
        a: ["Jede Rolle sieht nur ihre eigenen Bildschirme. Ein direkter Zugriff auf einen anderen Bildschirm wird abgelehnt und im Prüfprotokoll erfasst. Die Zugriffsmatrix steht im Bildschirm Benutzer und Rollen."],
        src: ["Berechtigungsmatrix nach Rolle"], kw: "zugriff verweigert rechte rolle bildschirm verboten berechtigung menue" }
    },
    {
      id: "wo_create", screen: "workorders",
      fr: { q: "Qui peut créer un ordre de travail ?",
        a: ["Le Responsable CAMO et le Planificateur maintenance, depuis l'écran Ordres de travail, bouton « Nouvel ordre de travail »."],
        src: ["Matrice des droits par rôle", "Guide MIS · Ordres de travail"], kw: "creer nouvel ordre travail ot ouvrir planifier" },
      en: { q: "Who can create a work order?",
        a: ["The CAMO manager and the maintenance planner, from the Work orders screen, “New work order” button."],
        src: ["Role permission matrix", "MIS guide · Work orders"], kw: "create new work order wo open plan" },
      es: { q: "¿Quién puede crear una orden de trabajo?",
        a: ["El responsable CAMO y el planificador de mantenimiento, desde la pantalla Órdenes de trabajo, botón «Nueva orden de trabajo»."],
        src: ["Matriz de permisos por rol", "Guía MIS · Órdenes de trabajo"], kw: "crear nueva orden trabajo ot planificar" },
      de: { q: "Wer kann einen Arbeitsauftrag anlegen?",
        a: ["Der CAMO-Verantwortliche und der Instandhaltungsplaner, im Bildschirm Arbeitsaufträge über die Schaltfläche „Neuer Arbeitsauftrag“."],
        src: ["Berechtigungsmatrix nach Rolle", "MIS-Leitfaden · Arbeitsaufträge"], kw: "anlegen erstellen neuer arbeitsauftrag auftrag planen" }
    },
    {
      id: "crs", screen: "workorders",
      fr: { q: "Comment émettre un CRS ?",
        a: ["Rôle Certificateur : ouvrez l'ordre de travail, puis « Émettre le CRS », et signez avec votre code personnel.",
          "Toutes les cartes doivent être signées par le technicien et contresignées, sans non-conformité de niveau 1 ouverte sur l'appareil. Le CRS fige l'agrément, votre catégorie (B1 ou B2) et les heures."],
        src: ["Guide MIS · Ordres de travail > CRS", "Part-145, 145.A.50 (extrait)"], kw: "emettre crs certificat remise service signer liberer cloturer ordre" },
      en: { q: "How do I issue a CRS?",
        a: ["Certifier role: open the work order, then “Issue CRS”, and sign with your personal code.",
          "Every task card must be signed by the technician and countersigned, with no level 1 finding open on the aircraft. The CRS freezes the approval, your category (B1 or B2) and the hours."],
        src: ["MIS guide · Work orders > CRS", "Part-145, 145.A.50 (extract)"], kw: "issue crs certificate release service sign close" },
      es: { q: "¿Cómo emito un CRS?",
        a: ["Rol Certificador: abra la orden de trabajo, pulse «Emitir el CRS» y firme con su código personal.",
          "Todas las tarjetas deben estar firmadas por el técnico y refrendadas, sin no conformidad de nivel 1 abierta en la aeronave. El CRS fija la aprobación, su categoría (B1 o B2) y las horas."],
        src: ["Guía MIS · Órdenes de trabajo > CRS", "Part-145, 145.A.50 (extracto)"], kw: "emitir crs certificado puesta servicio firmar cerrar" },
      de: { q: "Wie stelle ich ein CRS aus?",
        a: ["Rolle Freigabeberechtigter: Öffnen Sie den Arbeitsauftrag, dann „CRS ausstellen“, und signieren Sie mit Ihrem persönlichen Code.",
          "Alle Arbeitskarten müssen vom Techniker signiert und gegengezeichnet sein, ohne offene Beanstandung der Stufe 1 am Luftfahrzeug. Das CRS hält die Genehmigung, Ihre Kategorie (B1 oder B2) und die Stunden fest."],
        src: ["MIS-Leitfaden · Arbeitsaufträge > CRS", "Part-145, 145.A.50 (Auszug)"], kw: "ausstellen crs freigabebescheinigung freigabe signieren abschliessen" }
    },
    {
      id: "countersign", screen: "workorders",
      fr: { q: "Pourquoi je ne peux pas contresigner cette carte ?",
        a: ["Vous ne pouvez pas certifier un travail que vous avez exécuté : la contresignature doit venir d'une autre personne. La carte doit aussi avoir été signée d'abord par le technicien."],
        src: ["Guide MIS · Ordres de travail > Cartes de travail"], kw: "contresigner contresignature carte signer refuse propre travail" },
      en: { q: "Why can't I countersign this task card?",
        a: ["You cannot certify work you performed yourself: the countersignature must come from someone else. The card must also have been signed first by the technician."],
        src: ["MIS guide · Work orders > Task cards"], kw: "countersign countersignature card sign refused own work" },
      es: { q: "¿Por qué no puedo refrendar esta tarjeta?",
        a: ["No puede certificar un trabajo que ha realizado usted: el refrendo debe venir de otra persona. La tarjeta también debe haber sido firmada antes por el técnico."],
        src: ["Guía MIS · Órdenes de trabajo > Tarjetas de trabajo"], kw: "refrendar refrendo tarjeta firmar rechazado propio trabajo" },
      de: { q: "Warum kann ich diese Karte nicht gegenzeichnen?",
        a: ["Sie dürfen keine Arbeit freigeben, die Sie selbst ausgeführt haben: Die Gegenzeichnung muss von einer anderen Person kommen. Die Karte muss außerdem zuerst vom Techniker signiert sein."],
        src: ["MIS-Leitfaden · Arbeitsaufträge > Arbeitskarten"], kw: "gegenzeichnen gegenzeichnung karte signieren abgelehnt eigene arbeit" }
    },
    {
      id: "wo_start", screen: "stock",
      fr: { q: "Pourquoi je ne peux pas démarrer cet OT ?",
        a: ["La pièce nécessaire est en quarantaine, sans EASA Form 1. Le magasin doit d'abord rattacher le certificat à la pièce."],
        src: ["Guide MIS · Stock > Quarantaine"], kw: "demarrer commencer ot ordre travail bloque piece quarantaine" },
      en: { q: "Why can't I start this work order?",
        a: ["The required part is in quarantine, without an EASA Form 1. The store must first attach the certificate to the part."],
        src: ["MIS guide · Stock > Quarantine"], kw: "start begin work order blocked part quarantine" },
      es: { q: "¿Por qué no puedo iniciar esta OT?",
        a: ["La pieza necesaria está en cuarentena, sin EASA Form 1. El almacén debe primero adjuntar el certificado a la pieza."],
        src: ["Guía MIS · Stock > Cuarentena"], kw: "iniciar empezar orden trabajo bloqueada pieza cuarentena" },
      de: { q: "Warum kann ich diesen Arbeitsauftrag nicht starten?",
        a: ["Das benötigte Teil ist in Quarantäne, ohne EASA Form 1. Das Lager muss zuerst das Zertifikat an das Teil anhängen."],
        src: ["MIS-Leitfaden · Lager > Quarantäne"], kw: "starten beginnen arbeitsauftrag blockiert teil quarantaene" }
    },
    {
      id: "flight", screen: "fleet",
      fr: { q: "Comment enregistrer un vol ?",
        a: ["Rôles CAMO ou Planificateur : Flotte, ouvrez l'appareil, puis « Enregistrer un vol ». Le MIS accepte de 0,1 à 24 h et de 0 à 60 cycles par saisie : ce sont des contrôles de saisie du MIS, pas des seuils EASA. La saisie est impossible sur un appareil immobilisé."],
        src: ["Guide MIS · Flotte"], kw: "enregistrer vol heures cycles saisir flotte appareil" },
      en: { q: "How do I record a flight?",
        a: ["CAMO or planner role: Fleet, open the aircraft, then “Record a flight”. The MIS accepts 0.1 to 24 h and 0 to 60 cycles per entry: these are MIS input checks, not EASA limits. Entry is impossible on a grounded aircraft."],
        src: ["MIS guide · Fleet"], kw: "record flight hours cycles enter fleet aircraft" },
      es: { q: "¿Cómo registro un vuelo?",
        a: ["Rol CAMO o Planificador: Flota, abra la aeronave y pulse «Registrar un vuelo». El MIS acepta de 0,1 a 24 h y de 0 a 60 ciclos por registro: son controles de entrada del MIS, no límites EASA. No se puede registrar en una aeronave inmovilizada."],
        src: ["Guía MIS · Flota"], kw: "registrar vuelo horas ciclos flota aeronave" },
      de: { q: "Wie erfasse ich einen Flug?",
        a: ["Rolle CAMO oder Planer: Flotte, Luftfahrzeug öffnen, dann „Flug erfassen“. Das MIS akzeptiert 0,1 bis 24 h und 0 bis 60 Zyklen pro Eingabe: Das sind Eingabeprüfungen des MIS, keine EASA-Grenzwerte. Bei einem stillgelegten Luftfahrzeug ist keine Eingabe möglich."],
        src: ["MIS-Leitfaden · Flotte"], kw: "erfassen flug stunden zyklen flotte luftfahrzeug" }
    },
    {
      id: "red_alert", screen: "dashboard",
      fr: { q: "Que signifie l'alerte rouge du tableau de bord ?",
        a: ["Une échéance est dépassée : le MIS affiche l'appareil comme non apte au vol tant que la tâche n'est pas réalisée et certifiée (règle du MIS).",
          "Le MIS signale aussi les échéances « à surveiller » dans les 30 jours, 25 h ou 30 cycles : c'est un réglage d'alerte du MIS, pas un seuil EASA."],
        src: ["Guide MIS · Tableau de bord", "Part-M, M.A.301 (extrait) : réalisation des tâches de maintien de la navigabilité"], kw: "alerte rouge tableau bord echeance depassee retard apte vol" },
      en: { q: "What does the red alert on the dashboard mean?",
        a: ["A due date has passed: the MIS shows the aircraft as not airworthy until the task is done and certified (MIS rule).",
          "The MIS also flags items “to watch” within 30 days, 25 h or 30 cycles: this is an MIS alert setting, not an EASA limit."],
        src: ["MIS guide · Dashboard", "Part-M, M.A.301 (extract): performance of continuing airworthiness tasks"], kw: "red alert dashboard overdue due airworthy" },
      es: { q: "¿Qué significa la alerta roja del panel?",
        a: ["Un vencimiento está superado: el MIS muestra la aeronave como no apta para el vuelo hasta que la tarea se realice y certifique (regla del MIS).",
          "El MIS señala también los vencimientos «a vigilar» en 30 días, 25 h o 30 ciclos: es un ajuste de alerta del MIS, no un límite EASA."],
        src: ["Guía MIS · Panel", "Part-M, M.A.301 (extracto): realización de las tareas de aeronavegabilidad continuada"], kw: "alerta roja panel vencimiento superado apta vuelo" },
      de: { q: "Was bedeutet der rote Alarm im Dashboard?",
        a: ["Eine Fälligkeit ist überschritten: Das MIS zeigt das Luftfahrzeug als nicht lufttüchtig an, bis die Aufgabe ausgeführt und freigegeben ist (MIS-Regel).",
          "Das MIS meldet außerdem Fälligkeiten „zu beobachten“ innerhalb von 30 Tagen, 25 h oder 30 Zyklen: Das ist eine Alarmeinstellung des MIS, kein EASA-Grenzwert."],
        src: ["MIS-Leitfaden · Dashboard", "Part-M, M.A.301 (Auszug): Durchführung der Aufgaben zur Aufrechterhaltung der Lufttüchtigkeit"], kw: "roter alarm dashboard faelligkeit ueberschritten lufttuechtig" }
    },
    {
      id: "quarantine", screen: "stock",
      fr: { q: "Pourquoi cette pièce est-elle en quarantaine ?",
        a: ["Elle a été réceptionnée sans EASA Form 1. Le magasinier la libère avec « Rattacher un EASA Form 1 » : référence unique (dans la démo, selon la convention de démo F1-ORG-AA-NNNNN, non définie par l'EASA), organisme émetteur et date non future."],
        src: ["Guide MIS · Stock > Form 1", "Part-145, 145.A.42 (extrait)"], kw: "piece quarantaine form1 form certificat liberer rattacher" },
      en: { q: "Why is this part in quarantine?",
        a: ["It was received without an EASA Form 1. The storekeeper releases it with “Attach an EASA Form 1”: a unique reference (in the demo, following the demo convention F1-ORG-YY-NNNNN, not defined by EASA), the issuing organisation and a date not in the future."],
        src: ["MIS guide · Stock > Form 1", "Part-145, 145.A.42 (extract)"], kw: "part quarantine form1 form certificate release attach" },
      es: { q: "¿Por qué esta pieza está en cuarentena?",
        a: ["Se recibió sin EASA Form 1. El almacenero la libera con «Adjuntar un EASA Form 1»: referencia única (en la demo, según la convención de demo F1-ORG-AA-NNNNN, no definida por EASA), organismo emisor y fecha no futura."],
        src: ["Guía MIS · Stock > Form 1", "Part-145, 145.A.42 (extracto)"], kw: "pieza cuarentena form1 form certificado liberar adjuntar" },
      de: { q: "Warum ist dieses Teil in Quarantäne?",
        a: ["Es wurde ohne EASA Form 1 eingegangen. Der Lagerist gibt es mit „EASA Form 1 anhängen“ frei: eindeutige Referenz (in der Demo nach der Demo-Konvention F1-ORG-JJ-NNNNN, nicht von der EASA festgelegt), ausstellende Organisation und ein Datum, das nicht in der Zukunft liegt."],
        src: ["MIS-Leitfaden · Lager > Form 1", "Part-145, 145.A.42 (Auszug)"], kw: "teil quarantaene form1 form zertifikat freigeben anhaengen" }
    },
    {
      id: "install", screen: "workorders",
      fr: { q: "Pourquoi l'installation de la pièce est-elle refusée ?",
        a: ["À l'installation, le MIS revérifie le Form 1, la date de péremption et la limite de vie. Seules les pièces en stock avec un Form 1 valide et non périmées sont proposées. Chaque refus est enregistré au journal."],
        src: ["Guide MIS · Ordres de travail > Installer une pièce", "Part-145, 145.A.42 (extrait)"], kw: "installer installation piece refusee perimee limite vie poser" },
      en: { q: "Why is the part installation refused?",
        a: ["At installation, the MIS re-checks the Form 1, the expiry date and the life limit. Only parts in stock with a valid Form 1 and not expired are offered. Each refusal is written to the audit log."],
        src: ["MIS guide · Work orders > Install a part", "Part-145, 145.A.42 (extract)"], kw: "install installation part refused expired life limit fit" },
      es: { q: "¿Por qué se rechaza la instalación de la pieza?",
        a: ["En la instalación, el MIS vuelve a comprobar el Form 1, la fecha de caducidad y el límite de vida. Solo se proponen piezas en stock con Form 1 válido y no caducadas. Cada rechazo se registra en el diario."],
        src: ["Guía MIS · Órdenes de trabajo > Instalar una pieza", "Part-145, 145.A.42 (extracto)"], kw: "instalar instalacion pieza rechazada caducada limite vida montar" },
      de: { q: "Warum wird der Einbau des Teils abgelehnt?",
        a: ["Beim Einbau prüft das MIS erneut das Form 1, das Ablaufdatum und die Lebensdauergrenze. Angeboten werden nur Teile auf Lager mit gültigem Form 1, die nicht abgelaufen sind. Jede Ablehnung wird im Prüfprotokoll erfasst."],
        src: ["MIS-Leitfaden · Arbeitsaufträge > Teil einbauen", "Part-145, 145.A.42 (Auszug)"], kw: "einbauen einbau teil abgelehnt abgelaufen lebensdauer" }
    },
    {
      id: "po", screen: "orders",
      fr: { q: "Qui peut passer une commande fournisseur ?",
        a: ["Le Planificateur et le Magasinier, depuis l'écran Commandes. Une commande reçue sans certificat reste en attente de document."],
        src: ["Matrice des droits par rôle", "Guide MIS · Commandes"], kw: "commande fournisseur commander achat acheter" },
      en: { q: "Who can place a supplier order?",
        a: ["The planner and the storekeeper, from the Orders screen. An order received without a certificate stays waiting for its document."],
        src: ["Role permission matrix", "MIS guide · Orders"], kw: "order supplier purchase buy" },
      es: { q: "¿Quién puede hacer un pedido a proveedor?",
        a: ["El planificador y el almacenero, desde la pantalla Pedidos. Un pedido recibido sin certificado queda a la espera del documento."],
        src: ["Matriz de permisos por rol", "Guía MIS · Pedidos"], kw: "pedido proveedor comprar compra" },
      de: { q: "Wer kann eine Lieferantenbestellung aufgeben?",
        a: ["Der Planer und der Lagerist, im Bildschirm Bestellungen. Eine ohne Zertifikat eingegangene Bestellung wartet auf ihr Dokument."],
        src: ["Berechtigungsmatrix nach Rolle", "MIS-Leitfaden · Bestellungen"], kw: "bestellung lieferant bestellen einkauf kaufen" }
    },
    {
      id: "nc_close", screen: "nc",
      fr: { q: "Quel rôle peut clôturer une non-conformité ?",
        a: ["Seul le Responsable qualité, après avoir renseigné l'analyse des causes et l'action corrective, avec sa signature. Tous les rôles peuvent en ouvrir une."],
        src: ["Matrice des droits par rôle", "Guide MIS · Non-conformités"], kw: "cloturer cloture non conformite nc qualite role fermer" },
      en: { q: "Which role can close a finding?",
        a: ["Only the quality manager, after filling in the root cause analysis and the corrective action, with a signature. Every role can open one."],
        src: ["Role permission matrix", "MIS guide · Findings"], kw: "close closing finding nonconformity nc quality role" },
      es: { q: "¿Qué rol puede cerrar una no conformidad?",
        a: ["Solo el responsable de calidad, tras completar el análisis de causas y la acción correctiva, con su firma. Todos los roles pueden abrir una."],
        src: ["Matriz de permisos por rol", "Guía MIS · No conformidades"], kw: "cerrar cierre no conformidad nc calidad rol" },
      de: { q: "Welche Rolle kann eine Beanstandung schließen?",
        a: ["Nur der Qualitätsverantwortliche, nach Eintrag der Ursachenanalyse und der Korrekturmaßnahme, mit seiner Signatur. Jede Rolle kann eine eröffnen."],
        src: ["Berechtigungsmatrix nach Rolle", "MIS-Leitfaden · Beanstandungen"], kw: "schliessen abschluss beanstandung nichtkonformitaet qualitaet rolle" }
    },
    {
      id: "anchor", screen: "auditlog",
      fr: { q: "À quoi sert l'empreinte de tête du journal ?",
        a: ["Le journal est en ajout seul et chaîné en SHA-256. Copiez l'empreinte de tête hors du poste (courriel, registre qualité) : si le journal est réécrit, elle ne correspondra plus. Elle figure aussi à la fin des exports du journal."],
        src: ["Guide MIS · Journal d'audit"], kw: "empreinte tete journal audit hash chaine integrite trace" },
      en: { q: "What is the audit log head hash for?",
        a: ["The log is append-only and chained with SHA-256. Copy the head hash outside the workstation (email, quality register): if the log is rewritten, it will no longer match. It is also printed at the end of the log exports."],
        src: ["MIS guide · Audit log"], kw: "head hash audit log chain integrity trace" },
      es: { q: "¿Para qué sirve la huella de cabecera del diario?",
        a: ["El diario solo admite añadidos y está encadenado con SHA-256. Copie la huella de cabecera fuera del puesto (correo, registro de calidad): si se reescribe el diario, ya no coincidirá. También figura al final de las exportaciones del diario."],
        src: ["Guía MIS · Diario de auditoría"], kw: "huella cabecera diario auditoria hash cadena integridad" },
      de: { q: "Wozu dient der Kopf-Hash des Prüfprotokolls?",
        a: ["Das Protokoll ist nur erweiterbar und mit SHA-256 verkettet. Kopieren Sie den Kopf-Hash außerhalb des Arbeitsplatzes (E-Mail, Qualitätsregister): Wird das Protokoll umgeschrieben, stimmt er nicht mehr. Er steht auch am Ende der Protokollexporte."],
        src: ["MIS-Leitfaden · Prüfprotokoll"], kw: "kopf hash pruefprotokoll protokoll kette integritaet" }
    },
    {
      id: "export", screen: null,
      fr: { q: "Comment exporter un tableau ?",
        a: ["Utilisez « Export CSV » ou « Export PDF » au-dessus du tableau : le fichier reprend exactement le tableau affiché, filtres compris. Chaque export est enregistré au journal."],
        src: ["Guide MIS · Exports"], kw: "exporter export csv pdf tableau telecharger fichier excel" },
      en: { q: "How do I export a table?",
        a: ["Use “Export CSV” or “Export PDF” above the table: the file holds exactly the table shown, filters included. Each export is written to the audit log."],
        src: ["MIS guide · Exports"], kw: "export csv pdf table download file excel" },
      es: { q: "¿Cómo exporto una tabla?",
        a: ["Use «Exportar CSV» o «Exportar PDF» encima de la tabla: el archivo contiene exactamente la tabla mostrada, filtros incluidos. Cada exportación se registra en el diario."],
        src: ["Guía MIS · Exportaciones"], kw: "exportar exportacion csv pdf tabla descargar archivo excel" },
      de: { q: "Wie exportiere ich eine Tabelle?",
        a: ["Verwenden Sie „CSV-Export“ oder „PDF-Export“ über der Tabelle: Die Datei enthält genau die angezeigte Tabelle, inklusive Filter. Jeder Export wird im Prüfprotokoll erfasst."],
        src: ["MIS-Leitfaden · Exporte"], kw: "exportieren export csv pdf tabelle herunterladen datei excel" }
    },
    {
      id: "crs_retention", screen: "certificates",
      fr: { q: "Combien de temps conserver un CRS ?",
        a: ["Part-145 demande de conserver les enregistrements d'entretien, dont le CRS, au moins 3 ans après la remise en service. La durée retenue par l'organisme figure dans son manuel (MOE). En cas de doute, voyez le responsable qualité."],
        src: ["Part-145, 145.A.55(c) (extrait)", "Documents qualité · MOE"], kw: "conserver conservation duree garder archiver crs enregistrements combien temps" },
      en: { q: "How long must a CRS be kept?",
        a: ["Part-145 requires maintenance records, including the CRS, to be kept for at least 3 years after release to service. The period chosen by the organisation is in its exposition (MOE). If in doubt, ask the quality manager."],
        src: ["Part-145, 145.A.55(c) (extract)", "Quality documents · MOE"], kw: "keep retention retain archive crs records how long period" },
      es: { q: "¿Cuánto tiempo hay que conservar un CRS?",
        a: ["Part-145 exige conservar los registros de mantenimiento, incluido el CRS, al menos 3 años tras la puesta en servicio. El plazo elegido por la organización figura en su manual (MOE). En caso de duda, consulte al responsable de calidad."],
        src: ["Part-145, 145.A.55(c) (extracto)", "Documentos de calidad · MOE"], kw: "conservar conservacion plazo guardar archivar crs registros cuanto tiempo" },
      de: { q: "Wie lange muss ein CRS aufbewahrt werden?",
        a: ["Part-145 verlangt, Instandhaltungsaufzeichnungen, einschließlich des CRS, mindestens 3 Jahre nach der Freigabe aufzubewahren. Die vom Betrieb gewählte Dauer steht in seinem Handbuch (MOE). Im Zweifel fragen Sie den Qualitätsverantwortlichen."],
        src: ["Part-145, 145.A.55(c) (Auszug)", "Qualitätsdokumente · MOE"], kw: "aufbewahren aufbewahrung dauer archivieren crs aufzeichnungen wie lange" }
    },
    {
      id: "ad", screen: "directives",
      fr: { q: "Qu'est-ce qu'une consigne de navigabilité (AD) ?",
        a: ["Une AD impose une action (inspection, modification) pour corriger une condition dangereuse. Son application est obligatoire, dans les délais fixés par chaque AD. Règle du MIS : une AD dont le délai est dépassé fait afficher l'appareil comme non apte au vol. Le suivi est dans l'écran Consignes de navigabilité (AD)."],
        src: ["Part-M, M.A.303 (extrait)", "Guide MIS · Consignes de navigabilité"], kw: "consigne navigabilite ad directive obligatoire" },
      en: { q: "What is an airworthiness directive (AD)?",
        a: ["An AD requires an action (inspection, modification) to correct an unsafe condition. Compliance is mandatory, within the time limits set by each AD. MIS rule: an AD past its time limit makes the MIS show the aircraft as not airworthy. Tracking is on the Airworthiness directives (AD) screen."],
        src: ["Part-M, M.A.303 (extract)", "MIS guide · Airworthiness directives"], kw: "airworthiness directive ad mandatory" },
      es: { q: "¿Qué es una directiva de aeronavegabilidad (AD)?",
        a: ["Una AD impone una acción (inspección, modificación) para corregir una condición insegura. Su cumplimiento es obligatorio, en los plazos fijados por cada AD. Regla del MIS: una AD con el plazo superado hace que el MIS muestre la aeronave como no apta para el vuelo. El seguimiento está en la pantalla Directivas de aeronavegabilidad (AD)."],
        src: ["Part-M, M.A.303 (extracto)", "Guía MIS · Directivas de aeronavegabilidad"], kw: "directiva aeronavegabilidad ad obligatoria" },
      de: { q: "Was ist eine Lufttüchtigkeitsanweisung (AD)?",
        a: ["Eine AD schreibt eine Maßnahme vor (Inspektion, Änderung), um einen unsicheren Zustand zu beheben. Ihre Umsetzung ist Pflicht, innerhalb der Fristen jeder AD. MIS-Regel: Eine AD mit überschrittener Frist lässt das MIS das Luftfahrzeug als nicht lufttüchtig anzeigen. Die Verfolgung erfolgt im Bildschirm Lufttüchtigkeitsanweisungen (AD)."],
        src: ["Part-M, M.A.303 (Auszug)", "MIS-Leitfaden · Lufttüchtigkeitsanweisungen"], kw: "lufttuechtigkeitsanweisung anweisung ad pflicht" }
    },
    {
      id: "out_action", screen: "nc", refusal: true,
      fr: { q: "Peux-tu clôturer NC-2026-029 pour moi ?",
        a: ["Je ne peux pas agir sur les données : je donne uniquement des informations. Pour clôturer cette non-conformité, le Responsable qualité l'ouvre dans l'écran Non-conformités et signe la clôture."],
        src: ["Règles de l'assistant · périmètre"], kw: "peux tu pour moi fais faire ma place" },
      en: { q: "Can you close NC-2026-029 for me?",
        a: ["I cannot act on the data: I only give information. To close this finding, the quality manager opens it on the Findings screen and signs the closure."],
        src: ["Assistant rules · scope"], kw: "can you for me do it instead" },
      es: { q: "¿Puedes cerrar NC-2026-029 por mí?",
        a: ["No puedo actuar sobre los datos: solo doy información. Para cerrar esta no conformidad, el responsable de calidad la abre en la pantalla No conformidades y firma el cierre."],
        src: ["Reglas del asistente · alcance"], kw: "puedes por mi hazlo en mi lugar" },
      de: { q: "Kannst du NC-2026-029 für mich schließen?",
        a: ["Ich kann keine Daten ändern: Ich gebe nur Informationen. Um diese Beanstandung zu schließen, öffnet der Qualitätsverantwortliche sie im Bildschirm Beanstandungen und signiert den Abschluss."],
        src: ["Regeln des Assistenten · Umfang"], kw: "kannst du fuer mich mach statt meiner" }
    },
    {
      id: "out_compliance", screen: "fleet", refusal: true,
      fr: { q: "F-XXXD est-il conforme pour voler aujourd'hui ?",
        a: ["Je ne donne pas d'avis de conformité sur un cas réel. Dans le MIS, un appareil avec une échéance ou une AD dépassée est affiché non apte au vol. Vérifiez son statut dans l'écran Flotte, et la décision revient à la CAMO."],
        src: ["Règles de l'assistant · périmètre", "Guide MIS · Flotte"], kw: "conforme conformite voler aujourd peut il avis" },
      en: { q: "Is F-XXXD compliant to fly today?",
        a: ["I do not give a compliance opinion on a real case. In the MIS, an aircraft with an overdue item or AD is shown as not airworthy. Check its status on the Fleet screen; the decision belongs to the CAMO."],
        src: ["Assistant rules · scope", "MIS guide · Fleet"], kw: "compliant compliance fly today allowed opinion" },
      es: { q: "¿F-XXXD es conforme para volar hoy?",
        a: ["No doy opiniones de conformidad sobre un caso real. En el MIS, una aeronave con un vencimiento o una AD superados se muestra como no apta para el vuelo. Compruebe su estado en la pantalla Flota; la decisión corresponde a la CAMO."],
        src: ["Reglas del asistente · alcance", "Guía MIS · Flota"], kw: "conforme conformidad volar hoy puede opinion" },
      de: { q: "Ist F-XXXD heute flugtauglich?",
        a: ["Ich gebe keine Konformitätsbewertung für einen realen Fall ab. Im MIS wird ein Luftfahrzeug mit überschrittener Fälligkeit oder AD als nicht lufttüchtig angezeigt. Prüfen Sie seinen Status im Bildschirm Flotte; die Entscheidung liegt bei der CAMO."],
        src: ["Regeln des Assistenten · Umfang", "MIS-Leitfaden · Flotte"], kw: "konform konformitaet fliegen heute darf flugtauglich bewertung" }
    }
  ];

  /** Suggested questions shown first, per role (ids of KB entries). */
  const SUGGESTED = {
    CAMO: ["red_alert", "ad", "flight", "wo_create"],
    PLANNER: ["wo_create", "flight", "po", "wo_start"],
    TECH: ["wo_start", "install", "countersign", "locked"],
    CERT: ["crs", "countersign", "crs_retention", "nc_close"],
    STORE: ["quarantine", "po", "install", "denied"],
    QUALITY: ["nc_close", "anchor", "crs_retention", "export"],
    ADMIN: ["denied", "switch", "locked", "anchor"]
  };

  window.MIS_KB = { KB, SUGGESTED };
})();
