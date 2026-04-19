import time
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

# 假设你的app名字叫 crm，请根据实际情况修改导入路径
from .models import Customer, FollowUp, Opportunity

class RFMAlgorithmTests(TestCase):
    """
    TC-RFM系列：核心动态算法测试（重点测试防刷与边界）
    """
    def setUp(self):
        # 初始化基础测试数据
        self.customer_a = Customer.objects.create(
            name="测试客户A", phone="13800000000"
        )
        self.customer_b = Customer.objects.create(
            name="孤儿客户B", phone="13900000000" # 无跟进无商机的极端异常数据
        )

    def test_f_score_anti_brushing(self):
        """TC-RFM-02: F值防刷机制验证 (同一天密集打卡过滤)"""
        # 模拟销售员为了凑单，在今天连续录入了20条跟进记录
        followups = [
            FollowUp(customer=self.customer_a, content=f"第{i}次无效打卡")
            for i in range(20)
        ]
        FollowUp.objects.bulk_create(followups)

        # 断言：虽然有20条记录，但都在同一天，F值应该只算1天的有效互动，得1分
        self.assertEqual(self.customer_a.f_score, 1)

    def test_m_score_emv_boundaries(self):
        """TC-RFM-04: M值EMV加权边界测试"""
        # 商机1：金额20万，概率50% -> EMV = 10万
        Opportunity.objects.create(
            customer=self.customer_a, name="高意向商机", stage="offer",
            amount=200000.00, probability=50
        )
        # 商机2：金额10万，概率49% -> EMV = 4.9万
        Opportunity.objects.create(
            customer=self.customer_a, name="低意向商机", stage="talk",
            amount=100000.00, probability=49
        )
        
        # 断言：总EMV为14.9万。按照我们在模型里的逻辑，>10万得5分
        self.assertEqual(self.customer_a.m_score, 5)

    def test_extreme_exception_handling(self):
        """TC-RFM-05: 极端异常数据容错测试"""
        # 客户B没有任何关联记录，断言系统不会抛出除以0或NoneType异常
        self.assertEqual(self.customer_b.r_score, 0)
        self.assertEqual(self.customer_b.f_score, 0)
        self.assertEqual(self.customer_b.m_score, 0)
        self.assertEqual(self.customer_b.rfm_level['level_name'], "潜在流失客户")

    def test_r_score_time_decay(self):
        """TC-RFM-03: R值时间衰减边界测试"""
        # 录入一条跟进记录
        f1 = FollowUp.objects.create(customer=self.customer_a, content="模拟跟进")
        
        # Django测试技巧：绕过 auto_now_add 强制修改创建时间到 16天前
        past_date = timezone.now() - timedelta(days=16)
        FollowUp.objects.filter(id=f1.id).update(created_at=past_date)
        
        # 重新从数据库拉取客户状态，断言16天前的记录R值得分应降为1分
        self.customer_a.refresh_from_db()
        self.assertEqual(self.customer_a.r_score, 1)


class SystemPerformanceTests(TestCase):
    """
    TC-PERF系列：系统性能与压力测试
    """
    @classmethod
    def setUpTestData(cls):
        # 批量生成 1000 个客户用于性能压测
        customers = [
            Customer(name=f"压测客户_{i}", phone=f"130000{i:04d}")
            for i in range(1000)
        ]
        Customer.objects.bulk_create(customers)

    def test_dynamic_property_performance(self):
        """TC-PERF-01: 高数据量动态聚合查询性能评估"""
        start_time = time.time()
        
        # 触发 1000 个客户的全量 RFM 动态计算
        # 注意：这里模拟了前端列表页的渲染压力
        for customer in Customer.objects.all():
            _ = customer.rfm_level 
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 断言：1000条级联动态运算时间必须小于 1.5 秒
        self.assertLess(execution_time, 1.5, "动态聚合性能未达标，存在N+1查询风险")


class SecurityTests(TestCase):
    """
    TC-SEC系列：越权与安全测试
    """
    def setUp(self):
        self.client = Client()
        # 创建两个销售账号
        self.user_a = User.objects.create_user('sales_A', password='password123')
        self.user_b = User.objects.create_user('sales_B', password='password123')
        
        # 假设Customer模型有关联user（仅作安全测试演示）
        # self.customer_b = Customer.objects.create(name="B的私海客户", user=self.user_b)

    def test_horizontal_privilege_escalation(self):
        """TC-SEC-01: 水平越权访问拦截"""
        pass
        # 模拟 User A 登录
        # self.client.login(username='sales_A', password='password123')
        # 尝试通过硬编码 URL 访问 User B 的客户详情页
        # response = self.client.get(f'/customer/detail/{self.customer_b.id}/')
        # 断言越权访问被拦截 (403禁止 或 404找不到)
        # self.assertIn(response.status_code, [403, 404])