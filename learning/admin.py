from django.contrib import admin
from .models import LearningSession, ChatMessage, SessionRating
admin.site.register(LearningSession)
admin.site.register(ChatMessage)
admin.site.register(SessionRating)
