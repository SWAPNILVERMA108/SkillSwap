from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Skill, User, UserSkill

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Profile", {"fields": ("bio",)}),)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "kind", "level")
    list_filter = ("kind", "level")
    search_fields = ("user__username", "skill__name")

from .models import Certification, Notification, UserBlock
admin.site.register(Certification)
admin.site.register(Notification)
admin.site.register(UserBlock)
