from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('customers/', views.customer_list, name='customer_list'),
    path('opportunities/', views.opportunity_list, name='opportunity_list'),
]
