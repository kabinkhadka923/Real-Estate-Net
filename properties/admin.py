from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, Q
from django.contrib import messages
import json
import csv
import datetime
from .models import Property, PropertyType, Amenity, Image, SavedSearch, Company, Location

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('get_thumbnail', 'title', 'user', 'property_type', 'city', 'format_price', 'format_status', 'is_premium', 'created_at', 'admin_actions')
    list_display_links = ('get_thumbnail', 'title')
    list_filter = ('property_type', 'status', 'is_premium', 'is_verified', 'created_at', 'state')
    search_fields = ('title', 'description', 'city', 'state', 'user__username', 'user__email', 'broker_name')
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large', 'property_actions', 'verification_status')
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('title', 'description', 'property_type', 'user')
        }),
        ('📍 Location', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country')
        }),
        ('🏠 Property Details', {
            'fields': ('price', 'square_footage', 'lot_size', 'year_built', 'zoning', 'status')
        }),
        ('📞 Contact Information', {
            'fields': ('broker_name', 'broker_email', 'broker_phone')
        }),
        ('🖼️ Media & Images', {
            'fields': ('image_preview_large', 'virtual_tour_url', 'floor_plan_image')
        }),
        ('✅ Verification & Status', {
            'fields': ('verification_status', 'is_premium', 'is_verified')
        }),
        ('⚡ Actions', {
            'fields': ('property_actions',),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_per_page = 25
    ordering = ('-created_at',)

    # Enhanced formatters for list display
    def get_thumbnail(self, obj):
        """Display property thumbnail"""
        if obj.images.exists():
            image = obj.images.first()
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                             image.image.url)
        elif obj.floor_plan_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                             obj.floor_plan_image.url)
        return format_html('<div style="width: 50px; height: 50px; background: {} ; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🏠</div>',
                          'linear-gradient(135deg, var(--nepal-blue), var(--nepal-crimson))')
    get_thumbnail.short_description = "Image"

    def format_price(self, obj):
        """Format price with Nepali Rupee symbol"""
        return f"NPR {obj.price:,.0f}"
    format_price.short_description = "Price (NPR)"
    format_price.admin_order_field = 'price'

    def format_status(self, obj):
        """Format status with color coding"""
        status_colors = {
            'for_sale': ('green', 'available'),
            'for_lease': ('blue', 'for rent'),
            'sold': ('red', 'sold'),
            'leased': ('purple', 'leased'),
            'pending': ('orange', 'under review'),
            'under_contract': ('orange', 'contract'),
            'off_market': ('gray', 'off market')
        }
        color, label = status_colors.get(obj.status, ('gray', obj.status))
        return format_html('<span style="background: {}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; font-weight: 600; text-transform: uppercase;">{}</span>',
                          color, label.replace('_', ' '))
    format_status.short_description = "Status"

    def is_verified(self, obj):
        """Display verification status with better icons"""
        if obj.user.is_staff or obj.user.is_superuser:
            return format_html('<span style="color: green;">✅ Admin</span>')
        elif obj.user.user_type == 'broker':
            return format_html('<span style="color: blue;">🏢 Broker</span>')
        else:
            return format_html('<span style="color: #6c757d;">👤 User</span>')
    is_verified.short_description = "User Type"

    def property_actions(self, obj):
        """Show property actions in detail view"""
        view_url = obj.get_absolute_url()
        edit_url = f'/real-admin/properties/property/{obj.pk}/change/'

        return format_html(
            '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
            '<a href="{}" target="_blank" style="background: #17a2b8; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px;">👀 View</a>'
            '<a href="{}" target="_blank" style="background: #6c757d; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px;">✏️ Edit</a>'
            '<button onclick="deleteProperty({})" style="background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">🗑️ Delete</button>'
            '</div>'
            '<script>'
            'function deleteProperty(id) {'
            '  if (confirm("Are you sure you want to DELETE this property?\\n\\nThis action cannot be undone and will delete all associated images and data.")) {'
    '    fetch("/real-admin/properties/property/" + id + "/delete/", {'
            '      method: "POST",'
            '      headers: {'
            '        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,'
            '        "Content-Type": "application/json"'
            '      }'
            '    }).then(response => {'
            '      if (response.ok) {'
            '        location.reload();'
            '      } else {'
            '        alert("Error deleting property");'
            '      }'
            '    });'
            '  }'
            '}'
            '</script>'
        )
    property_actions.short_description = "Quick Actions"

    def admin_actions(self, obj):
        """Action buttons in list view"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="{}" target="_blank" title="View Property" style="background: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">👀</a>'
            '<a href="/real-admin/properties/property/{}/change/" title="Edit Property" style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">✏️</a>'
            '<a href="/real-admin/properties/property/{}/delete/" title="Delete Property (Superuser Only)" style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">🗑️</a>'
            '</div>',
            obj.get_absolute_url(),
            obj.pk,
            obj.pk
        )
    admin_actions.short_description = "Actions"

    def image_preview_large(self, obj):
        """Show larger image preview in detail view"""
        if obj.images.exists():
            return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px;" />',
                             obj.images.first().image.url)
        return "No images available"
    image_preview_large.short_description = "Images"

    def verification_status(self, obj):
        """Show detailed verification status"""
        user = obj.user
        status_info = []

        if user.is_superuser:
            status_info.append(('👑 Super Admin', 'darkgreen'))
        elif user.is_staff:
            status_info.append(('👮 Admin', 'darkblue'))
        elif user.user_type == 'broker':
            status_info.append(('🏢 Real Estate Broker', 'blue'))
        elif user.user_type == 'buyer':
            status_info.append(('👥 Property Buyer', 'green'))
        else:
            status_info.append(('👤 Regular User', 'gray'))

        if obj.is_verified:
            status_info.append(('✅ Property Verified', 'green'))
        else:
            status_info.append(('❌ Property Not Verified', 'orange'))

        if obj.is_premium:
            status_info.append(('⭐ Premium Listing', 'gold'))

        html = '<div style="line-height: 1.6;">'
        for text, color in status_info:
            html += f'<span style="color: {color}; margin-right: 15px;">{text}</span>'
        html += '</div>'

        return format_html(html)
    verification_status.short_description = "Verification & Status"

    def is_verified(self, obj):
        return "✅ Verified" if obj.user.is_staff or obj.user.is_superuser else "❌ Unverified"
    is_verified.short_description = "Verification Status"

    def company_name(self, obj):
        return obj.company.name if obj.company else "No Company"
    company_name.short_description = "Company"

    def location_name(self, obj):
        return obj.location.name if obj.location else "No Location"
    location_name.short_description = "Location"

    actions = ['delete_selected_properties', 'mark_as_verified', 'mark_as_premium', 'remove_premium', 'export_properties', 'bulk_update_status']

    def delete_selected_properties(self, request, queryset):
        """Admin bulk delete properties with confirmation"""
        properties_count = queryset.count()
        properties_list = list(queryset.values_list('title', flat=True))[:10]  # Show first 10

        if 'confirm_delete' in request.POST:
            # Actually delete the properties
            deleted_count = 0
            for property_obj in queryset:
                property_obj.delete()
                deleted_count += 1
            self.message_user(request,
                f"🗑️ Successfully deleted {deleted_count} properties and all associated images.")
            return

        # Show confirmation page
        context = {
            'title': 'Confirm Property Deletion',
            'queryset': queryset,
            'properties_count': properties_count,
            'properties_list': properties_list,
            'opts': self.model._meta,
            'action_name': 'delete_selected_properties',
            'media': self.media,
        }
        return render(request, 'admin/properties/confirm_delete_properties.html', context)
    delete_selected_properties.short_description = "🗑️ Delete selected properties (Admin Only)"

    def get_actions(self, request):
        """Only show delete action to superusers"""
        actions = super().get_actions(request)
        if not request.user.user_type == 'super_admin':
            if 'delete_selected_properties' in actions:
                del actions['delete_selected_properties']
        return actions

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete properties"""
        return request.user.user_type == 'super_admin'

    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} properties marked as verified.")
    mark_as_verified.short_description = "Verify selected properties"

    def mark_as_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} properties marked as premium.")
    mark_as_premium.short_description = "Make premium"

    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} properties removed from premium.")
    remove_premium.short_description = "Remove premium status"

    def export_properties(self, request, queryset):
        # Export selected properties to CSV
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="properties_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Title', 'User', 'Type', 'City', 'State', 'Price', 'Status', 'Premium', 'Verified', 'Created'])

        for property in queryset:
            writer.writerow([
                property.title,
                property.user.username,
                property.property_type.name if property.property_type else '',
                property.city,
                property.state,
                property.price,
                property.status,
                'Yes' if property.is_premium else 'No',
                'Yes' if property.is_verified else 'No',
                property.created_at.strftime('%Y-%m-%d %H:%M')
            ])

        self.message_user(request, f"Exported {queryset.count()} properties to CSV.")
    export_properties.short_description = "Export to CSV"

    def bulk_update_status(self, request, queryset):
        # Bulk update property status
        from django.contrib.admin.helpers import Fieldset
        from django import forms

        if 'apply' in request.POST:
            new_status = request.POST.get('status')
            queryset.update(status=new_status)
            self.message_user(request, f"Updated status to '{new_status}' for {queryset.count()} properties.")
            return

        # Show a form to select new status
        form = forms.Form()
        form.fields['status'] = forms.ChoiceField(
            choices=[('for_sale', 'For Sale'), ('for_lease', 'For Lease'), ('sold', 'Sold'), ('leased', 'Leased')],
            widget=forms.Select(attrs={'class': 'form-control'})
        )

        return self.render_change_form(request, {'form': form, 'selected_items': queryset})
    bulk_update_status.short_description = "Update property status"

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('image_thumbnail', 'property', 'caption', 'status', 'file_size_display', 'dimensions', 'is_fake_suspected', 'created_at')
    list_filter = ('status', 'is_duplicate', 'created_at', 'property__city', 'property__state')
    search_fields = ('property__title', 'caption', 'flagged_reason', 'moderation_notes')
    readonly_fields = ('created_at', 'updated_at', 'file_size', 'width', 'height', 'image_preview')
    actions = ['approve_images', 'reject_images', 'flag_for_review', 'soft_delete_images', 'mark_as_duplicate', 'restore_images']
    list_per_page = 25

    fieldsets = (
        ('📸 Image Information', {
            'fields': ('property', 'image', 'image_preview', 'caption')
        }),
        ('📊 Image Metadata', {
            'fields': ('file_size', 'width', 'height', 'dimensions'),
            'classes': ('collapse',)
        }),
        ('🚩 Moderation Status', {
            'fields': ('status', 'flagged_reason', 'flagged_by', 'flagged_at', 'moderation_notes', 'moderated_by', 'moderated_at')
        }),
        ('🗑️ Deletion Tracking', {
            'fields': ('deleted_at', 'deleted_by', 'deletion_reason'),
            'classes': ('collapse',)
        }),
        ('🔍 Duplicate Detection', {
            'fields': ('is_duplicate', 'duplicate_of'),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_thumbnail(self, obj):
        """Display thumbnail image in admin list"""
        if obj.image:
            return f'<img src="{obj.image.url}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />'
        return "No Image"
    image_thumbnail.short_description = "Image"
    image_thumbnail.allow_tags = True

    def image_preview(self, obj):
        """Display full-size image preview in admin detail"""
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 400px; max-height: 400px; object-fit: contain;" />'
        return "No Image"
    image_preview.short_description = "Image Preview"
    image_preview.allow_tags = True

    def file_size_display(self, obj):
        """Display human-readable file size"""
        if obj.file_size:
            size = obj.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "Unknown"
    file_size_display.short_description = "Size"

    def dimensions(self, obj):
        """Display image dimensions"""
        if obj.width and obj.height:
            return f"{obj.width}×{obj.height}"
        return "Unknown"
    dimensions.short_description = "Dimensions"

    def is_fake_suspected(self, obj):
        """Display fake suspicion status"""
        if obj.is_fake_suspected():
            return "⚠️ Suspected"
        return "✅ OK"
    is_fake_suspected.short_description = "Fake Check"

    def approve_images(self, request, queryset):
        """Bulk approve selected images"""
        count = 0
        for image in queryset:
            if image.status != 'approved':
                image.approve_image(request.user)
                count += 1
        self.message_user(request, f"✅ Approved {count} images.")
    approve_images.short_description = "Approve selected images"

    def reject_images(self, request, queryset):
        """Bulk reject selected images"""
        count = 0
        for image in queryset:
            if image.status != 'rejected':
                image.reject_image(request.user, "Bulk rejection by admin")
                count += 1
        self.message_user(request, f"❌ Rejected {count} images.")
    reject_images.short_description = "Reject selected images"

    def flag_for_review(self, request, queryset):
        """Bulk flag images for review"""
        count = 0
        for image in queryset:
            if image.status != 'flagged':
                image.flag_for_review(request.user, "Bulk flagged for review")
                count += 1
        self.message_user(request, f"🚩 Flagged {count} images for review.")
    flag_for_review.short_description = "Flag selected images for review"

    def soft_delete_images(self, request, queryset):
        """Bulk soft delete images"""
        count = 0
        for image in queryset:
            if image.status != 'deleted':
                image.soft_delete(request.user, "Bulk deletion by admin")
                count += 1
        self.message_user(request, f"🗑️ Soft deleted {count} images.")
    soft_delete_images.short_description = "Soft delete selected images"

    def mark_as_duplicate(self, request, queryset):
        """Mark selected images as duplicates"""
        if len(queryset) < 2:
            self.message_user(request, "⚠️ Please select at least 2 images to mark as duplicates.", level='warning')
            return

        # Mark all but the first as duplicates of the first
        images_list = list(queryset)
        master_image = images_list[0]

        count = 0
        for image in images_list[1:]:
            image.is_duplicate = True
            image.duplicate_of = master_image
            image.save()
            count += 1

        self.message_user(request, f"📋 Marked {count} images as duplicates of {master_image}.")
    mark_as_duplicate.short_description = "Mark selected as duplicates"

    def restore_images(self, request, queryset):
        """Restore deleted images"""
        count = 0
        for image in queryset:
            if image.status == 'deleted':
                image.restore_image(request.user)
                count += 1
        self.message_user(request, f"🔄 Restored {count} images.")
    restore_images.short_description = "Restore selected images"

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'property', 'flagged_by', 'moderated_by', 'deleted_by'
        )

    def save_model(self, request, obj, form, change):
        """Override save to ensure metadata is populated"""
        super().save_model(request, obj, form, change)
        # Trigger metadata population if image was uploaded
        if 'image' in form.changed_data:
            obj.save()  # Re-save to populate metadata

    def get_urls(self):
        """Add custom URLs for image moderation"""
        urls = super().get_urls()
        custom_urls = [
            path('review-queue/', self.image_review_queue, name='properties_image_review_queue'),
            path('fake-detection/', self.run_fake_detection, name='properties_fake_detection'),
        ]
        return custom_urls + urls

    def image_review_queue(self, request):
        """Display images flagged for review"""
        flagged_images = Image.objects.filter(status='flagged').select_related('property', 'flagged_by')

        context = {
            'title': 'Image Review Queue',
            'flagged_images': flagged_images,
            'total_flagged': flagged_images.count(),
        }
        return render(request, 'admin/properties/image_review_queue.html', context)

    def run_fake_detection(self, request):
        """Run fake image detection on all images"""
        from .utils import detect_fake_images

        if request.method == 'POST':
            # Run detection
            flagged_count = detect_fake_images()

            self.message_user(
                request,
                f"🔍 Fake detection complete. {flagged_count} images flagged for review."
            )
            return redirect('admin:properties_image_changelist')

        context = {
            'title': 'Run Fake Image Detection',
            'description': 'This will scan all property images and flag suspicious ones for review.',
        }
        return render(request, 'admin/properties/fake_detection.html', context)

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'alert_enabled', 'created_at')
    list_filter = ('alert_enabled', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'logo', 'description')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website', 'address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_companies', 'deactivate_companies']

    def activate_companies(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} companies activated.")
    activate_companies.short_description = "Activate selected companies"

    def deactivate_companies(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} companies deactivated.")
    deactivate_companies.short_description = "Deactivate selected companies"

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'state', 'country', 'is_active')
    list_filter = ('type', 'state', 'country', 'is_active')
    search_fields = ('name', 'state', 'country')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'state', 'country')
        }),
        ('Geographic Data', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    actions = ['activate_locations', 'deactivate_locations']

    def activate_locations(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} locations activated.")
    activate_locations.short_description = "Activate selected locations"

    def deactivate_locations(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} locations deactivated.")
    deactivate_locations.short_description = "Deactivate selected locations"
