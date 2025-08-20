from django.contrib import admin
from .models import Company, Job, JobCategory


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "status", "created_at")
    list_filter = ("status", "location", "created_at")
    search_fields = ("name", "location", "description")
    ordering = ("-created_at",)

    actions = ["approve_companies", "reject_companies"]

    def approve_companies(self, request, queryset):
        updated = queryset.update(status="approved")
        self.message_user(request, f"{updated} company(ies) approved.")

    def reject_companies(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} company(ies) rejected.")

    approve_companies.short_description = "Approve selected companies"
    reject_companies.short_description = "Reject selected companies"


# You can still register Job & JobCategory as before
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "category", "is_active", "created_at")
    list_filter = ("is_active", "company", "category")
    search_fields = ("title", "description")
    ordering = ("-created_at",)


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
