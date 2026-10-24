from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserSkill, Certification


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class SkillForm(forms.Form):
    skill = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"placeholder": "e.g. Python, Guitar, French"}))
    kind = forms.ChoiceField(choices=UserSkill.KIND_CHOICES, initial=UserSkill.TEACH)
    level = forms.ChoiceField(choices=UserSkill.LEVELS, initial="beginner")
    def clean_skill(self):
        name = self.cleaned_data["skill"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Skill name must contain at least 2 characters.")
        return name


class ProfileDetailsForm(forms.ModelForm):
    def clean_profile_picture(self):
        image = self.cleaned_data.get("profile_picture")
        if not image:
            return image
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Profile pictures must be 5 MB or smaller.")
        try:
            from PIL import Image, UnidentifiedImageError
            image.seek(0)
            with Image.open(image) as picture:
                if picture.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Use a JPEG, PNG, or WebP image.")
                if picture.width > 6000 or picture.height > 6000:
                    raise forms.ValidationError("Image dimensions must be 6000 × 6000 pixels or smaller.")
                picture.verify()
            image.seek(0)
        except forms.ValidationError:
            raise
        except Exception as exc:
            raise forms.ValidationError("Upload a valid JPEG, PNG, or WebP image.") from exc
        return image

    class Meta:
        model = User
        fields = ("email", "profile_picture", "bio", "linkedin_url", "github_url")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3}), "linkedin_url": forms.URLInput(attrs={"placeholder": "https://linkedin.com/in/your-profile"}), "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/your-username"})}


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ("name", "issuer", "credential_url", "issued_on")
        widgets = {"issued_on": forms.DateInput(attrs={"type": "date"})}
