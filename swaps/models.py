from django.conf import settings
from django.db import models
from django.db.models import Q
from accounts.models import Skill


class SwapRequest(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (COMPLETED, "Completed"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_swaps"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_swaps"
    )
    skill_offered = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="offered_in_swaps")
    skill_wanted = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="wanted_in_swaps")
    message = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user", "skill_offered", "skill_wanted"],
                name="unique_swap_request",
            ),
            models.CheckConstraint(
                condition=~Q(from_user=models.F("to_user")),
                name="no_self_swap",
            ),
        ]
        indexes = [
            models.Index(fields=["to_user", "status"]),
            models.Index(fields=["from_user", "status"]),
        ]

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"
