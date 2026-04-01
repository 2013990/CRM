from django.db import models
from django.utils import timezone
from datetime import timedelta

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

    # ======= RFM 逻辑必须放在 Customer 类里面 =======
    @property
    def rfm_score(self):
        # 1. 计算 R (最近跟进距离天数)，注意这里换成了 created_at
        last_follow = self.followup_set.order_by('-created_at').first()
        if last_follow:
            # 取出日期的天数进行计算
            r_days = (timezone.now().date() - last_follow.created_at.date()).days
        else:
            r_days = 999
        
        # 2. 计算 F (跟进次数/频率)
        f_count = self.followup_set.count()
        
        # 3. 计算 M (潜在成交总额)
        # 注意：如果金额为空，默认算0
        m_amount = sum(opp.amount for opp in self.opportunity_set.all() if opp.amount)

        # 简单的评分逻辑（示例：分值越高越好）
        r_score = 5 if r_days < 7 else (3 if r_days < 30 else 1)
        f_score = 5 if f_count > 5 else (3 if f_count > 2 else 1)
        m_score = 5 if m_amount > 10000 else (3 if m_amount > 1000 else 1)
        
        total = r_score + f_score + m_score
        
        if total >= 12: return "重要价值客户"
        if total >= 8: return "一般保持客户"
        return "潜在流失客户"


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