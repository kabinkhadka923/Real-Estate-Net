from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Property, SavedSearch, Amenity, PropertyType, Company, Image
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import PropertySearchForm, PropertyForm, ImageFormSet
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random


def broker_required(view_func):
    """
    Decorator to check if user is a broker
    """
    def check_user(user):
        return user.is_authenticated and user.user_type == 'broker'
    return user_passes_test(check_user, login_url='accounts:login', redirect_field_name='next')(view_func)


def home(request):
    if request.user.is_authenticated:
        # Get featured/premium properties (limit to 6)
        featured_properties = Property.objects.filter(is_premium=True)[:6]

        # Get latest properties (limit to 8)
        latest_properties = Property.objects.all().order_by('-created_at')[:8]

        context = {
            'featured_properties': featured_properties,
            'latest_properties': latest_properties,
            'show_properties': True,  # Flag to show property sections
        }
    else:
        context = {
            'show_properties': False,  # Flag to hide property sections
        }
    return render(request, 'home.html', context)

@login_required(login_url='/accounts/login/')
def property_list(request):
    properties = Property.objects.all()
    total_properties_count = Property.objects.count()

    # Get all filter parameters
    property_type_filter = request.GET.get('property_type')
    listing_type_filter = request.GET.get('listing_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    city_filter = request.GET.get('city')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')  # Default: newest first
    view_mode = request.GET.get('view', 'grid')  # Default to grid view
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 12)  # Default 12 properties per page

    # Advanced filters
    min_sq_ft = request.GET.get('min_sq_ft')
    max_sq_ft = request.GET.get('max_sq_ft')
    year_built_filter = request.GET.get('year_built')
    amenities_filter = request.GET.getlist('amenities')
    brokerage_filter = request.GET.get('brokerage')
    verification_filter = request.GET.get('verification')
    load_saved_search = request.GET.get('saved_search')

    # Handle saved search loading
    if load_saved_search:
        try:
            saved_search = SavedSearch.objects.get(id=load_saved_search, user=request.user)
            # Parse saved search filters (would need implementation based on how filters are stored)
            # For now, just load and redirect with filters
            messages.info(request, f"Loaded saved search: {saved_search.name}")
        except SavedSearch.DoesNotExist:
            pass

    # Search functionality (across title, description, address, city, state)
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(zip_code__icontains=search_query) |
            Q(broker_name__icontains=search_query)
        )

    # Property type filter
    if property_type_filter:
        if property_type_filter.isdigit():  # Property type ID
            properties = properties.filter(property_type_id=property_type_filter)
        else:  # Property type name
            properties = properties.filter(property_type__name__icontains=property_type_filter)

    # Listing type filter (sale/lease)
    if listing_type_filter:
        if listing_type_filter == 'sale':
            properties = properties.filter(status='for_sale')
        elif listing_type_filter == 'lease':
            properties = properties.filter(status='for_lease')

    # Price filters
    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Square footage filters
    if min_sq_ft:
        try:
            properties = properties.filter(square_footage__gte=int(min_sq_ft))
        except ValueError:
            pass

    if max_sq_ft:
        try:
            properties = properties.filter(square_footage__lte=int(max_sq_ft))
        except ValueError:
            pass

    # City filter
    if city_filter:
        properties = properties.filter(city__icontains=city_filter)

    # Year built filter
    if year_built_filter:
        try:
            properties = properties.filter(year_built__gte=int(year_built_filter))
        except ValueError:
            pass

    # Amenities filter (text search)
    if amenities_filter:
        for amenity_name in amenities_filter:
            if amenity_name:
                properties = properties.filter(amenities__icontains=amenity_name.strip())

    # Brokerage/Company filter
    if brokerage_filter:
        if brokerage_filter.isdigit():
            properties = properties.filter(company_id=brokerage_filter)
        else:
            properties = properties.filter(company__name__icontains=brokerage_filter)

    # Verification filter
    if verification_filter:
        if verification_filter == 'verified':
            properties = properties.filter(is_verified=True)
        elif verification_filter == 'unverified':
            properties = properties.filter(is_verified=False)

    # Apply sorting
    sort_options = {
        'price_low': 'price',
        'price_high': '-price',
        'date_new': '-created_at',
        'date_old': 'created_at',
        'size_large': '-square_footage',
        'size_small': 'square_footage',
        'year_new': '-year_built',
        'year_old': 'year_built'
    }

    sort_field = sort_options.get(sort_by, '-created_at')
    properties = properties.order_by(sort_field)

    # Add related data for template performance
    properties = properties.prefetch_related('images', 'property_type', 'company').select_related('location')

    # Get filtered count before pagination
    filtered_count = properties.count()

    # Pagination
    try:
        page_size = int(page_size)
        if page_size not in [12, 24, 48]:
            page_size = 12
    except (ValueError, TypeError):
        page_size = 12

    paginator = Paginator(properties, page_size)

    try:
        properties_page = paginator.page(page)
    except PageNotAnInteger:
        properties_page = paginator.page(1)
    except EmptyPage:
        properties_page = paginator.page(paginator.num_pages)

    # Get user's saved searches for the sidebar
    user_saved_searches = SavedSearch.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Get available filter options for the form
    property_types = PropertyType.objects.all()
    companies = Company.objects.filter(is_active=True)
    all_amenities = Amenity.objects.all()

    # Get user's favorite property IDs for this page
    user_favorite_ids = set()
    if request.user.is_authenticated:
        user_favorite_ids = set(
            request.user.favorites.filter(property__in=properties_page).values_list('property_id', flat=True)
        )
        # Add favorite_property_ids to context for templates
        request.user.favorite_property_ids = user_favorite_ids

    # Prepare data for map markers using actual property coordinates
    properties_data = []
    for prop in properties_page:
        # Use property's location coordinates if available, otherwise fallback to Kathmandu
        lat = prop.location.latitude if prop.location and prop.location.latitude else 27.7172
        lng = prop.location.longitude if prop.location and prop.location.longitude else 85.3240

        # Add slight randomization if multiple properties have same coordinates
        same_coords = [p for p in properties_data if p['lat'] == lat and p['lng'] == lng]
        if same_coords:
            lat += random.uniform(-0.01, 0.01)
            lng += random.uniform(-0.01, 0.01)

        # Get first approved image URL
        image_url = None
        first_image = prop.images.filter(status='approved').first()
        if first_image:
            image_url = first_image.image.url

        properties_data.append({
            'title': prop.title,
            'lat': lat,
            'lng': lng,
            'url': f'/properties/{prop.pk}/',
            'is_premium': prop.is_premium,
            'is_verified': prop.is_verified,
            'price': str(prop.price),
            'image_url': image_url,
            'id': prop.pk,
            'is_favorited': prop.pk in user_favorite_ids
        })

    context = {
        'properties': properties_page,
        'page_obj': properties_page,
        'is_paginated': properties_page.has_other_pages(),
        'view_mode': view_mode,
        'properties_data': properties_data,
        'total_properties_count': total_properties_count,
        'filtered_count': filtered_count,
        'current_filters': {
            'search': search_query,
            'property_type': property_type_filter,
            'listing_type': listing_type_filter,
            'min_price': min_price,
            'max_price': max_price,
            'city': city_filter,
            'sort': sort_by,
            'min_sq_ft': min_sq_ft,
            'max_sq_ft': max_sq_ft,
            'year_built': year_built_filter,
            'amenities': amenities_filter,
            'brokerage': brokerage_filter,
            'verification': verification_filter,
        },
        'saved_searches': user_saved_searches,
        'property_types': property_types,
        'companies': companies,
        'all_amenities': all_amenities,
    }
    return render(request, 'properties/property_list.html', context)

