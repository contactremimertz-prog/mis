from django.http import JsonResponse
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_GET

from . import engine


@require_GET
def ask(request):
    """Réponse JSON de l'assistant. Aucune donnée métier n'est lue ni modifiée."""
    lang = (get_language() or "fr")[:2]
    q = request.GET.get("q", "")
    if not q.strip():
        return JsonResponse({"answer": None, "suggestions": [], "questions": engine.questions(lang, request.user)})
    best, suggestions = engine.answer(q, lang, request.user)
    return JsonResponse({
        "answer": best, "suggestions": suggestions,
        "fallback": None if best else _("Je n'ai pas de réponse validée à cette question. Choisissez une question ci-dessous ou consultez les tutoriels."),
        "questions": [] if best else engine.questions(lang, request.user),
    })
