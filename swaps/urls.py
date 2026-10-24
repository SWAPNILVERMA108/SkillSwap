from django.urls import path
from . import views

app_name = "swaps"

urlpatterns = [
    path("", views.matches, name="matches"),
    path("requests/send/", views.send_request, name="send_request"),
    path("requests/", views.requests_list, name="requests"),
    path("requests/<int:pk>/<str:action>/", views.update_request, name="update_request"),
]
