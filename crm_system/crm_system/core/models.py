from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models import Count, F, Sum, FloatField, ExpressionWrapper

class Customer(models.Model):
    name = models.CharField(max_length=50, verbose_name='客户姓名')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name='地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户管理'

    # ======= 重构后的 RFM 动态评估算法 =======
    
    @property
    def r_score(self):
        """1. 计算 R (跟进动能：时间越近，分值越高)"""
        last_follow = self.followup_set.order_by('-created_at').first()
        if not last_follow:
            return 0
            
        r_days = (timezone.now().date() - last_follow.created_at.date()).days
        
        # 赋分逻辑：7天内得5分，15天内得3分，30天内得1分
        if r_days <= 7: return 5
        elif r_days <= 15: return 3
        elif r_days <= 30: return 1
        return 0

    @property
    def f_score(self):
        """2. 计算 F (有效互动频次：引入防刷逻辑，按日去重统计)"""
        # 利用 TruncDate 将时间戳精确到天，结合 distinct() 过滤同一天的密集无效打卡
        valid_interaction_count = self.followup_set.annotate(
            follow_date=TruncDate('created_at')
        ).values('follow_date').distinct().count()
        
        # 赋分逻辑：10天以上有效互动得5分，5-9天得3分，1-4天得1分
        if valid_interaction_count >= 10: return 5
        elif valid_interaction_count >= 5: return 3
        elif valid_interaction_count >= 1: return 1
        return 0

    @property
    def m_score(self):
        """3. 计算 M (真实商机价值：利用 Django ORM 跨表直接进行 EMV 概率加权)"""
        # 利用 ExpressionWrapper 在数据库引擎层直接计算: 金额 * (概率 / 100)
        emv_result = self.opportunity_set.annotate(
            emv=ExpressionWrapper(
                F('amount') * (F('probability') / 100.0),
                output_field=FloatField()
            )
        ).aggregate(total_emv=Sum('emv'))
        
        total_value = emv_result['total_emv'] or 0
        
        # 赋分逻辑：加权总额超10万得5分，超5万得3分，其余得1分
        if total_value >= 100000: return 5
        elif total_value >= 50000: return 3
        elif total_value > 0: return 1
        return 0

    @property
    def rfm_level(self):
        """4. 价值等级聚合，返回字典供前端直接渲染高亮标签"""
        total_score = self.r_score + self.f_score + self.m_score
        
        if total_score >= 12:
            return {'level_name': '重要价值客户', 'color_code': 'danger', 'score': total_score}
        elif total_score >= 8:
            return {'level_name': '一般保持客户', 'color_code': 'warning', 'score': total_score}
        else:
            return {'level_name': '潜在流失客户', 'color_code': 'info', 'score': total_score}


class FollowUp(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户')
    content = models.TextField(verbose_name='跟进内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='跟进时间')

    def __str__(self):
        return f'{self.customer.name} 跟进记录'
        
    class Meta:
        verbose_name = '客户跟进'
        verbose_name_plural = '客户跟进记录'


class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('clue', '线索'),
        ('talk', '洽谈'),
        ('offer', '报价'),
        ('deal', '成交'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='客户')
    name = models.CharField(max_length=100, verbose_name='商机名称')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, verbose_name='阶段')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='预计金额')
    probability = models.IntegerField(verbose_name='成功概率(%)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = '销售机会'
        verbose_name_plural = '销售机会管理'