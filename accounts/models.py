from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('broker', 'Broker'),
        ('buyer', 'Buyer'),
        ('agent', 'Real Estate Agent'),
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='buyer')
    agree_terms = models.BooleanField(default=False)
    terms_accepted_date = models.DateTimeField(null=True, blank=True)

    # Enhanced Profile Fields
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    social_facebook = models.URLField(blank=True, null=True)
    social_linkedin = models.URLField(blank=True, null=True)
    social_twitter = models.URLField(blank=True, null=True)

    # User Preferences
    email_alerts = models.BooleanField(default=True)
    property_notifications = models.BooleanField(default=True)
    newsletter_subscribed = models.BooleanField(default=True)
    preferred_currency = models.CharField(max_length=3, default='NPR')

    # Location Preferences
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)

    # Advanced Features
    is_premium_user = models.BooleanField(default=False)
    premium_expires = models.DateTimeField(null=True, blank=True)
    membership_level = models.CharField(max_length=20, choices=[
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
        ('admin', 'Admin')
    ], default='basic')

    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)

    # Activity Tracking
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Admin System Fields
    is_admin_active = models.BooleanField(default=False, help_text="Whether this admin account is active")
    admin_permissions = models.JSONField(default=dict, blank=True, help_text="JSON object containing admin permissions")

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    @property
    def properties(self):
        return self.property_set.all()

    @property
    def properties_count(self):
        return self.properties.count()

    def is_super_admin(self):
        return self.user_type == 'super_admin' and self.is_admin_active

    def is_normal_admin(self):
        return self.user_type == 'admin' and self.is_admin_active

    def can_manage_properties(self):
        """Check if this admin can manage properties"""
        # Super admin has full access, normal admin checks permissions
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('manage_properties', False)

    def can_manage_users(self):
        """Check if this admin can manage users"""
        # Super admin has full access, normal admin checks permissions
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('manage_users', False)

    def can_manage_premium(self):
        """Check if this admin can manage premium features"""
        # Super admin has full access, normal admin checks permissions
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('manage_premium', False)

    def can_manage_payments(self):
        """Check if this admin can manage payments"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('manage_payments', False)

    def can_manage_system(self):
        """Check if this admin can manage system settings"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('system_settings', False)

    def can_view_logs(self):
        """Check if this admin can view logs"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('view_logs', False)

    def can_delete_data(self):
        """Check if this admin can delete data"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('delete_data', False)

    def can_export_data(self):
        """Check if this admin can export data"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('export_data', False)

    def can_manage_content(self):
        """Check if this admin can manage content"""
        if self.user_type == 'super_admin':
            return True
        return self.is_admin_active and self.admin_permissions.get('manage_content', False)

    def can_manage_admins(self):
        """Check if this admin can manage other admins (Super Admin only)"""
        return self.user_type == 'super_admin'

    def get_admin_permissions(self):
        """Get admin permissions as a dictionary"""
        if not self.is_admin_active:
            return {
                'manage_users': False,
                'manage_properties': False,
                'manage_payments': False,
                'manage_premium': False,
                'manage_admins': False,
                'system_settings': False,
                'view_logs': False,
                'delete_data': False,
                'export_data': False,
                'manage_content': False,
            }
        return self.admin_permissions or {}


class RealEstateAgentApplication(models.Model):
    APPLICATION_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_info', 'Needs More Information'),
    )

    applicant = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_application')
    company_name = models.CharField(max_length=100, help_text="Company/Agency name where you work")
    license_number = models.CharField(max_length=50, help_text="Your real estate license number")
    license_expiry = models.DateField(help_text="License expiry date")
    years_experience = models.PositiveIntegerField(help_text="Years of real estate experience")
    bio = models.TextField(help_text="Brief biography and professional background")
    specializations = models.CharField(max_length=255, blank=True, help_text="Areas of specialization (optional)")
    contact_phone = models.CharField(max_length=20, help_text="Professional contact phone")
    contact_email = models.EmailField(help_text="Professional email address")

    # Document uploads
    license_document = models.FileField(upload_to='licenses/', help_text="Upload your license document (PDF/Image)")
    id_document = models.FileField(upload_to='id_docs/', help_text="Upload government ID (PDF/Image)")
    business_registration = models.FileField(upload_to='business_docs/', blank=True, null=True,
                                           help_text="Business registration document (if applicable)")

    # Application processing
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                  related_name='reviewed_applications')

    # Admin feedback
    admin_feedback = models.TextField(blank=True, help_text="Admin feedback and comments")
    requested_documents = models.TextField(blank=True, help_text="Additional documents requested from applicant")

    def __str__(self):
        return f"Real Estate Agent Application - {self.applicant.username}"

    class Meta:
        ordering = ['-submitted_at']


# Advanced User Features Models
class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')

    def __str__(self):
        return f"{self.user.username} favorite {self.property.title}"

class UserPropertyView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_views')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.property.title}"

class PropertyRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_ratings')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'property')

    def __str__(self):
        return f"{self.user.username} rated {self.property.title}: {self.rating}/5"

    def get_average_rating(self):
        return PropertyRating.objects.filter(property=self.property).aggregate(models.Avg('rating'))['rating__avg'] or 0

class SavedSearchAlert(models.Model):
    saved_search = models.OneToOneField('properties.SavedSearch', on_delete=models.CASCADE, related_name='alerts')
    last_notified_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerts for {self.saved_search.name}"

class PropertyComparison(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comparisons')
    name = models.CharField(max_length=100)
    properties = models.ManyToManyField('properties.Property', related_name='in_comparisons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user.username}'s comparison: {self.name}"

class UserNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_property', 'New Property Added'),
        ('saved_search', 'Saved Search Match'),
        ('favorite_change', 'Favorite Property Update'),
        ('price_alert', 'Price Change Alert'),
        ('system', 'System Notification'),
        ('marketing', 'Marketing & Promotions'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    data = models.JSONField(blank=True, null=True)  # Store additional data like property_id
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('register', 'User Registration'),
        ('property_view', 'Property View'),
        ('property_save', 'Property Saved'),
        ('property_contact', 'Contact Broker'),
        ('search', 'Search Performed'),
        ('favorite_add', 'Added to Favorites'),
        ('favorite_remove', 'Removed from Favorites'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)  # Store additional context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

class MortgageCalculator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mortgage_calculations')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='mortgage_calculations', null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    loan_term_years = models.PositiveIntegerField()
    down_payment = models.DecimalField(max_digits=15, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    total_interest = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mortgage calc for {self.user.username}: NPR {self.monthly_payment}/month"

class PropertyGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    properties = models.ManyToManyField('properties.Property', related_name='groups')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s group: {self.name}"


# ===== ADMIN SYSTEM MODELS =====

class AdminActivityLog(models.Model):
    ACTION_TYPES = [
        ('login', 'Admin Login'),
        ('logout', 'Admin Logout'),
        ('create', 'Create Record'),
        ('update', 'Update Record'),
        ('delete', 'Delete Record'),
        ('approve', 'Approve Item'),
        ('reject', 'Reject Item'),
        ('ban', 'Ban User'),
        ('unban', 'Unban User'),
        ('verify', 'Verify Item'),
        ('refund', 'Process Refund'),
        ('export', 'Export Data'),
        ('settings', 'Change Settings'),
        ('permission', 'Change Permissions'),
    ]

    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField(help_text="Detailed description of the action")
    target_model = models.CharField(max_length=100, blank=True, null=True, help_text="Model affected")
    target_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of affected record")
    ip_address = models.GenericIPAddressField(help_text="IP address of admin")
    user_agent = models.TextField(blank=True, null=True, help_text="Browser/device info")
    device_info = models.JSONField(default=dict, blank=True, help_text="Device details")
    timestamp = models.DateTimeField(default=timezone.now)
    is_high_risk = models.BooleanField(default=False, help_text="High-risk action")

    class Meta:
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['is_high_risk', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.admin.username} - {self.get_action_type_display()} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # Mark high-risk actions
        high_risk_actions = ['delete', 'ban', 'refund', 'permission']
        if self.action_type in high_risk_actions:
            self.is_high_risk = True
        super().save(*args, **kwargs)


class AdminNotification(models.Model):
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    NOTIFICATION_TYPES = [
        ('activity', 'Admin Activity'),
        ('system', 'System Alert'),
        ('security', 'Security Alert'),
        ('payment', 'Payment Alert'),
        ('user', 'User Alert'),
        ('permission_request', 'Permission Request'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='activity')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    related_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notifications')
    related_log = models.ForeignKey(AdminActivityLog, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.related_admin.username}"


class AdminPermissionRequest(models.Model):
    PERMISSION_TYPES = [
        ('manage_users', 'User Management'),
        ('manage_properties', 'Property Management'),
        ('manage_payments', 'Payment Management'),
        ('manage_premium', 'Premium Features Management'),
        ('manage_content', 'Content Management'),
        ('view_logs', 'View System Logs'),
        ('export_data', 'Export Data'),
        ('delete_data', 'Delete Data'),
        ('system_settings', 'System Settings'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    requesting_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_requests')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    reason = models.TextField(help_text="Why do you need this permission?")
    justification = models.TextField(help_text="How will you use this permission responsibly?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='reviewed_permission_requests')
    review_notes = models.TextField(blank=True, help_text="Super Admin review notes")
    granted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Admin Permission Request'
        verbose_name_plural = 'Admin Permission Requests'
        ordering = ['-requested_at']
        unique_together = ('requesting_admin', 'permission_type', 'status')

    def __str__(self):
        return f"{self.requesting_admin.username} - {self.get_permission_type_display()}"

    def approve_request(self, super_admin):
        """Approve the permission request"""
        from django.utils import timezone

        # Update the admin's permissions
        permissions = self.requesting_admin.admin_permissions or {}
        permissions[self.permission_type] = True
        self.requesting_admin.admin_permissions = permissions
        self.requesting_admin.save()

        # Update request status
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = super_admin
        self.granted_at = timezone.now()
        self.save()

        # Log the action
        AdminActivityLog.objects.create(
            admin=super_admin,
            action_type='permission',
            description=f'Granted {self.get_permission_type_display()} permission to {self.requesting_admin.username}',
            target_model='User',
            target_id=self.requesting_admin.id,
            is_high_risk=True
        )

        # Create notification for the requesting admin
        AdminNotification.objects.create(
            title='Permission Request Approved',
            message=f'Your request for {self.get_permission_type_display()} permission has been approved by {super_admin.username}. Please logout and login again to see the changes.',
            notification_type='permission_request',
            priority='high',
            related_admin=self.requesting_admin
        )

    def reject_request(self, super_admin, reason=""):
        """Reject the permission request"""
        from django.utils import timezone

        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = super_admin
        self.review_notes = reason
        self.save()

        # Log the action
        AdminActivityLog.objects.create(
            admin=super_admin,
            action_type='permission',
            description=f'Rejected {self.get_permission_type_display()} permission request from {self.requesting_admin.username}',
            target_model='AdminPermissionRequest',
            target_id=self.id,
            is_high_risk=False
        )

        # Create notification for the requesting admin
        AdminNotification.objects.create(
            title='Permission Request Rejected',
            message=f'Your request for {self.get_permission_type_display()} permission has been rejected by {super_admin.username}. {reason}',
            notification_type='permission_request',
            priority='medium',
            related_admin=self.requesting_admin
        )
