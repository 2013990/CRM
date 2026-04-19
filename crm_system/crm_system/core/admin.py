from django.contrib import admin
from .models import Customer, FollowUp, Opportunity

# 注册 Customer 模型并自定义展示页
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # list_display 决定了后台列表显示哪些列。我们把 'rfm_level' 加到了最后
    list_display = ('name', 'phone', 'email', 'created_at', 'rfm_level')
    search_fields = ('name', 'phone')  # 增加搜索框
    list_filter = ('created_at',)      # 增加右侧过滤栏

    # 定义 rfm_level 列的显示逻辑
    def rfm_level(self, obj):
        return obj.rfm_score
    
    # 给这一列设置一个中文表头
    rfm_level.short_description = '客户价值等级'


# 注册 FollowUp (跟进记录) 模型
@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('customer', 'content', 'created_at')
    search_fields = ('customer__name', 'content')


# 注册 Opportunity (销售机会) 模型
@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'stage', 'amount', 'probability', 'created_at')
    list_filter = ('stage',)
    search_fields = ('name', 'customer__name')