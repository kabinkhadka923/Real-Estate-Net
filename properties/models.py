from django.db import models
from django.conf import settings
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=(
        ('city', 'City'),
        ('district', 'District'),
        ('region', 'Region'),
        ('neighborhood', 'Neighborhood'),
    ))
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'type', 'state')

    def __str__(self):
        return f"{self.name} ({self.type})"

class PropertyType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    filters = models.TextField()  # Store URL encoded query string
    alert_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} by {self.user.username}"

class Property(models.Model):
    PROPERTY_STATUS_CHOICES = (
        ('for_sale', 'For Sale'),
        ('for_lease', 'For Lease'),
        ('sold', 'Sold'),
        ('leased', 'Leased'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, related_name='properties')
    address = models.CharField(max_length=255)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    square_footage = models.IntegerField(blank=True, null=True)
    lot_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    year_built = models.IntegerField(blank=True, null=True)
    zoning = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PROPERTY_STATUS_CHOICES, default='for_sale')
    amenities = models.TextField(blank=True, null=True, help_text="Enter custom amenities (one per line or comma-separated)")
    
    # Financial Data
    cap_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    noi = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True) # Net Operating Income
    rent_roll = models.TextField(blank=True, null=True) # Can be a JSON field or a separate model if complex
    expense_summaries = models.TextField(blank=True, null=True) # Can be a JSON field or a separate model if complex

    # Contact Information
    broker_name = models.CharField(max_length=255, blank=True, null=True)
    broker_email = models.EmailField(blank=True, null=True)
    broker_phone = models.CharField(max_length=20, blank=True, null=True)

    # Multimedia
    virtual_tour_url = models.URLField(blank=True, null=True)
    floor_plan_image = models.ImageField(upload_to='floor_plans/', blank=True, null=True)

    # Premium status
    is_premium = models.BooleanField(default=False)

    # Verification status
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the URL for this property's detail page"""
        from django.urls import reverse
        return reverse('properties:property_detail', kwargs={'pk': self.pk})

class Image(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    caption = models.CharField(max_length=255, blank=True, null=True)

    # Moderation fields
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
        ('deleted', 'Deleted'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderation_notes = models.TextField(blank=True, null=True)
    flagged_reason = models.CharField(max_length=255, blank=True, null=True)
    flagged_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='flagged_images')
    flagged_at = models.DateTimeField(null=True, blank=True)

    # Validation fields
    file_size = models.PositiveIntegerField(null=True, blank=True)  # File size in bytes
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')

    # Audit fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_images')
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_images')
    deletion_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['flagged_by', 'status']),
        ]

    def __str__(self):
        return f"Image for {self.property.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-populate image metadata
        if self.image:
            try:
                from PIL import Image as PILImage
                img = PILImage.open(self.image)
                self.width, self.height = img.size
                self.file_size = self.image.size
            except Exception:
                pass  # Handle cases where PIL can't read the image

        super().save(*args, **kwargs)

    def is_fake_suspected(self):
        """Check if image is suspected to be fake based on various criteria"""
        suspicious_indicators = 0

        # Check file size (too small might be fake)
        if self.file_size and self.file_size < 10240:  # Less than 10KB
            suspicious_indicators += 1

        # Check dimensions (too small might be fake)
        if self.width and self.height:
            if self.width < 300 or self.height < 300:
                suspicious_indicators += 1

        # Check if marked as duplicate
        if self.is_duplicate:
            suspicious_indicators += 1

        # Check if flagged
        if self.status == 'flagged':
            suspicious_indicators += 1

        return suspicious_indicators >= 2

    def flag_for_review(self, admin_user, reason):
        """Flag image for admin review"""
        from django.utils import timezone
        self.status = 'flagged'
        self.flagged_reason = reason
        self.flagged_by = admin_user
        self.flagged_at = timezone.now()
        self.save()

    def approve_image(self, admin_user):
        """Approve image after review"""
        from django.utils import timezone
        self.status = 'approved'
        self.moderated_at = timezone.now()
        self.moderated_by = admin_user
        self.save()

    def reject_image(self, admin_user, reason=None):
        """Reject image after review"""
        from django.utils import timezone
        self.status = 'rejected'
        self.moderation_notes = reason
        self.moderated_at = timezone.now()
        self.moderated_by = admin_user
        self.save()

    def soft_delete(self, admin_user, reason=None):
        """Soft delete image (mark as deleted but keep in database)"""
        from django.utils import timezone
        self.status = 'deleted'
        self.deleted_at = timezone.now()
        self.deleted_by = admin_user
        self.deletion_reason = reason
        self.save()

    def restore_image(self, admin_user):
        """Restore a deleted image"""
        self.status = 'approved'
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None
        self.save()
