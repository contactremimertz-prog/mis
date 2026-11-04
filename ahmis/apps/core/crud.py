"""Vues génériques de liste / création / modification, partagées par tous les modules."""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import CreateView, ListView, UpdateView


def formfield_callback(field, **kwargs):
    if isinstance(field, models.DateTimeField):
        kwargs["widget"] = forms.DateTimeInput(attrs={"type": "datetime-local"})
    elif isinstance(field, models.DateField):
        kwargs["widget"] = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    elif isinstance(field, models.TextField):
        kwargs["widget"] = forms.Textarea(attrs={"rows": 4})
    return field.formfield(**kwargs)


class AhmisModelForm(forms.ModelForm):
    formfield_callback = formfield_callback


def perm(model, action):
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


class AhmisListView(PermissionRequiredMixin, ListView):
    template_name = "core/list.html"
    paginate_by = 50
    columns = []  # [(libellé, accesseur)]
    search_fields = []
    filter_fields = []  # champs à choix ou FK
    title = ""
    subtitle = ""
    create_url = None
    link_column = 0
    extra_actions = []  # [(libellé, url)]

    def get_permission_required(self):
        return [perm(self.model, "view")]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q and self.search_fields:
            cond = Q()
            for f in self.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        for f in self.filter_fields:
            v = self.request.GET.get(f)
            if v:
                qs = qs.filter(**{f: v})
        return qs

    def get_filters(self):
        result = []
        for name in self.filter_fields:
            field = self.model._meta.get_field(name)
            if field.choices:
                options = list(field.flatchoices)
            elif field.is_relation:
                options = [(o.pk, str(o)) for o in field.related_model.objects.all()]
            elif isinstance(field, models.BooleanField):
                options = [("1", "Oui"), ("0", "Non")]
            else:
                continue
            result.append({
                "name": name, "label": field.verbose_name.capitalize(),
                "options": [(str(k), v) for k, v in options],
                "value": self.request.GET.get(name, ""),
            })
        return result

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.model._meta
        can_add = self.request.user.has_perm(perm(self.model, "add"))
        ctx.update({
            "title": self.title or meta.verbose_name_plural.capitalize(),
            "subtitle": self.subtitle,
            "columns": self.columns,
            "filters": self.get_filters(),
            "searchable": bool(self.search_fields),
            "create_url": self.create_url if can_add else None,
            "link_column": self.link_column,
            "extra_actions": self.extra_actions,
        })
        return ctx


class _FormMixin:
    template_name = "core/form.html"
    form_class = None
    fields = None
    title = ""
    cancel_url = None

    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return forms.modelform_factory(self.model, form=AhmisModelForm, fields=self.fields)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.get_title()
        ctx["cancel_url"] = self.cancel_url or self.request.META.get("HTTP_REFERER", "")
        return ctx

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ValidationError as e:
            for msg in e.messages:
                form.add_error(None, msg)
            return self.form_invalid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name.capitalize()} « {self.object} » enregistré(e).")
        return response

    def get_success_url(self):
        if hasattr(self.object, "get_absolute_url"):
            return self.object.get_absolute_url()
        return self.request.path


class AhmisCreateView(PermissionRequiredMixin, _FormMixin, CreateView):
    def get_permission_required(self):
        return [perm(self.model, "add")]

    def get_title(self):
        return self.title or f"Nouveau / nouvelle {self.model._meta.verbose_name}"


class AhmisUpdateView(PermissionRequiredMixin, _FormMixin, UpdateView):
    def get_permission_required(self):
        return [perm(self.model, "change")]

    def get_title(self):
        return self.title or f"Modifier {self.object}"


def back(request, default="dashboard"):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and nxt.startswith("/"):
        return redirect(nxt)
    return redirect(request.META.get("HTTP_REFERER") or default)


def error_messages(request, exc):
    msgs = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
    for m in msgs:
        messages.error(request, m)
