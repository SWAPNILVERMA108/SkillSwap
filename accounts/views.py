from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import RegisterForm, SkillForm, ProfileDetailsForm, CertificationForm
from .models import Skill, UserSkill, Certification, Notification, UserBlock


def register(request):
    if request.user.is_authenticated:
        return redirect("swaps:matches")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(); login(request, user)
        messages.success(request, "Your account has been created.")
        return redirect("accounts:profile")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    skill_form = SkillForm(request.POST or None, prefix="skill")
    details_form = ProfileDetailsForm(
        request.POST or None, request.FILES or None, instance=request.user, prefix="details"
    )
    cert_form = CertificationForm(request.POST or None, prefix="cert")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "details" and details_form.is_valid():
            details_form.save(); messages.success(request, "Profile details updated."); return redirect("accounts:profile")
        if action == "certification" and cert_form.is_valid():
            cert = cert_form.save(commit=False); cert.user = request.user; cert.save()
            messages.success(request, "Certification added."); return redirect("accounts:profile")
        if action == "skill" and skill_form.is_valid():
            name = skill_form.cleaned_data["skill"].strip()
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                try: skill = Skill.objects.create(name=name)
                except IntegrityError: skill = Skill.objects.get(name__iexact=name)
            UserSkill.objects.get_or_create(user=request.user, skill=skill, kind=skill_form.cleaned_data["kind"], defaults={"level": skill_form.cleaned_data["level"]})
            messages.success(request, "Skill added to your profile."); return redirect("accounts:profile")
    teach = request.user.skills.filter(kind=UserSkill.TEACH).select_related("skill")
    learn = request.user.skills.filter(kind=UserSkill.LEARN).select_related("skill")
    return render(request, "accounts/profile.html", {"form": skill_form, "details_form": details_form, "cert_form": cert_form, "teach": teach, "learn": learn, "certifications": request.user.certifications.all()})


@login_required
@require_POST
def remove_skill(request, pk):
    get_object_or_404(UserSkill, pk=pk, user=request.user).delete()
    messages.success(request, "Skill removed."); return redirect("accounts:profile")


@login_required
@require_POST
def remove_certification(request, pk):
    get_object_or_404(Certification, pk=pk, user=request.user).delete()
    messages.success(request, "Certification removed."); return redirect("accounts:profile")


@login_required
def notifications(request):
    items = request.user.notifications.select_related("actor")[:100]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {"notifications": items})


@login_required
@require_POST
def block_user(request, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, "You cannot block yourself.")
    else:
        UserBlock.objects.get_or_create(blocker=request.user, blocked=target)
        messages.success(request, f"{target.username} has been blocked. Their chat and new requests are disabled for you.")
    return redirect(request.POST.get("next") or "swaps:requests")


@login_required
@require_POST
def unblock_user(request, user_id):
    UserBlock.objects.filter(blocker=request.user, blocked_id=user_id).delete()
    messages.success(request, "User unblocked.")
    return redirect("accounts:profile")
