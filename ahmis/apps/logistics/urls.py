from django.urls import path

from . import views as v

app_name = "logistics"

urlpatterns = [
    path("reception/", v.receive, name="receive"),
    path("certificats/", v.CertificateList.as_view(), name="certificate_list"),
    path("certificats/nouveau/", v.CertificateCreate.as_view(), name="certificate_create"),
    path("composants/<int:pk>/statut/", v.component_status, name="component_status"),
    path("composants/<int:pk>/rebut/", v.component_scrap, name="component_scrap"),
    path("quarantaine/", v.quarantine, name="quarantine"),
    path("stock/", v.StockList.as_view(), name="stock_list"),
    path("stock/<int:pk>/modifier/", v.StockUpdate.as_view(), name="stock_update"),
    path("stock/<int:pk>/ajuster/", v.stock_adjust, name="stock_adjust"),
    path("demandes/", v.RequestList.as_view(), name="request_list"),
    path("demandes/<int:pk>/", v.request_detail, name="request_detail"),
    path("task-cards/<int:card_pk>/demande/", v.request_create, name="request_create"),
    path("task-cards/<int:card_pk>/outillage/", v.tool_checkout, name="tool_checkout"),
    path("outillage/", v.ToolList.as_view(), name="tool_list"),
    path("outillage/nouveau/", v.ToolCreate.as_view(), name="tool_create"),
    path("outillage/<int:pk>/", v.tool_detail, name="tool_detail"),
    path("outillage/<int:pk>/modifier/", v.ToolUpdate.as_view(), name="tool_update"),
    path("outillage/<int:pk>/restituer/", v.tool_checkin, name="tool_checkin"),
    path("magasins/", v.StoreList.as_view(), name="store_list"),
    path("magasins/nouveau/", v.StoreCreate.as_view(), name="store_create"),
]
