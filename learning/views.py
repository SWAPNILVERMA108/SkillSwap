from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse, Http404
from django.views.decorators.http import require_POST
from accounts.models import Notification, UserBlock
from swaps.models import SwapRequest
from .models import LearningSession, ChatMessage, SessionRating

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio", ".webm": "audio",
    ".pdf": "file", ".txt": "file", ".zip": "file",
}

def validate_chat_upload(upload):
    """Validate size, extension and file signature; never trust browser MIME alone."""
    import os
    from PIL import Image, UnidentifiedImageError
    from django.core.exceptions import ValidationError

    if upload.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError("Attachments must be 10 MB or smaller.")
    extension = os.path.splitext(upload.name)[1].lower()
    kind = ALLOWED_EXTENSIONS.get(extension)
    if not kind:
        raise ValidationError("Allowed files: JPG, PNG, WebP, MP3, WAV, OGG, M4A, WebM, PDF, TXT, and ZIP.")
    upload.seek(0)
    head = upload.read(16)
    upload.seek(0)
    if kind == "image":
        try:
            with Image.open(upload) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Image file content does not match an allowed image format.")
                image.verify()
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("The uploaded image is invalid or corrupted.") from exc
        finally:
            upload.seek(0)
    elif extension == ".pdf" and not head.startswith(b"%PDF-"):
        raise ValidationError("The file content does not match a PDF.")
    elif extension == ".zip" and not head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        raise ValidationError("The file content does not match a ZIP archive.")
    elif extension == ".txt":
        data = upload.read(4096)
        upload.seek(0)
        if b"\x00" in data:
            raise ValidationError("The text file contains binary data.")
    elif kind == "audio":
        signatures = {
            ".mp3": (b"ID3",), ".wav": (b"RIFF",), ".ogg": (b"OggS",),
            ".m4a": (b"\x00\x00\x00",), ".webm": (b"\x1aE\xdf\xa3",),
        }
        if not any(head.startswith(signature) for signature in signatures[extension]):
            raise ValidationError("The file content does not look like the selected audio format.")
    upload.seek(0)
    return kind

def blocked_between(a, b):
    return UserBlock.objects.filter(blocker_id=a, blocked_id=b).exists() or UserBlock.objects.filter(blocker_id=b, blocked_id=a).exists()

@login_required
def room_for_swap(request, swap_id):
    swap = get_object_or_404(SwapRequest, pk=swap_id)
    if request.user.pk not in (swap.from_user_id, swap.to_user_id):
        messages.error(request, "You are not a participant in this swap."); return redirect("swaps:requests")
    if swap.status != SwapRequest.ACCEPTED:
        messages.error(request, "A learning room is available only after the swap request is accepted."); return redirect("swaps:requests")
    if blocked_between(swap.from_user_id, swap.to_user_id):
        messages.error(request, "Chat and learning rooms are unavailable because one participant has blocked the other."); return redirect("swaps:requests")
    session, _ = LearningSession.objects.get_or_create(swap_request=swap)
    return redirect("learning:room", room_id=session.pk)

@login_required
def room(request, room_id):
    session = get_object_or_404(LearningSession.objects.select_related("swap_request__from_user", "swap_request__to_user"), pk=room_id)
    swap = session.swap_request
    if swap.status != SwapRequest.ACCEPTED or request.user.pk not in (swap.from_user_id, swap.to_user_id) or blocked_between(swap.from_user_id, swap.to_user_id):
        messages.error(request, "You cannot access this learning room."); return redirect("swaps:requests")
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        upload = request.FILES.get("attachment")
        if not text and not upload:
            messages.error(request, "Write a message or attach a file.")
        else:
            upload_kind = None
            if upload:
                from django.core.exceptions import ValidationError
                try:
                    upload_kind = validate_chat_upload(upload)
                except ValidationError as exc:
                    messages.error(request, " ".join(exc.messages))
                    return redirect("learning:room", room_id=session.pk)
            msg = ChatMessage(session=session, sender=request.user, text=text)
            if upload:
                msg.attachment = upload; msg.attachment_name = upload.name.replace("\\", "/").split("/")[-1][:255]
                msg.attachment_type = upload_kind
                msg.attachment_content_type = {"image": "image/" + upload.name.rsplit(".", 1)[-1].lower(), "audio": "audio/" + upload.name.rsplit(".", 1)[-1].lower(), "file": "application/octet-stream"}[upload_kind][:120]
            msg.save()
            peer = swap.to_user if request.user.pk == swap.from_user_id else swap.from_user
            Notification.objects.create(recipient=peer, actor=request.user, message=f"New chat message from {request.user.username}.", url=f"/learning/room/{session.pk}/")
            return redirect("learning:room", room_id=session.pk)
    peer = swap.to_user if request.user.pk == swap.from_user_id else swap.from_user
    ratings = session.ratings.all()
    my_rating = ratings.filter(reviewer=request.user).first()
    can_rate = session.status == LearningSession.ENDED and not my_rating
    rating_skill = swap.skill_wanted if request.user.pk == swap.from_user_id else swap.skill_offered
    return render(request, "learning/room.html", {"session": session, "peer": peer, "chat_messages": session.chat_messages.select_related("sender"), "my_rating": my_rating, "can_rate": can_rate, "rating_skill": rating_skill, "ratings": ratings})

