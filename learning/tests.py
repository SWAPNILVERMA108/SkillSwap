from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Skill, UserBlock
from swaps.models import SwapRequest
from .models import LearningSession, SessionRating
from .views import validate_chat_upload
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

User = get_user_model()


class LearningRoomAccessTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="alice", email="alice@example.com", password="Test-pass-123")
        self.b = User.objects.create_user(username="bob", email="bob@example.com", password="Test-pass-123")
        self.strength = Skill.objects.create(name="Python")
        self.wanted = Skill.objects.create(name="SQL")
        self.swap = SwapRequest.objects.create(from_user=self.a, to_user=self.b, skill_offered=self.strength, skill_wanted=self.wanted, status=SwapRequest.ACCEPTED)
        self.session = LearningSession.objects.create(swap_request=self.swap)

    def test_nonparticipant_cannot_open_room(self):
        outsider = User.objects.create_user(username="outsider", password="Test-pass-123")
        self.client.force_login(outsider)
        response = self.client.get(reverse("learning:room", args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)

    def test_participant_can_open_accepted_room(self):
        self.client.force_login(self.a)
        response = self.client.get(reverse("learning:room", args=[self.session.pk]))
        self.assertEqual(response.status_code, 200)

    def test_block_disables_room_access(self):
        UserBlock.objects.create(blocker=self.a, blocked=self.b)
        self.client.force_login(self.a)
        response = self.client.get(reverse("learning:room", args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)

    def test_invalid_pdf_signature_is_rejected(self):
        upload = SimpleUploadedFile("fake.pdf", b"not a pdf", content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_chat_upload(upload)

    def test_session_completion_is_idempotent(self):
        self.client.force_login(self.a)
        url = reverse("learning:end_session", args=[self.session.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(self.a.notifications.count(), 0)
        self.assertEqual(self.b.notifications.count(), 1)

    def test_rating_constraint_and_completed_only_view(self):
        self.session.status = LearningSession.ENDED
        self.session.save(update_fields=["status"])
        self.client.force_login(self.a)
        response = self.client.post(reverse("learning:submit_rating", args=[self.session.pk]), {"score": "5", "review": "Great"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SessionRating.objects.filter(session=self.session, reviewer=self.a).count(), 1)
        self.client.post(reverse("learning:submit_rating", args=[self.session.pk]), {"score": "4"})
        self.assertEqual(SessionRating.objects.filter(session=self.session, reviewer=self.a).count(), 1)
