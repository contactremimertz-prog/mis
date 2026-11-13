"""Jeu de données minimal pour les tests automatiques."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from apps.core.roles import setup_roles
from apps.fleet.models import Aircraft, AircraftType, Component, PartNumber
from apps.logistics.models import ReleaseCertificate, StoreLocation
from apps.part145.models import Authorization, ExperienceRecord, Qualification, Staff

PASSWORD = "Test-pass-2026!"
D = Decimal


def today():
    return timezone.localdate()


def make_world():
    setup_roles()
    User = get_user_model()
    w = {}
    w["type"] = AircraftType.objects.create(code="H125", manufacturer="Airbus Helicopters", model="H125", category="helicopter", cycle_label="Atterrissages")
    w["other_type"] = AircraftType.objects.create(code="H135", manufacturer="Airbus Helicopters", model="H135", category="helicopter")
    w["ac"] = Aircraft.objects.create(
        registration="F-TEST", msn="1", aircraft_type=w["type"], manufacture_date=today() - timedelta(days=2000),
        total_fh=D("1000"), total_fc=3000, counters_date=today(), planned_daily_fh=D("2"), planned_daily_fc=D("5"),
    )
    w["store"] = StoreLocation.objects.create(code="MAG", name="Magasin")
    w["quar"] = StoreLocation.objects.create(code="QUAR", name="Quarantaine", is_quarantine=True)
    w["pn_engine"] = PartNumber.objects.create(pn="P-ENG", description="Moteur", is_serialized=True, tbo_fh=D("3000"))
    w["pn_engine"].applicable_types.set([w["type"]])
    w["pn_llp"] = PartNumber.objects.create(pn="P-LLP", description="Moyeu", is_serialized=True, is_llp=True, life_limit_fc=5000)
    for name, group, cert_cat in [("meca", "Mécanicien", "MECH"), ("b1", "Certifiant", "B1"), ("b1bis", "Certifiant", "B1"), ("certc", "Certifiant", "C"), ("mag", "Magasinier", None), ("planif", "Planificateur", None), ("camo", "Ingénieur CAMO", None)]:
        u = User.objects.create_user(name, password=PASSWORD)
        u.groups.add(Group.objects.get(name=group))
        w[f"u_{name}"] = u
        if cert_cat:
            s = Staff.objects.create(user=u, employee_number=name.upper(), first_name=name, last_name="Test",
                                     licence_number="" if cert_cat == "MECH" else f"FR.66.{name}", licence_categories=cert_cat,
                                     licence_expiry=today() + timedelta(days=365))
            Authorization.objects.create(staff=s, number=f"A-{name}", aircraft_type=w["type"], category=cert_cat,
                                         certifying=cert_cat != "MECH", valid_from=today() - timedelta(days=10), valid_until=today() + timedelta(days=100))
            # Formations obligatoires et expérience récente (145.A.35) à jour
            for cat in ("human_factors", "continuation"):
                Qualification.objects.create(staff=s, category=cat, name=cat, obtained=today() - timedelta(days=100),
                                             expiry=today() + timedelta(days=600))
            ExperienceRecord.objects.create(staff=s, start=today() - timedelta(days=400), end=today() - timedelta(days=30),
                                            organisation="Atelier précédent", description="Entretien en ligne")
            w[f"s_{name}"] = s
    return w


def make_component(w, pn=None, sn="SN1", status="serviceable", cert=True, **kw):
    c = Component.objects.create(part_number=pn or w["pn_engine"], serial_number=sn, status=status, location=w["store"],
                                 manufacture_date=today() - timedelta(days=500), **kw)
    if cert:
        ReleaseCertificate.objects.create(cert_type="easa_form1", tracking_number=f"F1-{sn}", issuer="Atelier", issue_date=today(),
                                          part_number=c.part_number, serial_or_batch=sn, component=c)
    return c