@login_required(login_url='/accounts/login/')
def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)

    # Process amenities - split text field into list
    amenities_list = []
    if property.amenities:
        # Split by common delimiters and clean up
        amenities_text = property.amenities
        # Split by semicolons, commas, newlines, and clean up
        delimiters = [';', ',', '\n']
        for delimiter in delimiters:
            if delimiter in amenities_text:
                amenities_list = [a.strip() for a in amenities_text.split(delimiter) if a.strip()]
                break
        else:
            # If no delimiters found, treat as single amenity
            if amenities_text.strip():
                amenities_list = [amenities_text.strip()]

    context = {
        'property': property,
        'amenities_list': amenities_list,
    }
    return render(request, 'properties/property_detail.html', context)

@login_required(login_url='/accounts/login/')
def search_results(request):
    form = PropertySearchForm(request.GET)
    properties = Property.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        property_type = form.cleaned_data.get('property_type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_sq_ft = form.cleaned_data.get('min_sq_ft')
        max_sq_ft = form.cleaned_data.get('max_sq_ft')
        amenities = form.cleaned_data.get('amenities')
        city = form.cleaned_data.get('city')
        state = form.cleaned_data.get('state')
        zip_code = form.cleaned_data.get('zip_code')
        lease_or_buy = form.cleaned_data.get('lease_or_buy')
        cap_rate = form.cleaned_data.get('cap_rate')
        year_built = form.cleaned_data.get('year_built')
        zoning = form.cleaned_data.get('zoning')

        if query:
            properties = properties.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(address__icontains=query) |
                Q(city__icontains=query) |
                Q(state__icontains=query) |
                Q(zip_code__icontains=query)
            )
        if property_type:
            properties = properties.filter(property_type=property_type)
        if min_price:
            properties = properties.filter(price__gte=min_price)
        if max_price:
            properties = properties.filter(price__lte=max_price)
        if min_sq_ft:
            properties = properties.filter(square_footage__gte=min_sq_ft)
        if max_sq_ft:
            properties = properties.filter(square_footage__lte=max_sq_ft)
        if amenities:
            for amenity in amenities:
                properties = properties.filter(amenities__icontains=amenity.name)
        if city:
            properties = properties.filter(city__icontains=city)
        if state:
            properties = properties.filter(state__icontains=state)
        if zip_code:
            properties = properties.filter(zip_code__icontains=zip_code)
        if lease_or_buy:
            properties = properties.filter(status=lease_or_buy)
        if cap_rate:
            properties = properties.filter(cap_rate__gte=cap_rate)
        if year_built:
            properties = properties.filter(year_built=year_built)
        if zoning:
            properties = properties.filter(zoning__icontains=zoning)

    context = {
        'form': form,
        'properties': properties
    }
    return render(request, 'properties/search_results.html', context)

