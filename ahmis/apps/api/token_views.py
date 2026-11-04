"""Écrans de gestion des jetons API (réservés aux administrateurs)."""
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ApiToken

admin_required = user_passes_test(lambda u: u.is_active and u.is_superuser)


class TokenForm(forms.Form):
    name = forms.CharField(label="Nom du système appelant", max_length=100)
    user = forms.ModelChoiceField(get_user_model().objects.filter(is_active=True).order_by("username"), label="Compte AHMIS (droits appliqués)")
    scope = forms.ChoiceField(label="Portée", choices=ApiToken.SCOPES)
    validity_days = forms.IntegerField(label="Validité (jours, 0 = sans limite)", min_value=0, max_value=3650, initial=365)
    allowed_ips = forms.CharField(label="Adresses IP autorisées (virgules, vide = toutes)", required=False, max_length=500)

    def clean_user(self):
        user = self.cleaned_data["user"]
        if user.is_superuser:
            raise forms.ValidationError("Par sécurité, un jeton ne peut pas être lié à un compte administrateur : créez un compte de service avec le rôle voulu.")
        return user

    def clean_allowed_ips(self):
        import ipaddress

        raw = self.cleaned_data["allowed_ips"]
        for ip in [x.strip() for x in raw.split(",") if x.strip()]:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise forms.ValidationError(f"Adresse IP invalide : {ip}")
        return raw


@admin_required
def token_list(request):
    form = TokenForm(request.POST or None)
    new_key = None
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        expires = timezone.now() + timedelta(days=d["validity_days"]) if d["validity_days"] else None
        token, new_key = ApiToken.issue(d["name"], d["user"], d["scope"], created_by=request.user, expires_at=expires, allowed_ips=d["allowed_ips"])
        messages.success(request, f"Jeton « {token.name} » créé. Copiez la clé maintenant : elle ne sera plus jamais affichée.")
        form = TokenForm()
    return render(request, "api/tokens.html", {"tokens": ApiToken.objects.select_related("user", "created_by"), "form": form, "new_key": new_key})


@admin_required
@require_POST
def token_revoke(request, pk):
    token = get_object_or_404(ApiToken, pk=pk)
    token.active = False
    token.save(update_fields=["active"])
    messages.success(request, f"Jeton « {token.name} » révoqué.")
    return redirect("api_tokens")
