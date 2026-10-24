from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Skill, UserSkill, UserBlock, Notification
from .forms import SwapRequestForm
from .models import SwapRequest

User = get_user_model()


@login_required
def matches(request):
    me = request.user
    my_teach_ids = set(me.skills.filter(kind=UserSkill.TEACH).values_list("skill_id", flat=True))
    my_learn_ids = set(me.skills.filter(kind=UserSkill.LEARN).values_list("skill_id", flat=True))

    if not my_teach_ids or not my_learn_ids:
        return render(request, "swaps/matches.html", {
            "matches": [], "need_skills": True,
        })

    blocked_ids = set(UserBlock.objects.filter(blocker=me).values_list("blocked_id", flat=True)) | set(UserBlock.objects.filter(blocked=me).values_list("blocker_id", flat=True))
    relevant = UserSkill.objects.filter(
        Q(kind=UserSkill.TEACH, skill_id__in=my_learn_ids)
        | Q(kind=UserSkill.LEARN, skill_id__in=my_teach_ids)
    ).exclude(user=me).exclude(user_id__in=blocked_ids).select_related("user", "skill")

    by_user = defaultdict(lambda: {"user": None, "can_teach": [], "wants_to_learn": []})
    for entry in relevant:
        row = by_user[entry.user_id]
        row["user"] = entry.user
        if entry.kind == UserSkill.TEACH:
            row["can_teach"].append(entry.skill)
        else:
            row["wants_to_learn"].append(entry.skill)

    results = []
    for row in by_user.values():
        if row["can_teach"] and row["wants_to_learn"]:
            # A valid pair means they want a skill I teach and teach a skill I want.
            pairs = []
            for their_wanted in row["wants_to_learn"]:
                if their_wanted.id in my_teach_ids:
                    for their_teach in row["can_teach"]:
                        if their_teach.id in my_learn_ids:
                            pairs.append((their_wanted, their_teach))
            if pairs:
                # Average ratings are specific to the skill this user teaches.
                from learning.models import SessionRating
                for skill in row["can_teach"]:
                    agg = SessionRating.objects.filter(reviewee=row["user"], skill=skill).aggregate(avg=Avg("score"), count=Count("id"))
                    skill.avg_rating = agg["avg"]
                    skill.rating_count = agg["count"]
                row["pairs"] = pairs
                results.append(row)

    return render(request, "swaps/matches.html", {
        "matches": results, "need_skills": False,
    })


@login_required
@require_POST
def send_request(request):
    form = SwapRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid swap request.")
        return redirect("swaps:matches")

    data = form.cleaned_data
    to_user = get_object_or_404(User, pk=data["to_user"])
    offered = get_object_or_404(Skill, pk=data["skill_offered"])
    wanted = get_object_or_404(Skill, pk=data["skill_wanted"])

    if UserBlock.objects.filter(blocker=request.user, blocked=to_user).exists() or UserBlock.objects.filter(blocker=to_user, blocked=request.user).exists():
        messages.error(request, "You cannot send a request because one of you has blocked the other.")
        return redirect("swaps:matches")

    if to_user == request.user:
        messages.error(request, "You cannot send a request to yourself.")
        return redirect("swaps:matches")

    if not request.user.skills.filter(skill=offered, kind=UserSkill.TEACH).exists():
        messages.error(request, "You do not teach the offered skill.")
        return redirect("swaps:matches")
    if not to_user.skills.filter(skill=offered, kind=UserSkill.LEARN).exists():
        messages.error(request, "The other user does not want to learn your offered skill.")
        return redirect("swaps:matches")
    if not to_user.skills.filter(skill=wanted, kind=UserSkill.TEACH).exists():
        messages.error(request, "The other user does not teach the requested skill.")
        return redirect("swaps:matches")
    if not request.user.skills.filter(skill=wanted, kind=UserSkill.LEARN).exists():
        messages.error(request, "You do not want to learn that skill.")
        return redirect("swaps:matches")

    try:
        obj, created = SwapRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user,
            skill_offered=offered,
            skill_wanted=wanted,
            defaults={"message": data.get("message", "").strip()},
        )
    except IntegrityError:
        created = False
        obj = SwapRequest.objects.filter(
            from_user=request.user, to_user=to_user,
            skill_offered=offered, skill_wanted=wanted,
        ).first()

    if created:
        Notification.objects.create(recipient=to_user, actor=request.user, message=f"{request.user.username} sent you a skill-swap request.", url="/requests/")
        messages.success(request, "Swap request sent.")
    elif obj and obj.status == SwapRequest.REJECTED:
        obj.status = SwapRequest.PENDING
        obj.message = data.get("message", "").strip()
        obj.save(update_fields=["status", "message", "updated_at"])
        messages.success(request, "Swap request sent again.")
    else:
        messages.info(request, "You already have a request for this skill pair.")
    return redirect("swaps:requests")


@login_required
def requests_list(request):
    incoming = SwapRequest.objects.filter(to_user=request.user).select_related(
        "from_user", "skill_offered", "skill_wanted"
    )
    outgoing = SwapRequest.objects.filter(from_user=request.user).select_related(
        "to_user", "skill_offered", "skill_wanted"
    )
    return render(request, "swaps/requests.html", {"incoming": incoming, "outgoing": outgoing})


@login_required
@require_POST
def update_request(request, pk, action):
    req = get_object_or_404(SwapRequest, pk=pk)
    if action in {"accept", "reject"} and req.to_user == request.user and req.status == SwapRequest.PENDING:
        req.status = SwapRequest.ACCEPTED if action == "accept" else SwapRequest.REJECTED
        req.save(update_fields=["status", "updated_at"])
        Notification.objects.create(recipient=req.from_user, actor=request.user, message=f"{request.user.username} {action}ed your skill-swap request.", url="/requests/")
        messages.success(request, f"Request {action}ed.")
    elif action == "complete" and request.user in {req.from_user, req.to_user} and req.status == SwapRequest.ACCEPTED:
        req.status = SwapRequest.COMPLETED
        req.save(update_fields=["status", "updated_at"])
        messages.success(request, "Swap marked as completed.")
    else:
        messages.error(request, "That action is not allowed for this request.")
    return redirect("swaps:requests")