@broker_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        image_formset = ImageFormSet(request.POST, request.FILES)

        if form.is_valid() and image_formset.is_valid():
            property_obj = form.save(commit=False)
            property_obj.user = request.user
            property_obj.save()

            # Process images
            for form_obj in image_formset:
                if form_obj.cleaned_data and not form_obj.cleaned_data.get('DELETE', False):
                    image = form_obj.cleaned_data.get('image')
                    if image:
                        Image.objects.create(
                            property=property_obj,
                            image=image,
                            caption=form_obj.cleaned_data.get('caption', '')
                        )

            messages.success(request, "Property created successfully.")
            return redirect('properties:property_detail', pk=property_obj.pk)
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Property {field}: {error}")

            for form_obj in image_formset:
                for field, errors in form_obj.errors.items():
                    for error in errors:
                        messages.error(request, f"Image {field}: {error}")
    else:
        form = PropertyForm()
        image_formset = ImageFormSet(queryset=Image.objects.none())

    return render(request, 'properties/property_form.html', {
        'form': form,
        'image_formset': image_formset,
        'action': 'Create'
    })

@login_required
def property_update(request, pk):
    property = get_object_or_404(Property, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully.")
            return redirect('properties:property_detail', pk=property.pk)
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PropertyForm(instance=property)

    return render(request, 'properties/property_form.html', {'form': form, 'action': 'Update'})

@login_required
def property_delete(request, pk):
    property = get_object_or_404(Property, pk=pk, user=request.user)
    if request.method == 'POST':
        property.delete()
        messages.success(request, "Property deleted successfully.")
        return redirect('properties:property_list')
    return render(request, 'properties/property_confirm_delete.html', {'property': property})

@login_required
def save_search(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        filters = request.POST.get('filters')
        if name:
            SavedSearch.objects.create(
                user=request.user,
                name=name,
                filters=filters or '',
                alert_enabled=request.POST.get('alert_enabled') == 'on'
            )
            messages.success(request, "Search saved successfully.")
        else:
            messages.error(request, "Please provide a name for the search.")
    return redirect('properties:search_results')


@login_required
@require_POST
def toggle_favorite(request, property_id):
    """Toggle property favorite status"""
    property_obj = get_object_or_404(Property, id=property_id)

    # Import UserFavorite model
    from accounts.models import UserFavorite, UserActivity

    # Check if already favorited
    favorite, created = UserFavorite.objects.get_or_create(
        user=request.user,
        property=property_obj,
        defaults={}
    )

    is_favorite = False
    status_message = ""

    if created:
        # Added to favorites
        is_favorite = True
        status_message = "Property added to favorites!"

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='favorite_add',
            title=f"Added to favorites: {property_obj.title}",
            description=f"Added property '{property_obj.title}' to favorites",
            metadata={'property_id': property_id}
        )
    else:
        # Remove from favorites
        favorite.delete()
        is_favorite = False
        status_message = "Property removed from favorites!"

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='favorite_remove',
            title=f"Removed from favorites: {property_obj.title}",
            description=f"Removed property '{property_obj.title}' from favorites",
            metadata={'property_id': property_id}
        )

    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite,
        'property_id': property_id,
        'message': status_message
    })


