from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from .models import User, RealEstateAgentApplication, UserActivity
from .forms import AgentApplicationReviewForm

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone_number', 'is_staff', 'is_active', 'is_verified', 'date_joined', 'properties_count')
    list_filter = ('user_type', 'is_staff', 'is_active', 'is_verified', 'date_joined')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('phone_number', 'address', 'user_type')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_date')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('phone_number', 'address', 'user_type')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_date')
        }),
    )

    readonly_fields = ('verification_date',)

    def properties_count(self, obj):
        return obj.properties.count()
    properties_count.short_description = 'Properties Listed'

    actions = ['activate_users', 'deactivate_users', 'verify_agents', 'revoke_verification', 'make_brokers', 'make_buyers', 'make_agents']

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} users activated.")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

    def make_brokers(self, request, queryset):
        queryset.update(user_type='broker')
        self.message_user(request, f"{queryset.count()} users set as brokers.")
    make_brokers.short_description = "Set selected users as brokers"

    def make_buyers(self, request, queryset):
        queryset.update(user_type='buyer')
        self.message_user(request, f"{queryset.count()} users set as buyers.")
    make_buyers.short_description = "Set selected users as buyers"

    def make_agents(self, request, queryset):
        queryset.update(user_type='agent')
        self.message_user(request, f"{queryset.count()} users set as real estate agents.")
    make_agents.short_description = "Set selected users as real estate agents"

    def verify_agents(self, request, queryset):
        from django.utils import timezone
        # Only verify agents and set their accounts as active
        agents_to_verify = queryset.filter(user_type='agent', is_verified=False)
        agents_to_verify.update(is_verified=True, is_active=True, verification_date=timezone.now())
        verified_count = agents_to_verify.count()
        if verified_count > 0:
            self.message_user(request, f"{verified_count} real estate agents verified and activated.")
        else:
            self.message_user(request, "No agents selected or all selected agents are already verified.")
    verify_agents.short_description = "Verify and activate selected real estate agents"

    def revoke_verification(self, request, queryset):
        agents_to_revoke = queryset.filter(user_type='agent', is_verified=True)
        agents_to_revoke.update(is_verified=False, is_active=False, verification_date=None)
        revoked_count = agents_to_revoke.count()
        if revoked_count > 0:
            self.message_user(request, f"Verification revoked for {revoked_count} agents (accounts deactivated).")
        else:
            self.message_user(request, "No verified agents selected.")
    revoke_verification.short_description = "Revoke verification and deactivate selected agents"


@admin.register(RealEstateAgentApplication)
class RealEstateAgentApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'company_name', 'license_number', 'status_badge', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('applicant__username', 'applicant__email', 'company_name', 'license_number')
    readonly_fields = ('submitted_at', 'reviewed_at', 'reviewed_by')
    ordering = ('-submitted_at',)

    fieldsets = (
        ('Application Details', {
            'fields': ('applicant', 'status')
        }),
        ('Professional Information', {
            'fields': ('company_name', 'license_number', 'license_expiry', 'years_experience', 'bio', 'specializations')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'contact_email')
        }),
        ('Documents', {
            'fields': ('license_document', 'id_document', 'business_registration'),
            'classes': ('collapse',)
        }),
        ('Review Process', {
            'fields': ('reviewed_at', 'reviewed_by', 'admin_feedback', 'requested_documents'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'under_review': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'needs_info': '#fd7e14'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 0.8em; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('applicant', 'reviewed_by')

    def save_model(self, request, obj, form, change):
        # Set reviewed_by when admin updates the application
        if change and 'status' in form.changed_data and obj.status != 'pending':
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user

            # If approved, activate the user's account
            if obj.status == 'approved':
                obj.applicant.is_active = True
                obj.applicant.is_verified = True
                obj.applicant.verification_date = timezone.now()
                obj.applicant.save()

                # Log activity
                UserActivity.objects.create(
                    user=obj.applicant,
                    activity_type='register',
                    title='Real Estate Agent Application Approved',
                    description=f'Application approved by {request.user.username}'
                )
            elif obj.status in ['rejected', 'needs_info']:
                # Keep account deactivated until issues are resolved
                obj.applicant.is_active = False
                obj.applicant.is_verified = False
                obj.applicant.save()

        super().save_model(request, obj, form, change)

    actions = ['approve_applications', 'reject_applications', 'request_more_info']

    def approve_applications(self, request, queryset):
        updated = 0
        for application in queryset.filter(status__in=['pending', 'under_review']):
            # Update application
            application.status = 'approved'
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save()

            # Activate user's account
            application.applicant.is_active = True
            application.applicant.is_verified = True
            application.applicant.verification_date = timezone.now()
            application.applicant.save()
            updated += 1

        if updated > 0:
            self.message_user(request, f'{updated} applications approved. Users can now log in and list properties.')
        else:
            self.message_user(request, 'No applications were approved.')
    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'under_review', 'needs_info']).update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        if updated > 0:
            self.message_user(request, f'{updated} applications rejected.')
        else:
            self.message_user(request, 'No applications were rejected.')
    reject_applications.short_description = "Reject selected applications"

    def request_more_info(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'under_review']).update(
            status='needs_info',
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        if updated > 0:
            self.message_user(request, f'{updated} applications marked as needing more information.')
        else:
            self.message_user(request, 'No applications were updated.')
    request_more_info.short_description = "Request more information"