@login_required
@require_POST
def end_session(request, room_id):
    session = get_object_or_404(LearningSession.objects.select_related("swap_request"), pk=room_id)
    swap = session.swap_request
    if request.user.pk not in (swap.from_user_id, swap.to_user_id) or swap.status != SwapRequest.ACCEPTED:
        messages.error(request, "You cannot change this session."); return redirect("swaps:requests")
    peer = swap.to_user if request.user.pk == swap.from_user_id else swap.from_user
    if session.status != LearningSession.ENDED:
        session.status = LearningSession.ENDED; session.save(update_fields=["status", "updated_at"])
        Notification.objects.create(recipient=peer, actor=request.user, message="The learning session was marked complete. Please leave a rating.", url=f"/learning/room/{session.pk}/")
    messages.success(request, "Learning session completed. Both participants can now rate the tutorial.")
    return redirect("learning:room", room_id=session.pk)

@login_required
@require_POST
def submit_rating(request, room_id):
    session = get_object_or_404(LearningSession.objects.select_related("swap_request"), pk=room_id)
    swap = session.swap_request
    if request.user.pk not in (swap.from_user_id, swap.to_user_id) or swap.status != SwapRequest.ACCEPTED or session.status != LearningSession.ENDED:
        messages.error(request, "Ratings are available only to participants after the tutorial is completed."); return redirect("swaps:requests")
    peer = swap.to_user if request.user.pk == swap.from_user_id else swap.from_user
    skill = swap.skill_wanted if request.user.pk == swap.from_user_id else swap.skill_offered
    try: score = int(request.POST.get("score", "0"))
    except ValueError: score = 0
    if score not in range(1, 6):
        messages.error(request, "Choose a rating from 1 to 5."); return redirect("learning:room", room_id=session.pk)
    rating, created = SessionRating.objects.get_or_create(session=session, reviewer=request.user, defaults={"reviewee": peer, "skill": skill, "score": score, "review": request.POST.get("review", "").strip()[:500]})
    if not created:
        messages.error(request, "You have already rated this tutorial.")
    else:
        Notification.objects.create(recipient=peer, actor=request.user, message=f"{request.user.username} rated your {skill.name} tutorial {score}/5.", url=f"/learning/room/{session.pk}/")
        messages.success(request, "Your rating has been submitted.")
    return redirect("learning:room", room_id=session.pk)


@login_required
def attachment(request, message_id):
    msg = get_object_or_404(ChatMessage.objects.select_related("session__swap_request"), pk=message_id)
    swap = msg.session.swap_request
    if request.user.pk not in (swap.from_user_id, swap.to_user_id) or swap.status != SwapRequest.ACCEPTED or blocked_between(swap.from_user_id, swap.to_user_id) or not msg.attachment:
        raise Http404
    try:
        inline = request.GET.get("inline") == "1" and msg.attachment_type in {"image", "audio"}
        safe_inline_types = {"image/jpg": "image/jpeg", "image/jpeg": "image/jpeg", "image/png": "image/png", "image/webp": "image/webp", "audio/mp3": "audio/mpeg", "audio/mpeg": "audio/mpeg", "audio/wav": "audio/wav", "audio/ogg": "audio/ogg", "audio/m4a": "audio/mp4", "audio/webm": "audio/webm"}
        content_type = safe_inline_types.get(msg.attachment_content_type, "application/octet-stream") if inline else "application/octet-stream"
        inline = inline and content_type != "application/octet-stream"
        response = FileResponse(msg.attachment.open("rb"), as_attachment=not inline, filename=msg.attachment_name or "attachment", content_type=content_type)
        response["X-Content-Type-Options"] = "nosniff"
        return response
    except OSError:
        raise Http404
