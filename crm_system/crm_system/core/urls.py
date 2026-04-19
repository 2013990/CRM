# crm_system/core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list_view, name='customer_list'),
    # 其他路由...
]