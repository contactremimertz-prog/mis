from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from django.views.decorators.http import require_POST

from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView, error_messages
from apps.core.models import SignatureRecord
from apps.part145.forms import SignForm
from apps.part145.views import _check_password

from . import services
from .forms import AuditForm, DocumentForm, FindingCloseForm, FindingForm, RejectForm, RevisionForm
from .models import AuditFinding, ControlledDocument, DocumentRevision, InternalAudit


# ---------------------------------------------------------------- Audits internes
class AuditList(AhmisListView):
    model = InternalAudit
    queryset = InternalAudit.objects.select_related("auditor")
    columns = [(_l("N°"), "number"), (_l("Objet"), "title"), (_l("Référentiel"), "scope"), (_l("Activité"), "area"),
               (_l("Date prévue"), "planned_on"), (_l("Auditeur"), "auditor"), (_l("Statut"), "status")]
    search_fields = ["number", "title", "area"]
    filter_fields = ["status", "scope", "kind"]
    create_url = reverse_lazy("quality:audit_create")
    title = _l("Audits internes")
    subtitle = _l("Programme d'audits indépendants (145.A.65(c), CAMO.A.200(a)(6)) : constats classés et suivis jusqu'à clôture.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["extra_actions"] = [(_("Constats ouverts"), reverse("quality:finding_list") + "?status=open")]
        return ctx


class AuditCreate(AhmisCreateView):
    model = InternalAudit
    form_class = AuditForm
    title = _l("Planifier un audit")

    def get_initial(self):
        return {**super().get_initial(), "auditor": self.request.user}


class AuditUpdate(AhmisUpdateView):
    model = InternalAudit
    form_class = AuditForm


@permission_required("quality.view_internalaudit", raise_exception=True)
def audit_detail(request, pk):
    a = get_object_or_404(InternalAudit.objects.select_related("auditor"), pk=pk)
    findings = list(a.findings.all())
    sigs = {s.object_id: s for s in SignatureRecord.objects.filter(action="finding_close", object_id__in=[str(f.pk) for f in findings])}
    for f in findings:
        f.signature = sigs.get(str(f.pk))
    return render(request, "quality/audit_detail.html", {
        "a": a, "findings": findings, "finding_form": FindingForm(), "close_form": FindingCloseForm(),
    })


@require_POST
@permission_required("quality.add_auditfinding", raise_exception=True)
def finding_add(request, pk):
    a = get_object_or_404(InternalAudit, pk=pk)
    form = FindingForm(request.POST, instance=AuditFinding(audit=a))
    if form.is_valid():
        f = form.save()
        messages.success(request, _("Constat %(n)s enregistré, à corriger avant le %(d)s.") % {"n": f.number, "d": f.due_date.strftime("%d/%m/%Y")})
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect(a.get_absolute_url())


@require_POST
@permission_required("quality.change_auditfinding", raise_exception=True)
def finding_close(request, pk):
    f = get_object_or_404(AuditFinding.objects.select_related("audit"), pk=pk)
    form = FindingCloseForm(request.POST)
    if not form.is_valid():
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
        return redirect(f.audit.get_absolute_url())
    try:
        _check_password(request, form)
        services.close_finding(f, request.user, form.cleaned_data["root_cause"], form.cleaned_data["corrective_action"])
    except ValidationError as e:
        error_messages(request, e)
    else:
        messages.success(request, _("Constat %(n)s clôturé et signé.") % {"n": f.number})
    return redirect(f.audit.get_absolute_url())


class FindingList(AhmisListView):
    model = AuditFinding
    queryset = AuditFinding.objects.select_related("audit")
    columns = [(_l("N°"), "number"), (_l("Audit"), "audit.number"), (_l("Niveau"), "level"), (_l("Exigence"), "requirement"),
               (_l("À corriger avant le"), "due_date"), (_l("Statut"), "status")]
    search_fields = ["number", "requirement", "description", "audit__number"]
    filter_fields = ["status", "level"]
    title = _l("Constats d'audit")
    subtitle = _l("Niveau 1 : action immédiate. Niveau 2 : correction sous 3 mois au plus. Observation : 30 jours.")


# ---------------------------------------------------------------- Documents maîtrisés
class DocumentList(AhmisListView):
    model = ControlledDocument
    columns = [(_l("Référence"), "reference"), (_l("Intitulé"), "title"), (_l("Type"), "doc_type"),
               (_l("Révision en vigueur"), "current_revision"), (_l("En vigueur depuis"), "current_since"), (_l("Statut"), "status")]
    search_fields = ["reference", "title", "owner"]
    filter_fields = ["doc_type", "status"]
    create_url = reverse_lazy("quality:doc_create")
    title = _l("Documents maîtrisés")
    subtitle = _l("Une révision n'entre en vigueur qu'après approbation signée par une autre personne que son rédacteur.")


class DocumentCreate(AhmisCreateView):
    model = ControlledDocument
    form_class = DocumentForm
    title = _l("Nouveau document maîtrisé")


class DocumentUpdate(AhmisUpdateView):
    model = ControlledDocument
    form_class = DocumentForm


@permission_required("quality.view_controlleddocument", raise_exception=True)
def doc_detail(request, pk):
    d = get_object_or_404(ControlledDocument, pk=pk)
    revisions = list(d.revisions.select_related("created_by", "approved_by"))
    return render(request, "quality/doc_detail.html", {
        "d": d, "revisions": revisions, "pending": next((r for r in revisions if r.status == "pending"), None),
        "revision_form": RevisionForm(), "reject_form": RejectForm(),
        "sign_form": SignForm(),
    })


@require_POST
@permission_required("quality.add_documentrevision", raise_exception=True)
def revision_add(request, pk):
    d = get_object_or_404(ControlledDocument, pk=pk)
    if d.status == "obsolete":
        messages.error(request, _("Ce document est retiré : aucune nouvelle révision possible."))
        return redirect(d.get_absolute_url())
    form = RevisionForm(request.POST, request.FILES, instance=DocumentRevision(document=d))
    if form.is_valid():
        try:
            r = form.save()
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, _("Révision %(r)s soumise à approbation.") % {"r": r.revision})
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect(d.get_absolute_url())


