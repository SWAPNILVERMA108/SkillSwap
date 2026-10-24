import uuid
from django.conf import settings
from django.db import models
from swaps.models import SwapRequest

class LearningSession(models.Model):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    STATUS_CHOICES = [(SCHEDULED, "Scheduled"), (LIVE, "Live"), (ENDED, "Ended")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    swap_request = models.OneToOneField(SwapRequest, on_delete=models.CASCADE, related_name="learning_session")
    scheduled_for = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def participants(self):
        return (self.swap_request.from_user, self.swap_request.to_user)

    def __str__(self):
        return f"Learning session {self.pk} ({self.status})"


class ChatMessage(models.Model):
    session = models.ForeignKey(LearningSession, on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_messages")
    text = models.TextField(blank=True, max_length=4000)
    attachment = models.FileField(upload_to="learning_chat/%Y/%m/", blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_type = models.CharField(max_length=20, blank=True)
    attachment_content_type = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["created_at"]
    def __str__(self):
        return f"Chat message by {self.sender} in {self.session_id}"


class SessionRating(models.Model):
    session = models.ForeignKey(LearningSession, on_delete=models.CASCADE, related_name="ratings")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_given")
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_received")
    skill = models.ForeignKey("accounts.Skill", on_delete=models.PROTECT, related_name="session_ratings")
    score = models.PositiveSmallIntegerField()
    review = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "reviewer"], name="one_rating_per_user_per_session"), models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=5), name="rating_score_1_to_5")]
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.score}/5 for {self.reviewee}"
