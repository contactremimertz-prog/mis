"""Charge un jeu de données de démonstration (flotte mixte, à dominante Airbus Helicopters).

    python manage.py load_demo            # base vide uniquement
    python manage.py load_demo --reset    # efface tout et recharge

AVERTISSEMENT : toutes les références de tâches, P/N, consignes, intervalles et limites sont
FICTIVES et simplifiées. Elles illustrent le fonctionnement d'AHMIS et ne doivent jamais servir
à la maintenance réelle (se référer aux documents constructeur et autorités : MSM, MRI, ALS, AD).
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone

from apps.camo.models import AmpReview, AirworthinessReview, Directive, DirectiveApplicability, MaintenanceTask, TaskAccomplishment, TaskRequiredPart
from apps.core.demo_accounts import DEMO_ACCOUNTS, DEMO_PASSWORD
from apps.core.middleware import set_current_user
from apps.core.roles import setup_roles
from apps.fleet.models import Aircraft, AircraftType, Component, PartNumber, install_component
from apps.logistics.models import PartRequest, ReleaseCertificate, StockItem, StockMovement, StoreLocation, Tool, ToolCalibration
from apps.part145 import services as p145
from apps.part145.models import Authorization, Defect, ExperienceRecord, Qualification, Staff, WorkPackage

D = Decimal
HISTORY_DAYS = 60


class Command(BaseCommand):
    help = "Charge les données de démonstration AHMIS (flotte Airbus Helicopters + ATR)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Efface la base avant chargement")

    def handle(self, *args, **opts):
        if opts["reset"]:
            call_command("flush", interactive=False, verbosity=0)
        elif Aircraft.objects.exists():
            self.stdout.write(self.style.WARNING("La base contient déjà des aéronefs. Utilisez --reset pour recharger."))
            return
        random.seed(145)
        self.today = timezone.localdate()
        try:
            self._load()
        finally:
            set_current_user(None)
        self.stdout.write(self.style.SUCCESS(
            f"Données de démonstration chargées : {Aircraft.objects.exclude(status='retired').count()} aéronefs (+ 1 retiré), "
            f"{MaintenanceTask.objects.count()} tâches, {Component.objects.count()} composants. "
            f"Comptes : {', '.join(a[0] for a in DEMO_ACCOUNTS)} – mot de passe {DEMO_PASSWORD}"
        ))

    @transaction.atomic
    def _load(self):
        for step in (self.users, self.stores, self.types_and_parts, self.staff, self.programme, self.fleet, self.utilisation,
                     self.directives, self.history, self.logistics, self.workpackages, self.quality_and_purchasing):
            step()

    # ------------------------------------------------------------------ utilisateurs
    def users(self):
        setup_roles()
        User = get_user_model()
        self.u = {}
        for username, label, group, superuser in DEMO_ACCOUNTS:
            user = User.objects.create_user(username=username, password=DEMO_PASSWORD, is_superuser=superuser, is_staff=superuser)
            if group:
                user.groups.add(Group.objects.get(name=group))
            self.u[username] = user
        set_current_user(self.u["admin"])

    def as_user(self, name):
        set_current_user(self.u[name])

    # ------------------------------------------------------------------ magasins
    def stores(self):
        self.main = StoreLocation.objects.create(code="MAG-PRINC", name="Magasin principal", station="Base principale")
        self.line = StoreLocation.objects.create(code="MAG-LIGNE", name="Magasin ligne / escale", station="Escale")
        self.quar = StoreLocation.objects.create(code="QUAR", name="Zone de quarantaine", station="Base principale", is_quarantine=True)

    # ------------------------------------------------------------------ types et P/N
    def types_and_parts(self):
        T = AircraftType.objects.create
        note = "Données de démonstration : intervalles et limites FICTIFS."
        self.t = {
            "H125": T(code="H125", manufacturer="Airbus Helicopters", model="H125 (AS350 B3e)", category="helicopter", engine_count=1,
                      engine_model="Safran Arriel 2D", cycle_label="Atterrissages", mtow_kg=2250, notes=note),
            "H135": T(code="H135", manufacturer="Airbus Helicopters", model="H135 (EC135 T3)", category="helicopter", engine_count=2,
                      engine_model="Safran Arrius 2B2", cycle_label="Atterrissages", mtow_kg=2980, notes=note),
            "H145": T(code="H145", manufacturer="Airbus Helicopters", model="H145 D3 (BK117 D-3)", category="helicopter", engine_count=2,
                      engine_model="Safran Arriel 2E", cycle_label="Atterrissages", mtow_kg=3800, notes=note),
            "H160": T(code="H160", manufacturer="Airbus Helicopters", model="H160", category="helicopter", engine_count=2,
                      engine_model="Safran Arrano 1A", cycle_label="Atterrissages", mtow_kg=6050, notes=note),
            "ATR72": T(code="ATR72-600", manufacturer="ATR", model="ATR 72-600", category="aeroplane", engine_count=2,
                       engine_model="Pratt & Whitney Canada PW127M", cycle_label="Cycles", mtow_kg=23000, notes=note),
        }

        def pn(code, desc, mfr, ata, types, **kw):
            p = PartNumber.objects.create(pn=code, description=desc, manufacturer=mfr, ata=ata, **kw)
            p.applicable_types.set([self.t[x] for x in types])
            return p

        S = dict(is_serialized=True, is_rotable=True)
        self.pn = {
            # H125
            "ENG_2D": pn("DEMO-ARR2D-0001", "Moteur Arriel 2D", "Safran Helicopter Engines", "72", ["H125"], tbo_fh=D("4000"), **S),
            "MGB_125": pn("DEMO-350MGB-01", "Boîte de transmission principale (BTP)", "Airbus Helicopters", "63", ["H125"], tbo_fh=D("3000"), tbo_days=15 * 365, **S),
            "TGB_125": pn("DEMO-350TGB-01", "Boîte de transmission arrière (BTA)", "Airbus Helicopters", "65", ["H125"], tbo_fh=D("3500"), **S),
            "STAR_125": pn("DEMO-350STR-01", "Étoile de moyeu rotor principal (Starflex)", "Airbus Helicopters", "62", ["H125"], is_llp=True, life_limit_fh=D("5000"), life_limit_fc=20000, **S),
            "MRB_125": pn("DEMO-350MRB-01", "Pale de rotor principal", "Airbus Helicopters", "62", ["H125"], is_llp=True, life_limit_fh=D("20000"), **S),
            "SG": pn("DEMO-SG-150", "Démarreur-génératrice", "Safran Electrical", "24", ["H125", "H135"], **S),
            # H135
            "ENG_2B2": pn("DEMO-ARS2B2-01", "Moteur Arrius 2B2", "Safran Helicopter Engines", "72", ["H135"], tbo_fh=D("3500"), **S),
            "MGB_135": pn("DEMO-135MGB-01", "BTP H135", "Airbus Helicopters", "63", ["H135"], tbo_fh=D("3000"), **S),
            "MRH_135": pn("DEMO-135MRH-01", "Moyeu rotor principal (bearingless)", "Airbus Helicopters", "62", ["H135"], is_llp=True, life_limit_fh=D("10000"), life_limit_fc=7000, **S),
            "FEN_135": pn("DEMO-135FEN-01", "Boîte Fenestron", "Airbus Helicopters", "65", ["H135"], tbo_fh=D("3000"), **S),
            # H145
            "ENG_2E": pn("DEMO-ARR2E-01", "Moteur Arriel 2E", "Safran Helicopter Engines", "72", ["H145"], tbo_fh=D("4000"), **S),
            "MGB_145": pn("DEMO-145MGB-01", "BTP H145", "Airbus Helicopters", "63", ["H145"], tbo_fh=D("3500"), **S),
            "MRH_145": pn("DEMO-145MRH-01", "Moyeu rotor principal H145", "Airbus Helicopters", "62", ["H145"], is_llp=True, life_limit_fh=D("12000"), life_limit_fc=15000, **S),
            "FEN_145": pn("DEMO-145FEN-01", "Boîte Fenestron H145", "Airbus Helicopters", "65", ["H145"], tbo_fh=D("3200"), **S),
            # H160
            "ENG_ARR": pn("DEMO-ARRANO-01", "Moteur Arrano 1A", "Safran Helicopter Engines", "72", ["H160"], tbo_fh=D("5000"), **S),
            "MGB_160": pn("DEMO-160MGB-01", "BTP H160", "Airbus Helicopters", "63", ["H160"], tbo_fh=D("4000"), **S),
            # ATR
            "ENG_PW": pn("DEMO-PW127M-01", "Moteur PW127M", "Pratt & Whitney Canada", "72", ["ATR72"], **S),
            "MLG_ATR": pn("DEMO-ATRMLG-01", "Atterrisseur principal", "Safran Landing Systems", "32", ["ATR72"], is_llp=True, life_limit_fc=60000, **S),
            "PROP_ATR": pn("DEMO-568F-01", "Hélice", "Collins Aerospace", "61", ["ATR72"], tbo_fh=D("10000"), **S),
            # Consommables (non sérialisés)
            "OIL": pn("DEMO-OIL-T2", "Huile turbine type II (bidon 1 L)", "Fournisseur huiles", "79", [], unit="L", shelf_life_controlled=True, category="consumable", specification="MIL-PRF-23699 (DEMO)"),
            "GREASE": pn("DEMO-GRS-01", "Graisse aéronautique (cartouche)", "Fournisseur graisses", "12", [], unit="EA", shelf_life_controlled=True, category="consumable"),
            "ORING": pn("DEMO-ORING-12", "Joint torique Ø12", "Fournisseur joints", "20", [], unit="EA", shelf_life_controlled=True, category="standard_part", specification="AS568-012 (DEMO)"),
            "LOCKWIRE": pn("DEMO-LW-032", "Fil à freiner 0,032\" (bobine)", "Fournisseur standard parts", "20", [], unit="EA", category="raw_material", specification="MS20995C32 (DEMO)"),
            "FILTER_125": pn("DEMO-350FLT-01", "Filtre à huile moteur H125", "Airbus Helicopters", "79", ["H125"], unit="EA"),
            "CHIP": pn("DEMO-CHIP-01", "Bouchon magnétique (détecteur de limaille)", "Airbus Helicopters", "63", ["H125", "H135", "H145"], unit="EA"),
        }

    # ------------------------------------------------------------------ personnel
    def staff(self):
        types = list(self.t.values())
        helis = [self.t[x] for x in ("H125", "H135", "H145", "H160")]
        today = self.today
        start = today - timedelta(days=400)

        def person(username, emp, first, last, role, stamp="", lic="", cats="", lic_exp=None):
            return Staff.objects.create(user=self.u.get(username), employee_number=emp, first_name=first, last_name=last, role=role,
                                        stamp=stamp, licence_number=lic, licence_categories=cats, licence_expiry=lic_exp)

        self.s = {
            "meca": person("meca", "M001", "Lucas", "Martin", "mechanic", "LM1"),
            "b1": person("b1", "M002", "Claire", "Dubois", "certifying", "CD2", "FR.66.DEMO.0002", "B1.3, B1.1", today + timedelta(days=900)),
            "b2": person("b2", "M003", "Karim", "Benali", "certifying", "KB3", "FR.66.DEMO.0003", "B2", today + timedelta(days=700)),
            "certc": person("certc", "M004", "Sophie", "Lambert", "inspector", "SL4", "FR.66.DEMO.0004", "C, B1.3", today + timedelta(days=1200)),
            "camo": person("camo", "C001", "Julien", "Moreau", "camo"),
            "planif": person("planif", "P001", "Nadia", "Roux", "planner"),
            "magasin": person("magasin", "S001", "Thomas", "Petit", "storekeeper"),
            "qualite": person("qualite", "Q001", "Isabelle", "Garnier", "manager"),
        }
        n = 1

        def auth(staff, t, cat, cert, until_days=700):
            nonlocal n
            Authorization.objects.create(staff=staff, number=f"AUT-{n:03d}", aircraft_type=t, category=cat, certifying=cert,
                                         valid_from=start, valid_until=today + timedelta(days=until_days),
                                         scope="Entretien en ligne et en base" if cert else "Exécution sous supervision")
            n += 1

        for t in helis:
            auth(self.s["meca"], t, "MECH", False)
            auth(self.s["b1"], t, "B1", True, 700 if t.code != "H160" else 45)  # une autorisation expire bientôt
            auth(self.s["b2"], t, "B2", True)
            auth(self.s["certc"], t, "C", True)
        auth(self.s["b1"], self.t["ATR72"], "B1", True)
        auth(self.s["certc"], self.t["ATR72"], "C", True)
        for st in (self.s["meca"], self.s["b1"], self.s["b2"], self.s["certc"]):
            Qualification.objects.create(staff=st, category="human_factors", name="Facteurs humains (recyclage)", obtained=today - timedelta(days=300), expiry=today + timedelta(days=430))
            Qualification.objects.create(staff=st, category="continuation", name="Formation continue 145.A.35", obtained=today - timedelta(days=200), expiry=today + timedelta(days=530))
            Qualification.objects.create(staff=st, category="ewis", name="EWIS", obtained=today - timedelta(days=500), expiry=today + timedelta(days=230))
            # Expérience antérieure à AHMIS (récence 145.A.35 : 6 mois sur 2 ans)
            ExperienceRecord.objects.create(staff=st, start=today - timedelta(days=700), end=today - timedelta(days=62),
                                            organisation="Organisme Part-145 de démonstration", description="Entretien en ligne et en base hélicoptères",
                                            evidence="Carnet de travaux")
        Qualification.objects.create(staff=self.s["meca"], category="safety", name="Sûreté / zones réservées", obtained=today - timedelta(days=800), expiry=today - timedelta(days=5))
        # Ancien salarié : dossier conservé 3 ans après le départ (145.A.35(j)) -> échu
        Staff.objects.create(employee_number="ANC-001", first_name="Paul", last_name="ANCIEN", role="certifying", active=False,
                             licence_number="FR.66.0099", licence_categories="B1.3", left_on=today - timedelta(days=4 * 365))

    # ------------------------------------------------------------------ programme d'entretien
    def programme(self):
        self.tasks = {}

        def task(t, ref, title, **kw):
            parts = kw.pop("parts", [])
            mt = MaintenanceTask.objects.create(aircraft_type=self.t[t], reference=ref, title=title, amp_revision="DEMO rév. 3", **kw)
            for p, q in parts:
                TaskRequiredPart.objects.create(task=mt, part_number=self.pn[p], quantity=D(str(q)))
            self.tasks[(t, ref)] = mt
            return mt

        STEPS_100 = "\n".join([
            "Ouvrir les capotages et trappes d'accès de la zone moteur / BTP",
            "Inspection visuelle générale de la zone de transmission et des fixations",
            "Relever et nettoyer les bouchons magnétiques (BTP, BTA, moteur)",
            "Contrôler niveaux d'huile et absence de fuite",
            "Inspection des commandes de vol et des biellettes",
            "Refermer et freiner, contrôle d'absence d'objet étranger (FOD)",
        ])
        for code in ("H125", "H135", "H145", "H160"):
            p = code.replace("H", "")
            task(code, f"{p}-05-100", "Visite 100 h / 12 mois", source="AMP", task_type="INSP", ata="05",
                 interval_fh=D("100"), interval_days=365, tolerance_fh=D("10"), tolerance_days=30, estimated_mh=D("8"),
                 zone="Cellule complète", skill="B1", steps=STEPS_100, parts=[("OIL", 2), ("CHIP", 1), ("LOCKWIRE", 1)])
            task(code, f"{p}-05-600", "Visite 600 h / 24 mois", source="AMP", task_type="INSP", ata="05",
                 interval_fh=D("600"), interval_days=730, tolerance_fh=D("30"), tolerance_days=30, estimated_mh=D("40"),
                 zone="Cellule complète", skill="B1", requires_independent_inspection=True,
                 steps=STEPS_100 + "\nInspection détaillée de la structure (zones critiques)\nContrôle des jeux de la tête rotor\nEssais moteur et contrôle des vibrations",
                 parts=[("OIL", 4), ("GREASE", 2), ("ORING", 6)])
            task(code, f"{p}-62-050", "Lubrification de la tête rotor principal", source="AMP", task_type="LUB", ata="62",
                 interval_fh=D("50"), tolerance_fh=D("5"), estimated_mh=D("1.5"), skill="B1", parts=[("GREASE", 1)],
                 steps="Nettoyer les graisseurs\nGraisser selon le schéma de lubrification\nEssuyer l'excès de graisse")
            task(code, f"{p}-63-200", "Prélèvement huile BTP – analyse spectrométrique", source="AMP", task_type="SVC", ata="63",
                 interval_fh=D("200"), interval_days=182, tolerance_fh=D("20"), estimated_mh=D("0.5"), skill="B1",
                 steps="Prélever l'échantillon à chaud\nÉtiqueter et expédier au laboratoire")
            task(code, f"{p}-08-001", "Pesée et centrage", source="OPS", task_type="SVC", ata="08", interval_days=4 * 365, estimated_mh=D("4"), skill="B1")
            task(code, f"{p}-24-365", "Contrôle capacité batterie", source="AMP", task_type="FNC", ata="24", interval_days=365, tolerance_days=15,
                 estimated_mh=D("1"), skill="B2", steps="Déposer la batterie\nTest de capacité au banc\nReposer et contrôler le fonctionnement")
        # Tâches suivies sur composant (compteurs du composant)
        task("H125", "125-72-500", "Contrôle boroscopique moteur Arriel 2D", source="AMP", task_type="DET", ata="72",
             part_number=self.pn["ENG_2D"], interval_fh=D("500"), tolerance_fh=D("25"), estimated_mh=D("3"), skill="B1",
             steps="Déposer les bouchons d'inspection\nInspection boroscopique du générateur de gaz\nEnregistrer les constatations et images")
        task("H145", "145-72-500", "Contrôle boroscopique moteurs Arriel 2E", source="AMP", task_type="DET", ata="72",
             part_number=self.pn["ENG_2E"], interval_fh=D("500"), tolerance_fh=D("25"), estimated_mh=D("3"), skill="B1")
        # Limitation de navigabilité (ALS)
        task("H135", "135-04-001", "Inspection détaillée des ferrures de fixation BTP (ALS)", source="ALS", task_type="DET", ata="04",
             interval_fh=D("1500"), interval_days=3 * 365, estimated_mh=D("6"), skill="B1", requires_independent_inspection=True)
        # ATR 72-600
        task("ATR72", "ATR-05-A", "Visite A (500 FH)", source="AMP", task_type="INSP", ata="05", interval_fh=D("500"), tolerance_fh=D("50"),
             estimated_mh=D("30"), skill="B1", parts=[("OIL", 6)], steps="Tour avion\nInspection trains\nContrôle niveaux\nLecture des messages de maintenance")
        task("ATR72", "ATR-05-C", "Visite C (24 mois)", source="AMP", task_type="INSP", ata="05", interval_days=730, tolerance_days=30,
             estimated_mh=D("600"), skill="C")
        task("ATR72", "ATR-32-001", "Inspection détaillée du caisson de train", source="AMP", task_type="DET", ata="32",
             interval_fc=6000, interval_days=6 * 365, estimated_mh=D("12"), skill="B1", requires_independent_inspection=True)
        task("ATR72", "ATR-26-001", "Pesée bouteilles extincteurs", source="AMP", task_type="SVC", ata="26", interval_days=365, estimated_mh=D("2"), skill="B1")

    # ------------------------------------------------------------------ flotte et configuration
    def fleet(self):
        today = self.today
        start = today - timedelta(days=HISTORY_DAYS)
        A = Aircraft.objects.create

        def ac(reg, t, msn, fab_years, fh, fc, base, op, dfh, dfc, arc_days, status="active"):
            return A(registration=reg, aircraft_type=self.t[t], msn=msn, manufacture_date=today - timedelta(days=int(fab_years * 365)),
                     entry_into_service=today - timedelta(days=int(fab_years * 365) - 40), total_fh=D(fh), total_fc=fc,
                     counters_date=start, base=base, operator=op, owner="Société de démonstration SAS",
                     planned_daily_fh=D(dfh), planned_daily_fc=D(dfc), status=status, cofa_number=f"CDN-{msn}",
                     arc_expiry=today + timedelta(days=arc_days))

        self.ac = {
            "MA": ac("F-HDMA", "H125", "9101", 6, "2320.4", 6890, "Base Alpes", "Héli Montagne Démo", "1.6", "4.5", 190),
            "MB": ac("F-HDMB", "H125", "9102", 9, "3810.0", 11450, "Base Alpes", "Héli Montagne Démo", "1.4", "4.0", 75),
            "MC": ac("F-HDMC", "H135", "2201", 7, "4050.7", 6420, "Base hospitalière Nord", "SAMU Démo (HEMS)", "2.2", "5.0", 240),
            "MD": ac("F-HDMD", "H145", "21101", 4, "2890.2", 4870, "Base hospitalière Sud", "SAMU Démo (HEMS)", "2.0", "4.5", 160, "maintenance"),
            "ME": ac("F-HDME", "H160", "1601", 1.5, "640.0", 1280, "Base offshore", "Offshore Démo", "2.5", "3.0", 20),
            "MF": ac("F-HDMF", "ATR72", "1801", 5, "14250.0", 15980, "Base régionale", "Régional Démo", "6.5", "7.0", 300),
        }
        self.cert_n = 1000

        def comp(pkey, sn, aircraft, position, tsn, csn, tso=None, cso=None, fab_years=5, overhaul_years=None):
            c = Component.objects.create(
                part_number=self.pn[pkey], serial_number=sn, condition="overhauled" if tso is not None else "new",
                manufacture_date=today - timedelta(days=int(fab_years * 365)),
                last_overhaul_date=today - timedelta(days=int(overhaul_years * 365)) if overhaul_years else None,
                tsn_fh=D(tsn), csn=csn, tso_fh=D(tso if tso is not None else tsn), cso=cso if cso is not None else csn,
                status="serviceable", location=self.main,
            )
            self.certificate(c)
            if aircraft:
                install_component(c, aircraft, position, aircraft.entry_into_service or start, force=True)
            return c

        MA, MB, MC, MD, ME, MF = (self.ac[k] for k in ("MA", "MB", "MC", "MD", "ME", "MF"))
        # F-HDMA : BTP proche de son TBO (≈ 60 FH restantes à la fin de l'historique)
        comp("ENG_2D", "DEMO-E21001", MA, "MOT", "2320.4", 6890, "1850.0", 5400, overhaul_years=1)
        comp("MGB_125", "DEMO-M3501", MA, "BTP", "2880.0", 8100, "2865.0", 8050, overhaul_years=5)
        comp("TGB_125", "DEMO-T3501", MA, "BTA", "2320.4", 6890)
        comp("STAR_125", "DEMO-S3501", MA, "MRH", "2320.4", 6890)
        for i in (1, 2, 3):
            comp("MRB_125", f"DEMO-B350{i}", MA, f"PALE {i}", "2320.4", 6890)
        comp("SG", "DEMO-G1501", MA, "DEM-GEN", "900.0", 2600)
        # F-HDMB : Starflex proche de sa limite de vie
        comp("ENG_2D", "DEMO-E21002", MB, "MOT", "3810.0", 11450, "3100.0", 9300, overhaul_years=2)
        comp("MGB_125", "DEMO-M3502", MB, "BTP", "3810.0", 11450, "820.0", 2400, overhaul_years=1.5)
        comp("TGB_125", "DEMO-T3502", MB, "BTA", "3810.0", 11450, "310.0", 900, overhaul_years=0.5)
        comp("STAR_125", "DEMO-S3502", MB, "MRH", "4880.0", 15100)
        for i in (1, 2, 3):
            comp("MRB_125", f"DEMO-B351{i}", MB, f"PALE {i}", "3810.0", 11450)
        # F-HDMC (H135 HEMS) : moyeu proche limite cycles
        comp("ENG_2B2", "DEMO-A2201", MC, "MOT 1", "4050.7", 6420, "2600.0", 4100, overhaul_years=3)
        comp("ENG_2B2", "DEMO-A2202", MC, "MOT 2", "3200.0", 5100, "1900.0", 3000, overhaul_years=2)
        comp("MGB_135", "DEMO-M1351", MC, "BTP", "4050.7", 6420, "2100.0", 3300, overhaul_years=3)
        comp("MRH_135", "DEMO-H1351", MC, "MRH", "4050.7", 6500)
        comp("FEN_135", "DEMO-F1351", MC, "BTA", "4050.7", 6420, "1200.0", 1900, overhaul_years=2)
        # F-HDMD (H145) – en visite
        e1 = comp("ENG_2E", "DEMO-E2E01", MD, "MOT 1", "2890.2", 4870)
        comp("ENG_2E", "DEMO-E2E02", MD, "MOT 2", "2890.2", 4870)
        comp("MGB_145", "DEMO-M1451", MD, "BTP", "2890.2", 4870)
        comp("MRH_145", "DEMO-H1451", MD, "MRH", "2890.2", 4870)
        self.fen_145 = comp("FEN_145", "DEMO-F1451", MD, "BTA", "2890.2", 4870)
        self.eng_145 = e1
        # F-HDME (H160)
        comp("ENG_ARR", "DEMO-R1601", ME, "MOT 1", "640.0", 1280)
        comp("ENG_ARR", "DEMO-R1602", ME, "MOT 2", "640.0", 1280)
        comp("MGB_160", "DEMO-M1601", ME, "BTP", "640.0", 1280)
        # F-HDMF (ATR)
        comp("ENG_PW", "DEMO-PW0001", MF, "MOT 1", "14250.0", 15980, "5200.0", 5600, overhaul_years=3)
        comp("ENG_PW", "DEMO-PW0002", MF, "MOT 2", "12900.0", 14100, "3800.0", 4100, overhaul_years=2)
        comp("MLG_ATR", "DEMO-LG0001", MF, "TRAIN G", "14250.0", 15980)
        comp("MLG_ATR", "DEMO-LG0002", MF, "TRAIN D", "14250.0", 15980)
        comp("PROP_ATR", "DEMO-PR0001", MF, "HEL 1", "14250.0", 15980, "9300.0", 10300, overhaul_years=4)
        comp("PROP_ATR", "DEMO-PR0002", MF, "HEL 2", "14250.0", 15980, "4100.0", 4500, overhaul_years=2)

        # Aéronef retiré du service (hors self.ac : exclu des échéances) : conservation 12 mois après retrait -> échue
        from apps.fleet.models import UtilisationRecord

        z = Aircraft.objects.create(registration="F-HDMZ", aircraft_type=self.t["H125"], msn="8801", status="retired",
                                    manufacture_date=today - timedelta(days=22 * 365), total_fh=D("14210.5"), total_fc=40210,
                                    counters_date=today - timedelta(days=600), withdrawn_on=today - timedelta(days=600),
                                    owner="Société de démonstration SAS", notes="Retiré du service (accident sans blessé), cellule vendue pour pièces.")
        UtilisationRecord.objects.create(aircraft=z, date=today - timedelta(days=610), fh=D("1.2"), fc=3, source="manual",
                                         fh_after=D("14210.5"), fc_after=40210, reference="TL-8801-998")

    def certificate(self, target, valid=True, cert_type="easa_form1", work_status=None):
        self.cert_n += 1
        is_comp = isinstance(target, Component)
        return ReleaseCertificate.objects.create(
            cert_type=cert_type, tracking_number=f"DEMO-F1-{self.cert_n}", issuer="Atelier agréé de démonstration",
            issuer_approval="FR.145.DEMO-X", issue_date=self.today - timedelta(days=random.randint(90, 900)),
            work_status=work_status or (target.condition if is_comp and target.condition in ("new", "overhauled", "repaired", "inspected") else "new"),
            part_number=target.part_number, serial_or_batch=target.serial_number if is_comp else target.batch,
            quantity=D("1") if is_comp else target.quantity,
            component=target if is_comp else None, stock_item=None if is_comp else target, is_valid=valid,
            rejection_reason="" if valid else "Certificat non conforme",
        )

    # ------------------------------------------------------------------ utilisation (60 derniers jours)
    def utilisation(self):
        start = self.today - timedelta(days=HISTORY_DAYS)
        for ac in self.ac.values():
            for i in range(1, HISTORY_DAYS + 1):
                d = start + timedelta(days=i)
                if ac.registration == "F-HDMD" and d > self.today - timedelta(days=3):
                    continue  # en visite
                if random.random() < 0.25:
                    continue  # jour sans vol
                fh = (ac.planned_daily_fh * D(str(round(random.uniform(0.9, 1.6), 2)))).quantize(D("0.1"))
                fc = max(1, int(ac.planned_daily_fc * D(str(round(random.uniform(0.8, 1.5), 2)))))
                ac.record_utilisation(d, fh, fc, reference=f"CRM {ac.registration[-2:]}-{d:%m%d}")
            ac.refresh_from_db()

    # ------------------------------------------------------------------ consignes
    def directives(self):
        today = self.today
        self.as_user("camo")
        ad1 = Directive.objects.create(
            number="DEMO-AD-2026-0101", kind="AD", authority="EASA", title="BTP H125 – inspection répétitive des barres de suspension",
            effective_date=today - timedelta(days=200), is_recurring=True,
            applicability_text="Hélicoptères H125, tous numéros de série, équipés de BTP DEMO-350MGB-01 (exemple fictif).",
            required_action="Inspection détaillée des barres de suspension BTP dans les 50 FH puis toutes les 110 FH.",
        )
        ad1.aircraft_types.set([self.t["H125"]])
        t1 = MaintenanceTask.objects.create(
            aircraft_type=self.t["H125"], reference="DEMO-AD-2026-0101", title="Inspection des barres de suspension BTP (AD)", source="AD",
            directive=ad1, task_type="DET", ata="63", threshold_fh=D("50"), interval_fh=D("110"), estimated_mh=D("2"), skill="B1",
            requires_independent_inspection=True, amp_revision="DEMO rév. 3",
            steps="Déposer les capotages BTP\nInspection détaillée des barres et ferrures (fissures, corrosion)\nRelever les couples de serrage\nReposer les capotages",
        )
        self.tasks[("H125", "AD0101")] = t1
        for ac in (self.ac["MA"], self.ac["MB"]):
            DirectiveApplicability.objects.create(directive=ad1, aircraft=ac, status="recurring" if ac.registration == "F-HDMA" else "open",
                                                  justification="Applicable : BTP du P/N concerné installée.", reviewed_by="Julien MOREAU", reviewed_on=today - timedelta(days=190))
        asb = Directive.objects.create(
            number="DEMO-ASB-135-65-001", kind="ASB", authority="OEM", title="H135 – contrôle ponctuel de la biellette de commande rotor arrière",
            effective_date=today - timedelta(days=20), is_recurring=False,
            applicability_text="H135 dont le moyeu rotor principal est DEMO-135MRH-01 (exemple fictif).",
            required_action="Contrôle unique dans les 100 FH ou 3 mois.",
        )
        asb.aircraft_types.set([self.t["H135"]])
        MaintenanceTask.objects.create(aircraft_type=self.t["H135"], reference="DEMO-ASB-135-65-001", title="Contrôle biellette commande rotor arrière (ASB)",
                                       source="SB", directive=asb, task_type="DET", ata="67", threshold_fh=D("100"), threshold_days=90,
                                       estimated_mh=D("1.5"), skill="B1")
        DirectiveApplicability.objects.create(directive=asb, aircraft=self.ac["MC"], status="open", justification="Applicable – moyeu concerné installé.",
                                              reviewed_by="Julien MOREAU", reviewed_on=today - timedelta(days=15))
        ad3 = Directive.objects.create(
            number="DEMO-AD-2026-0177", kind="AD", authority="EASA", title="ATR 72 – inspection des ferrures de volet",
            effective_date=today + timedelta(days=10), applicability_text="ATR 72-600 MSN 1700 à 1850 (exemple fictif).",
            required_action="Inspection détaillée avant 3000 FC après l'entrée en vigueur.",
        )
        ad3.aircraft_types.set([self.t["ATR72"]])
        DirectiveApplicability.objects.create(directive=ad3, aircraft=self.ac["MF"], status="to_assess")
        sb = Directive.objects.create(
            number="DEMO-SB-145-24-010", kind="SB", authority="OEM", title="H145 – amélioration du faisceau électrique éclairage cabine",
            effective_date=today - timedelta(days=60), applicability_text="H145 D3 jusqu'au MSN 21200 (exemple fictif).",
            required_action="Modification optionnelle recommandée.",
        )
        sb.aircraft_types.set([self.t["H145"]])
        DirectiveApplicability.objects.create(directive=sb, aircraft=self.ac["MD"], status="to_assess")
        ad_h160 = Directive.objects.create(
            number="DEMO-AD-2025-0333", kind="AD", authority="EASA", title="H160 – logiciel du calculateur de vol",
            effective_date=today - timedelta(days=300), applicability_text="H160 tous MSN (exemple fictif).",
            required_action="Mise à jour logicielle (une fois).",
        )
        ad_h160.aircraft_types.set([self.t["H160"]])
        DirectiveApplicability.objects.create(directive=ad_h160, aircraft=self.ac["ME"], status="complied", compliance_date=today - timedelta(days=250),
                                              compliance_fh=D("420"), compliance_fc=840, justification="Appliquée à la livraison (CRS constructeur).",
                                              reviewed_by="Julien MOREAU", reviewed_on=today - timedelta(days=249))

    # ------------------------------------------------------------------ historique des réalisations
    def history(self):
        self.as_user("camo")
        today = self.today

        def done(ac_key, t, ref, fh_ago, days_ago, component=None):
            ac = self.ac[ac_key]
            task = self.tasks[(t, ref)]
            fh = ac.total_fh - D(str(fh_ago))
            rate_fc = ac.planned_daily_fc / ac.planned_daily_fh if ac.planned_daily_fh else D("1")
            fc = max(0, ac.total_fc - int(D(str(fh_ago)) * rate_fc))
            TaskAccomplishment.objects.create(
                task=task, aircraft=ac, component=component, date=today - timedelta(days=days_ago), fh=fh, fc=fc,
                comp_fh=(component.tsn_fh - D(str(fh_ago))) if component else None,
                comp_fc=(component.csn - int(D(str(fh_ago)) * rate_fc)) if component else None,
                source="initial", reference="Reprise historique (logbook)", certified_by="Reprise de données",
            )

        prog = {
            # (fh_ago, days_ago) par tâche et par aéronef -> statuts variés
            "MA": {"05-100": (88, 300), "05-600": (420, 500), "62-050": (41, 30), "63-200": (150, 120), "08-001": (900, 1000), "24-365": (300, 340)},
            "MB": {"05-100": (106, 200), "05-600": (300, 300), "62-050": (20, 15), "63-200": (90, 70), "08-001": (1500, 1300), "24-365": (200, 200)},
            "MC": {"05-100": (60, 40), "05-600": (560, 330), "62-050": (55, 25), "63-200": (120, 60), "08-001": (1200, 900), "24-365": (500, 380)},
            "MD": {"05-100": (97, 70), "05-600": (590, 400), "62-050": (48, 22), "63-200": (190, 100), "08-001": (800, 600), "24-365": (400, 330)},
            "ME": {"05-100": (30, 15), "05-600": (330, 150), "62-050": (25, 10), "63-200": (110, 50), "08-001": (640, 500), "24-365": (600, 300)},
        }
        for key, rows in prog.items():
            code = self.ac[key].aircraft_type.code
            p = code.replace("H", "")
            for suffix, (fh_ago, days_ago) in rows.items():
                done(key, code, f"{p}-{suffix}", fh_ago, days_ago)
        ma_eng = self.ac["MA"].components.get(position="MOT")
        done("MA", "H125", "125-72-500", 470, 280, component=ma_eng)
        done("MB", "H125", "125-72-500", 210, 140, component=self.ac["MB"].components.get(position="MOT"))
        done("MD", "H145", "145-72-500", 300, 150, component=self.eng_145)
        done("MD", "H145", "145-72-500", 520, 260, component=self.ac["MD"].components.get(position="MOT 2"))
        done("MC", "H135", "135-04-001", 1200, 800)
        done("MA", "H125", "AD0101", 95, 60)
        # F-HDMB : AD jamais réalisée -> seuil 50 FH depuis l'entrée en vigueur (dépassée)
        done("MF", "ATR72", "ATR-05-A", 420, 70)
        done("MF", "ATR72", "ATR-05-C", 3000, 700)
        done("MF", "ATR72", "ATR-32-001", 2000, 400)
        done("MF", "ATR72", "ATR-26-001", 2500, 400)  # dépassée de plus de la tolérance (aucune)
        # ARC
        for key, ac in self.ac.items():
            AirworthinessReview.objects.create(
                aircraft=ac, review_type="issue", reference=f"ARC-DEMO-{ac.msn}", review_date=ac.arc_expiry - timedelta(days=365),
                expiry_date=ac.arc_expiry, reviewer="Julien MOREAU (ARS)", physical_survey=True,
            )
        # Revue du programme d'entretien (M.A.302(g)) : un cas de chaque état
        def amp(t, days_ago, **kw):
            AmpReview.objects.create(aircraft_type=self.t[t], review_date=self.today - timedelta(days=days_ago),
                                     amp_reference=f"AMP-{t}-DEMO", revision_before="DEMO rév. 3", reviewer="Julien MOREAU (CAMO)",
                                     reliability_reviewed=True, instructions_reviewed=True, **kw)

        amp("H125", 400, findings="Revue initiale.")
        amp("H125", 40, outcome="amended", revision_after="DEMO rév. 4", approval_type="indirect",
            approval_reference="PAI-2026-014", approval_date=self.today - timedelta(days=35),
            findings="Défauts répétitifs ATA 63 (3 en 12 mois) ; révision MSM 2026-01 intégrée.",
            changes="Inspection BTP réduite à 300 FH ; ajout des ICA de la modification MOD-0001.")
        amp("H135", 350, findings="Programme efficace, aucun défaut répétitif.")       # à planifier sous 30 j
        amp("H145", 120, findings="Aucun changement nécessaire.")
        amp("H160", 395, findings="Revue initiale.")                                  # dépassée
        # ATR72 : aucune revue enregistrée -> alerte

    # ------------------------------------------------------------------ logistique
    def logistics(self):
        self.as_user("magasin")
        today = self.today

        def stock(pkey, batch, qty, loc, exp_days=None, mini=0, status="serviceable"):
            s = StockItem.objects.create(part_number=self.pn[pkey], batch=batch, location=loc, quantity=D(str(qty)), min_quantity=D(str(mini)),
                                         shelf_life_expiry=today + timedelta(days=exp_days) if exp_days is not None else None,
                                         status=status, supplier="Distributeur agréé démo")
            self.certificate(s, cert_type="easa_form1" if s.part_number.requires_release_certificate else "coc")
            StockMovement.objects.create(stock_item=s, kind="receipt", quantity=D(str(qty)), note="Stock initial")
            return s

        self.oil = stock("OIL", "LOT-OIL-2611", 48, self.main, 500, 20)
        stock("OIL", "LOT-OIL-2502", 6, self.line, -12, 0)  # périmé
        self.grease = stock("GREASE", "LOT-GR-118", 12, self.main, 300, 5)
        stock("ORING", "LOT-OR-077", 3, self.main, 900, 10)  # sous le stock mini
        stock("LOCKWIRE", "LOT-LW-001", 20, self.main, None, 5)
        stock("FILTER_125", "LOT-FL-44", 8, self.main, None, 2)
        stock("CHIP", "LOT-CH-09", 6, self.main, None, 2)
        # Pièce non récupérable : Starflex en butée de vie, rebutée et mutilée (145.A.42(d))
        Component.objects.create(
            part_number=self.pn["STAR_125"], serial_number="DEMO-S3399", status="scrapped", condition="used",
            manufacture_date=today - timedelta(days=12 * 365), tsn_fh=D("5000.0"), csn=14210, tso_fh=D("5000.0"), cso=14210,
            location=StoreLocation.objects.filter(is_quarantine=True).first(), status_reason="Rebuté : Limite de vie atteinte (LLP)",
            scrapped_on=today - timedelta(days=45), scrap_reason="life_limit", mutilation_method="Découpe en trois parties à la scie",
            mutilation_witness="Thomas PETIT (magasin) et Isabelle GARNIER (qualité)", scrap_reference="DESTR-2026-007")

        # Rechanges sérialisés
        def spare(pkey, sn, status="serviceable", loc=None, valid_cert=True, tsn="0", csn=0, reason="", condition="new"):
            c = Component.objects.create(part_number=self.pn[pkey], serial_number=sn, status=status, location=loc or self.main, condition=condition,
                                         manufacture_date=today - timedelta(days=400), tsn_fh=D(tsn), csn=csn, tso_fh=D("0"), cso=0, status_reason=reason)
            self.certificate(c, valid=valid_cert)
            return c

        self.spare_fen = spare("FEN_145", "DEMO-F1459", tsn="1450.0", csn=2300, condition="overhauled")
        spare("SG", "DEMO-G1599", tsn="300.0", csn=800, condition="repaired")
        spare("TGB_125", "DEMO-T3599", condition="overhauled", tsn="2100.0", csn=6000)
        spare("MRB_125", "DEMO-B3599")
        spare("SG", "DEMO-G1666", status="quarantine", loc=self.quar, valid_cert=False, tsn="1200.0", csn=3500,
              reason="Pièce suspecte (SUP) : plaque d'identification non conforme, certificat douteux")
        spare("ENG_2D", "DEMO-E21099", status="unserviceable", loc=self.quar, tsn="5100.0", csn=15000,
              reason="Déposé pour dépassement de température (rapport moteur)", condition="used")

        # Outillage
        def tool(ref, desc, interval, last_days_ago, sn):
            t = Tool.objects.create(reference=ref, description=desc, serial_number=sn, location=self.main, calibration_required=interval is not None,
                                    calibration_interval_days=interval)
            if interval:
                ToolCalibration.objects.create(tool=t, date=today - timedelta(days=last_days_ago), provider="Laboratoire de métrologie démo",
                                               certificate_ref=f"MET-{ref}")
            return t

        tool("CLE-DYN-01", "Clé dynamométrique 5–25 N·m", 365, 120, "TW-5512")
        tool("CLE-DYN-02", "Clé dynamométrique 20–100 N·m", 365, 380, "TW-7781")  # étalonnage échu
        tool("BORO-01", "Boroscope vidéo", 730, 200, "BS-3301")
        tool("TENS-01", "Tensiomètre câbles de commande", 365, 30, "TN-0042")
        tool("PESE-01", "Kit de pesée hélicoptère", 365, 300, "WK-1200")
        tool("LEV-01", "Barre de levage BTP", None, 0, "LB-0001")

    # ------------------------------------------------------------------ work packages et task cards
    def workpackages(self):
        today = self.today
        # WP clôturé sur F-HDMA (visite 50 h antérieure, CRS signé)
        self.as_user("planif")
        ma = self.ac["MA"]
        wp0 = WorkPackage.objects.create(aircraft=ma, title="Lubrification et contrôles", check_type="line", station="Base Alpes",
                                         planned_start=today - timedelta(days=2), planned_end=today - timedelta(days=2), status="planned")
        p145.add_due_items_to_wp(wp0, [f"task:{self.tasks[('H125', '125-62-050')].pk}:0"])
        card0 = wp0.task_cards.first()
        self.as_user("b1")
        p145.start_card(card0, self.u["b1"])
        for st in card0.steps.all():
            p145.sign_step(st, self.u["b1"])
        p145.perform_card(card0, self.u["b1"], "Lubrification réalisée selon schéma. RAS.", D("1.2"))
        p145.issue_crs(wp0, self.u["b1"])

        # WP en cours sur F-HDMD (H145) : visite 100 h + boroscopie + défaut
        md = self.ac["MD"]
        self.as_user("planif")
        wp = WorkPackage.objects.create(aircraft=md, title="Visite 100 h + boroscopie moteurs", check_type="periodic", station="Hangar Sud",
                                        planned_start=today - timedelta(days=2), planned_end=today + timedelta(days=2), status="planned",
                                        ordered_by="CAMO – Julien MOREAU", customer_order="CMD-DEMO-2026-118")
        keys = [f"task:{self.tasks[('H145', '145-05-100')].pk}:0", f"task:{self.tasks[('H145', '145-62-050')].pk}:0",
                f"task:{self.tasks[('H145', '145-72-500')].pk}:{self.eng_145.pk}", f"task:{self.tasks[('H145', '145-24-365')].pk}:0"]
        p145.add_due_items_to_wp(wp, keys)
        self.as_user("meca")
        defect = Defect.objects.create(aircraft=md, reported_by="Cdt de bord DEMO", source="techlog", techlog_ref="CRM MD-118", ata="65",
                                       description="Vibrations anormales ressenties au palonnier en stationnaire.")
        self.as_user("planif")
        p145.card_from_defect(wp, defect)
        cards = {c.task.reference if c.task else "DEF": c for c in wp.task_cards.all()}
        # 1) Lubrification : clôturée par le mécanicien (pas de contrôle indépendant)
        self.as_user("meca")
        c = cards["145-62-050"]
        p145.start_card(c, self.u["meca"])
        for st in c.steps.all():
            p145.sign_step(st, self.u["meca"])
        p145.perform_card(c, self.u["meca"], "Graissage effectué, excès essuyé.", D("1.0"))
        # 2) Visite 100 h : en cours, 3 étapes sur 6, demande de pièce délivrée, outil sorti
        c = cards["145-05-100"]
        p145.start_card(c, self.u["meca"])
        for st in list(c.steps.all())[:3]:
            p145.sign_step(st, self.u["meca"], measured_value="RAS")
        pr = PartRequest.objects.create(task_card=c, part_number=self.pn["OIL"], quantity=D("2"), priority="routine")
        self.as_user("magasin")
        pr.fulfil_with_stock(self.oil)
        self.as_user("meca")
        PartRequest.objects.create(task_card=c, part_number=self.pn["CHIP"], quantity=D("1"), priority="urgent", note="Joint du bouchon BTP abîmé")
        Tool.objects.get(reference="CLE-DYN-01").check_out(c, self.s["meca"])
        # 3) Boroscopie : exécutée par B1, en attente du contrôle indépendant
        self.as_user("b1")
        c = cards["145-72-500"]
        c.requires_independent_inspection = True
        c.save()
        p145.start_card(c, self.u["b1"])
        for st in c.steps.all():
            p145.sign_step(st, self.u["b1"])
        p145.perform_card(c, self.u["b1"], "Boroscopie générateur de gaz : aucune anomalie, images archivées.", D("2.5"))
        # 4) Défaut : réservation d'une boîte Fenestron de rechange pour la task card
        self.as_user("planif")
        pr2 = PartRequest.objects.create(task_card=cards["DEF"], part_number=self.pn["FEN_145"], quantity=D("1"), priority="aog")
        self.as_user("magasin")
        pr2.fulfil_with_component(self.spare_fen)

        # Défaut reporté sur F-HDMC (H135) cat. C
        self.as_user("b2")
        d2 = Defect.objects.create(aircraft=self.ac["MC"], reported_by="Pilote HEMS DEMO", source="techlog", techlog_ref="CRM MC-077", ata="33",
                                   description="Éclairage de lecture cabine arrière inopérant.")
        p145.defer_defect(d2, self.u["b2"], "MEL 33-20-01 (DEMO)", "C", procedure="Placard « INOP » apposé.")
        Defect.objects.create(aircraft=self.ac["MB"], reported_by="Pilote DEMO", source="techlog", techlog_ref="CRM MB-201", ata="25",
                              description="Fermeture de la porte coulissante gauche difficile.")

        # WP planifié sur F-HDMB (pour le tutoriel de planification)
        self.as_user("planif")
        WorkPackage.objects.create(aircraft=self.ac["MB"], title="Visite 100 h", check_type="periodic", station="Base Alpes",
                                   planned_start=today + timedelta(days=5), planned_end=today + timedelta(days=6), status="planned")
        self.occurrences(defect)
        self.transfers()
        set_current_user(None)

    # ------------------------------------------------------------------ transfert de dossier (M.A.307)
    def transfers(self):
        from django.core.files.base import ContentFile

        from apps.camo import dossier
        from apps.camo.models import TransferRecord

        self.as_user("camo")
        z = Aircraft.objects.get(registration="F-HDMZ")
        raw, digest, manifest = dossier.build_archive(z, self.u["camo"], recipient="Héli Pièces Démo (acquéreur)",
                                                      purpose="Vente de la cellule pour pièces")
        t = TransferRecord.objects.create(
            aircraft=z, direction="out", transfer_date=z.withdrawn_on + timedelta(days=20), counterparty="Héli Pièces Démo (acquéreur)",
            reason="Vente de la cellule pour pièces après retrait du service.", manifest=manifest, archive_sha256=digest,
            archive_size=len(raw), verification="Archive générée par AHMIS ; empreintes de chaque fichier dans manifest.json.",
            acknowledged_on=z.withdrawn_on + timedelta(days=24), acknowledged_by="Responsable technique, Héli Pièces Démo")
        t.archive.save(f"dossier-{z.registration}-{t.number}.zip", ContentFile(raw), save=True)

    # ------------------------------------------------------------------ comptes rendus d'événements (376/2014)
    def occurrences(self, vib_defect):
        from apps.safety.models import OccurrenceReport

        now = timezone.now()
        h = lambda n: now - timedelta(hours=n)  # noqa: E731
        self.as_user("meca")
        # À notifier : reste ~20 h sur les 72 h
        OccurrenceReport.objects.create(
            title="Vibrations palonnier en stationnaire", category="powerplant", severity="medium", phase="flight",
            occurred_at=h(54), aware_at=h(52), location="Base Côte", aircraft=vib_defect.aircraft, defect=vib_defect,
            description=vib_defect.description, immediate_actions="Aéronef immobilisé, recherche de panne ouverte (WP en cours).",
            reporter_name="Lucas MARTIN")
        self.as_user("qualite")
        # Notifié, suivi à 30 jours en retard
        OccurrenceReport.objects.create(
            title="Frein d'écrou non posé après dépose servocommande", category="maintenance_error", severity="high", phase="maintenance",
            occurred_at=h(24 * 41), aware_at=h(24 * 41 - 2), location="Hangar Base Alpes", aircraft=self.ac["MB"],
            description="Lors du contrôle indépendant, absence de freinage sur l'écrou de la biellette de commande de pas cyclique.",
            immediate_actions="Freinage posé et contrôlé, extension de l'inspection aux deux autres servocommandes.",
            reporter_name="Sophie LAMBERT", confidential=True, status="submitted", authority="DSAC / ECCAIRS 2",
            authority_reference="FR-2026-DEMO-0412", submitted_at=h(24 * 40), customer_notified=True)
        # Clôturé
        OccurrenceReport.objects.create(
            title="Pièce sans certificat libératoire reçue", category="suspected_unapproved_part", severity="medium", phase="storage",
            occurred_at=h(24 * 120), aware_at=h(24 * 120), location="Magasin principal",
            description="Roulement reçu avec un certificat de conformité fournisseur au lieu d'un EASA Form 1.",
            immediate_actions="Pièce mise en quarantaine, fournisseur contacté.", reporter_name="Thomas PETIT",
            status="closed", authority="DSAC / ECCAIRS 2", authority_reference="FR-2026-DEMO-0233", submitted_at=h(24 * 119),
            analysis="Erreur de saisie fournisseur ; aucune pièce suspecte montée.", follow_up_at=h(24 * 100),
            corrective_actions="Contrôle documentaire renforcé en réception ; fournisseur placé sous surveillance.",
            closed_on=(now - timedelta(days=90)).date())


    # ------------------------------------------------------------------ qualité, achats, Part-21
    def quality_and_purchasing(self):
        from apps.camo.models import ModificationRepair
        from apps.logistics.models import PurchaseOrder, PurchaseOrderLine, Supplier
        from apps.logistics.purchasing import receive_line, send_order
        from apps.quality.models import AuditFinding, ControlledDocument, DocumentRevision, InternalAudit
        from apps.quality.services import approve_revision

        t = self.today
        self.as_user("qualite")
        a1 = InternalAudit.objects.create(
            title="Réception et magasinage des pièces", scope="part145", kind="process", area="Magasin principal",
            planned_on=t - timedelta(days=40), performed_on=t - timedelta(days=38), auditor=self.u["qualite"],
            auditor_independent=True, status="reported", summary="Réception conforme dans l'ensemble ; deux écarts relevés.")
        AuditFinding.objects.create(audit=a1, level="level2", requirement="145.A.42(a)",
                                    description="Deux pièces stockées sans étiquette de statut (servicable / non servicable).")
        AuditFinding.objects.create(audit=a1, level="observation", requirement="MOE 2.3",
                                    description="Procédure de contrôle des températures de stockage à préciser.")
        InternalAudit.objects.create(
            title="Facteurs humains et formation continue", scope="part145", kind="process", area="Atelier",
            planned_on=t + timedelta(days=20), auditor=self.u["qualite"], auditor_independent=True)
        moe = ControlledDocument.objects.create(reference="MOE", title="Manuel des spécifications de l'organisme (MOE)",
                                                doc_type="moe", owner="Qualité", authority_approval=True, review_months=12)
        proc = ControlledDocument.objects.create(reference="PRO-STO-01", title="Réception et stockage des pièces",
                                                 doc_type="procedure", owner="Magasin", review_months=24)
        self.as_user("magasin")
        from django.core.files.base import ContentFile

        def pdf(name):
            return ContentFile(b"%PDF-1.4\n% document de demonstration AHMIS\n%%EOF\n", name=name)

        r1 = DocumentRevision.objects.create(document=proc, revision="A", change_summary="Édition initiale.", file=pdf("pro-sto-01-a.pdf"))
        self.as_user("qualite")
        approve_revision(r1, self.u["qualite"])
        DocumentRevision.objects.create(document=proc, revision="B", change_summary="Ajout de l'étiquetage du statut des pièces.")
        r_moe = DocumentRevision.objects.create(document=moe, revision="12", change_summary="Mise à jour de la liste du personnel d'encadrement.",
                                                authority_reference="DSAC/NO-2026-118", file=pdf("moe-12.pdf"))
        self.as_user("admin")
        approve_revision(r_moe, self.u["admin"])

        self.as_user("magasin")
        sup = Supplier.objects.create(name="Héli Pièces Distribution", kind="part145", approval_reference="FR.145.DEMO",
                                      approved=True, evaluated_on=t - timedelta(days=200), contact="commandes@exemple.invalid")
        Supplier.objects.create(name="Atelier non évalué", kind="other")
        po = PurchaseOrder.objects.create(supplier=sup, expected_on=t + timedelta(days=10))
        line_oil = PurchaseOrderLine.objects.create(order=po, part_number=self.pn["OIL"], quantity=D("6"))
        PurchaseOrderLine.objects.create(order=po, part_number=self.pn["CHIP"], quantity=D("2"))
        send_order(po)
        receive_line(line_oil, D("4"))
        PurchaseOrder.objects.create(supplier=sup, notes="Commande en préparation.")

        self.as_user("camo")
        ModificationRepair.objects.create(
            aircraft=self.ac["MC"], kind="mod", classification="major", approval_basis="stc",
            title="Installation d'un treuil de sauvetage", design_holder="Bureau d'études DEMO",
            design_approval_number="EASA.21J.DEMO", part21_status="requested", part21_requested_on=t - timedelta(days=15))
