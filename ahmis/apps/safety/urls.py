from django.urls import path

from . import views as v

app_name = "safety"

urlpatterns = [
    path("", v.OccurrenceList.as_view(), name="list"),
    path("declarer/", v.OccurrenceCreate.as_view(), name="create"),
    path("<int:pk>/", v.occurrence_detail, name="detail"),
    path("<int:pk>/traiter/", v.OccurrenceUpdate.as_view(), name="update"),
]
