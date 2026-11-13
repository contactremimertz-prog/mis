def ahmis(request):
    from django.conf import settings
    return {"AHMIS": settings.AHMIS}
