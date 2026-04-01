from django.shortcuts import render
from .models import Customer, Opportunity

def index(request):
    return render(request, 'core/index.html', {
        'customer_count': Customer.objects.count(),
        'opportunity_count': Opportunity.objects.count(),
    })


def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'core/customer_list.html', {
        'customers': customers
    })

def opportunity_list(request):
    opportunities = Opportunity.objects.all()
    return render(request, 'core/opportunity_list.html', {
        'opportunities': opportunities
    })
