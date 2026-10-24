from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    def __str__(self):
        return self.username


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    TEACH = "teach"
    LEARN = "learn"
    KIND_CHOICES = [(TEACH, "Teach"), (LEARN, "Learn")]
    LEVELS = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="user_skills")
    kind = models.CharField(max_length=5, choices=KIND_CHOICES)
    level = models.CharField(max_length=12, choices=LEVELS, default="beginner")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "skill", "kind"], name="unique_user_skill_kind")
        ]
        indexes = [
            models.Index(fields=["skill", "kind"]),
            models.Index(fields=["user", "kind"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.kind} {self.skill.name}"


class Certification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certifications")
    name = models.CharField(max_length=120)
    issuer = models.CharField(max_length=120, blank=True)
    credential_url = models.URLField(blank=True)
    issued_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.user.username}"


class UserBlock(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_made")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_user_block"),
                       models.CheckConstraint(condition=~models.Q(blocker=models.F("blocked")), name="no_self_block")]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="triggered_notifications")
    message = models.CharField(max_length=240)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient}: {self.message}"