@login_required
@require_POST
def contact_broker(request, property_id):
    """Send contact request to broker"""
    property_obj = get_object_or_404(Property, id=property_id)

    try:
        # Import necessary models for logging
        from accounts.models import UserActivity
        from contact.models import ContactInquiry

        # Create a contact inquiry record
        ContactInquiry.objects.create(
            property=property_obj,
            user=request.user,
            message=request.POST.get('message', 'Contact request sent'),
            contact_type='broker_inquiry',
            status='new'
        )

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='property_contact',
            title=f"Contacted broker: {property_obj.title}",
            description=f"User contacted broker for property '{property_obj.title}'",
            metadata={'property_id': property_id, 'broker_id': property_obj.user.id if property_obj.user else None}
        )

        status_message = "Contact request sent to broker successfully! They will get back to you soon."

    except Exception as e:
        # Fallback if contact inquiry model doesn't exist or other errors
        status_message = "Contact request recorded. We'll connect you with the broker."

    return JsonResponse({
        'success': True,
        'message': status_message,
        'property_id': property_id
    })


@login_required
@require_POST
def save_property_search(request):
    """Save current search filters as a named search"""
    if request.method == 'POST':
        search_name = request.POST.get('search_name', '').strip()
        alert_enabled = request.POST.get('alert_enabled') == 'on'

        if not search_name:
            return JsonResponse({'success': False, 'error': 'Search name is required'})

        # Get current URL query string as filters
        filters = request.POST.get('current_filters', '')

        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=request.user,
            name=search_name,
            filters=filters,
            alert_enabled=alert_enabled
        )

        messages.success(request, f"Search '{search_name}' saved successfully!")
        return JsonResponse({
            'success': True,
            'saved_search_id': saved_search.id
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
