from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import UserBlock, Notification

User = get_user_model()


class ProfileAndPrivacyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="learner", email="learner@example.com", password="Test-pass-123")
        self.other = User.objects.create_user(username="teacher", email="teacher@example.com", password="Test-pass-123")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_shows_username_and_email(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "learner")
        self.assertContains(response, "learner@example.com")

    def test_user_can_block_and_unblock(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:block_user", args=[self.other.pk]), {"next": reverse("swaps:requests")})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserBlock.objects.filter(blocker=self.user, blocked=self.other).exists())
        response = self.client.post(reverse("accounts:unblock_user", args=[self.other.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserBlock.objects.filter(blocker=self.user, blocked=self.other).exists())

    def test_notifications_page_marks_unread_as_read(self):
        Notification.objects.create(recipient=self.user, actor=self.other, message="Hello")
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.notifications.get().is_read)
