from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone

from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView

from .forms import DeclarationForm, ProcessingForm
from .models import OccurrenceReport
from django.utils.translation import gettext, gettext_lazy


def visible_reports(user):
    """Comptes rendus visibles : tous pour les rôles habilités, sinon ceux que l'utilisateur a déclarés."""
    qs = OccurrenceReport.objects.select_related("aircraft")
    if user.has_perm("safety.view_all_occurrences"):
        return qs
    return qs.filter(created_by=user)


def can_see_reporter(user, report):
    return not report.confidential or user.has_perm("safety.view_reporter_identity") or report.created_by_id == user.pk


class OccurrenceList(AhmisListView):
    model = OccurrenceReport
    columns = [("N°", "number"), (gettext_lazy("Intitulé"), "title"), (gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Catégorie"), "category"),
               (gettext_lazy("Gravité"), "severity"), (gettext_lazy("Connu le"), "aware_at"), (gettext_lazy("Statut"), "status"), (gettext_lazy("Réf. autorité"), "authority_reference")]
    search_fields = ["number", "title", "description", "authority_reference", "aircraft__registration"]
    filter_fields = ["status", "category", "severity", "aircraft"]
    create_url = reverse_lazy("safety:create")
    title = gettext_lazy("Comptes rendus d'événements")
    subtitle = gettext_lazy("Règlement (UE) 376/2014 et 145.A.60 : notification à l'autorité sous 72 h, suivi sous 30 jours.")

    def get_permission_required(self):
        return ["safety.add_occurrencereport"]

    def get_queryset(self):
        self.queryset = visible_reports(self.request.user)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if not self.request.user.has_perm("safety.view_all_occurrences"):
            ctx["subtitle"] = gettext("Vos déclarations. Le responsable qualité / sécurité traite chaque compte rendu en toute confidentialité.")
        return ctx


class OccurrenceCreate(AhmisCreateView):
    model = OccurrenceReport
    form_class = DeclarationForm
    title = gettext_lazy("Déclarer un événement")

    def get_initial(self):
        from apps.part145.models import Defect, TaskCard

        init = super().get_initial()
        u = self.request.user
        init["reporter_name"] = u.get_full_name() or u.get_username()
        init["aware_at"] = init["occurred_at"] = timezone.localtime().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
        g = self.request.GET
        if g.get("defect"):
            d = Defect.objects.filter(pk=g["defect"]).first()
            if d:
                init.update({"defect": d, "aircraft": d.aircraft, "description": d.description,
                             "title": gettext("Défaut {number} – ATA {ata}").format(number=d.number, ata=d.ata) if d.ata else gettext("Défaut {number}").format(number=d.number)})
        if g.get("task_card"):
            c = TaskCard.objects.filter(pk=g["task_card"]).select_related("work_package").first()
            if c:
                init.update({"task_card": c, "aircraft": c.aircraft, "title": gettext("Task card {number}").format(number=c.number)})
        if g.get("aircraft"):
            init["aircraft"] = g["aircraft"]
        return init


class OccurrenceUpdate(AhmisUpdateView):
    model = OccurrenceReport
    form_class = ProcessingForm

    def get_queryset(self):
        return visible_reports(self.request.user)


@permission_required("safety.add_occurrencereport", raise_exception=True)
def occurrence_detail(request, pk):
    r = get_object_or_404(OccurrenceReport.objects.select_related("aircraft", "component__part_number", "defect", "task_card"), pk=pk)
    if not (request.user.has_perm("safety.view_all_occurrences") or r.created_by_id == request.user.pk):
        raise PermissionDenied
    return render(request, "safety/detail.html", {"r": r, "show_reporter": can_see_reporter(request.user, r)})


def dashboard_kpi(user):
    """Compteurs du tableau de bord (rôles habilités uniquement)."""
    if not user.has_perm("safety.view_all_occurrences"):
        return None
    open_reports = [r for r in OccurrenceReport.objects.exclude(status__in=["closed", "not_reportable"])]
    return {
        "open": len(open_reports),
        "to_notify": sum(1 for r in open_reports if r.status == "draft"),
        "overdue": sum(1 for r in open_reports if r.alert == "overdue"),
    }
