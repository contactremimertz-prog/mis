"""Règles métier signées de la qualité : clôture des constats, approbation des révisions."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.models import SignatureRecord


@transaction.atomic
def close_finding(finding, user, root_cause, corrective_action):
    if finding.status == "closed":
        raise ValidationError(_("Ce constat est déjà clôturé."))
    finding.root_cause = root_cause
    finding.corrective_action = corrective_action
    finding.status = "closed"
    finding.closed_on = timezone.localdate()
    finding.full_clean()
    finding.save()
    SignatureRecord.sign(user, finding, "finding_close", _("Je certifie que la cause du constat %(n)s est traitée et que "
                                                           "l'action corrective est mise en œuvre et efficace.") % {"n": finding.number})
    return finding


@transaction.atomic
def approve_revision(rev, user):
    doc = rev.document
    if rev.status != "pending":
        raise ValidationError(_("Seule une révision en attente peut être approuvée."))
    if rev.created_by_id == user.pk:
        raise ValidationError(_("Le rédacteur d'une révision ne peut pas l'approuver (double regard)."))
    if doc.authority_approval and not rev.authority_reference.strip():
        raise ValidationError(_("Ce document exige l'approbation de l'autorité : indiquez sa référence avant d'approuver."))
    now = timezone.now()
    doc.revisions.filter(status="approved").update(status="superseded")
    rev.status = "approved"
    rev.approved_by = user
    rev.approved_at = now
    rev.save()
    doc.current_revision = rev.revision
    doc.current_since = timezone.localdate()
    doc.status = "current"
    doc.save()
    SignatureRecord.sign(user, rev, "doc_approve", _("J'approuve la révision %(r)s du document %(d)s et sa mise en vigueur.")
                         % {"r": rev.revision, "d": doc.reference})
    return rev


@transaction.atomic
def reject_revision(rev, user, reason):
    if rev.status != "pending":
        raise ValidationError(_("Seule une révision en attente peut être refusée."))
    if not reason.strip():
        raise ValidationError(_("Motif du refus obligatoire."))
    rev.status = "rejected"
    rev.rejection_reason = reason[:200]
    rev.save()
    return rev


@transaction.atomic
def withdraw_document(doc, user):
    if doc.status == "obsolete":
        raise ValidationError(_("Ce document est déjà retiré."))
    if doc.pending_revision:
        raise ValidationError(_("Une révision est en attente : approuvez-la ou refusez-la d'abord."))
    doc.status = "obsolete"
    doc.save()
    return doc