@require_POST
@permission_required("quality.approve_documentrevision", raise_exception=True)
def revision_approve(request, pk):
    from apps.part145.forms import SignForm

    r = get_object_or_404(DocumentRevision.objects.select_related("document"), pk=pk)
    form = SignForm(request.POST)
    if form.is_valid():
        try:
            _check_password(request, form)
            services.approve_revision(r, request.user)
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, _("Révision %(r)s approuvée et signée : elle est en vigueur.") % {"r": r.revision})
    return redirect(r.document.get_absolute_url())


@require_POST
@permission_required("quality.approve_documentrevision", raise_exception=True)
def revision_reject(request, pk):
    r = get_object_or_404(DocumentRevision.objects.select_related("document"), pk=pk)
    form = RejectForm(request.POST)
    if form.is_valid():
        try:
            services.reject_revision(r, request.user, form.cleaned_data["reason"])
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, _("Révision %(r)s refusée.") % {"r": r.revision})
    return redirect(r.document.get_absolute_url())


@require_POST
@permission_required("quality.approve_documentrevision", raise_exception=True)
def doc_withdraw(request, pk):
    d = get_object_or_404(ControlledDocument, pk=pk)
    try:
        services.withdraw_document(d, request.user)
    except ValidationError as e:
        error_messages(request, e)
    else:
        messages.success(request, _("Document %(d)s retiré.") % {"d": d.reference})
    return redirect(d.get_absolute_url())


def dashboard_kpi(user):
    if not user.has_perm("quality.view_internalaudit"):
        return None
    from django.utils import timezone

    today = timezone.localdate()
    open_f = AuditFinding.objects.filter(status="open")
    docs = [d for d in ControlledDocument.objects.filter(status="current")]
    return {
        "findings_open": open_f.count(),
        "findings_overdue": open_f.filter(due_date__lt=today).count(),
        "level1_open": open_f.filter(level="level1").count(),
        "revisions_pending": DocumentRevision.objects.filter(status="pending").count(),
        "docs_review_due": sum(1 for d in docs if d.alert == "overdue"),
    }
