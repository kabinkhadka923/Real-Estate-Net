from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('search/', views.search_results, name='search_results'),
    path('save_search/', views.save_search, name='save_search'),
    path('save_property_search/', views.save_property_search, name='save_property_search'),
    path('<int:property_id>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:property_id>/contact_broker/', views.contact_broker, name='contact_broker'),
    path('create/', views.property_create, name='property_create'),
    path('<int:pk>/update/', views.property_update, name='property_update'),
    path('<int:pk>/delete/', views.property_delete, name='property_delete'),
]
