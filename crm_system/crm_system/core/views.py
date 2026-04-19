# crm_system/core/views.py
from django.shortcuts import render
from django.db.models import Prefetch
from .models import Customer, FollowUp, Opportunity

def customer_list_view(request):
    """
    面向一线销售人员的客户看板视图
    """
    # 获取所有客户，为避免 N+1 查询问题，可以预加载相关的跟进和商机记录（如果需要进一步优化）
    customers = Customer.objects.all().order_by('-created_at')
    
    # 客户的 rfm_score 是以 @property 形式定义的，所以在模板中可以直接调用 customer.rfm_score
    
    context = {
        'customers': customers,
        'page_title': '我的客户看板 - 智能价值分析'
    }
    return render(request, 'core/customer_list.html', context)