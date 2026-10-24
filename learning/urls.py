from django.urls import path
from . import views
app_name = "learning"
urlpatterns = [
    path("from-swap/<int:swap_id>/", views.room_for_swap, name="room_for_swap"),
    path("room/<uuid:room_id>/", views.room, name="room"),
    path("room/<uuid:room_id>/end/", views.end_session, name="end_session"),
    path("room/<uuid:room_id>/rate/", views.submit_rating, name="submit_rating"),
    path("attachment/<int:message_id>/", views.attachment, name="attachment"),
]
