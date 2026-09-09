"""
瑙勫垯妫€娴婦jango妯″瀷
瀛樺偍瑙勫垯閰嶇疆銆佹晠闅滃畾涔夊拰妫€娴嬬粨鏋?
"""

from django.db import models
from django.utils import timezone
from data_management.models import PHM, PHMModel, PHMData


class FaultDefinition(models.Model):
    """鏁呴殰瀹氫箟妯″瀷"""
    
    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="fault_definitions",
        help_text="鍏宠仈鐨凜MG妯″瀷"
    )
    fault_name = models.CharField(max_length=128, help_text="鏁呴殰鍚嶇О")
    fault_level = models.IntegerField(default=1, help_text="鏁呴殰绛夌骇(1-5)")
    component = models.CharField(max_length=128, blank=True, help_text="娑夊強閮ㄤ欢")
    description = models.TextField(blank=True, help_text="鏁呴殰鎻忚堪")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "鏁呴殰瀹氫箟"
        verbose_name_plural = "鏁呴殰瀹氫箟"
        unique_together = ['cmg_model', 'fault_name']
    
    def __str__(self):
        return f"{self.cmg_model.model_name} - {self.fault_name}"


class RuleDefinition(models.Model):
    """瑙勫垯瀹氫箟妯″瀷"""
    
    SOURCE_CHOICES = [
        ('expert', '涓撳鎰忚'),
        ('data_driven', '鏁版嵁椹卞姩鎸栨帢'),
    ]
    
    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="rule_definitions",
        help_text="鍏宠仈鐨凜MG妯″瀷"
    )
    fault_definition = models.ForeignKey(
        FaultDefinition,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="鍏宠仈鐨勬晠闅滃畾涔?
    )
    rule_id = models.CharField(max_length=64, help_text="瑙勫垯ID")
    rule_expression = models.TextField(help_text="瑙勫垯琛ㄨ揪寮?)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='expert', help_text="瑙勫垯鏉ユ簮")
    plan_description = models.TextField(blank=True, help_text="棰勬鎻忚堪")
    is_online = models.BooleanField(default=True, help_text="鏄惁鍦ㄧ嚎鍚敤")
    is_new = models.BooleanField(default=True, help_text="鏄惁涓烘柊瑙勫垯")
    is_editable = models.BooleanField(default=True, help_text="鏄惁鍙紪杈?)
    related_parameters = models.JSONField(default=list, help_text="娑夊強鐨勫弬鏁板垪琛?)
    compiled_rule = models.JSONField(null=True, blank=True, help_text="缂栬瘧鍚庣殑瑙勫垯")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "瑙勫垯瀹氫箟"
        verbose_name_plural = "瑙勫垯瀹氫箟"
        unique_together = ['cmg_model', 'rule_id']
    
    def __str__(self):
        return f"{self.cmg_model.model_name} - {self.rule_id}"


class RuleDetectionResult(models.Model):
    """瑙勫垯妫€娴嬬粨鏋滄ā鍨?""
    
    data_point = models.ForeignKey(
        PHMData,
        on_delete=models.CASCADE,
        related_name="rule_results",
        help_text="鍏宠仈鐨勬暟鎹偣"
    )
    rule_definition = models.ForeignKey(
        RuleDefinition,
        on_delete=models.CASCADE,
        related_name="detection_results",
        help_text="瑙﹀彂鐨勮鍒?
    )
    fault_definition = models.ForeignKey(
        FaultDefinition,
        on_delete=models.CASCADE,
        related_name="detection_results",
        help_text="妫€娴嬪埌鐨勬晠闅?
    )
    is_triggered = models.BooleanField(help_text="瑙勫垯鏄惁琚Е鍙?)
    confidence_score = models.FloatField(help_text="缃俊搴﹀垎鏁?)
    detection_details = models.JSONField(
        default=dict,
        help_text="妫€娴嬭缁嗕俊鎭?
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "瑙勫垯妫€娴嬬粨鏋?
        verbose_name_plural = "瑙勫垯妫€娴嬬粨鏋?
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_triggered']),
            models.Index(fields=['data_point', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.data_point.timestamp} - {self.fault_definition.fault_name} ({'瑙﹀彂' if self.is_triggered else '鏈Е鍙?})"


class ComponentDefinition(models.Model):
    """缁勪欢瀹氫箟妯″瀷"""
    
    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="component_definitions",
        help_text="鍏宠仈鐨凜MG妯″瀷"
    )
    component_name = models.CharField(max_length=128, help_text="缁勪欢鍚嶇О")
    description = models.TextField(blank=True, help_text="缁勪欢鎻忚堪")
    parameters = models.JSONField(default=list, help_text="鍏宠仈鐨勫弬鏁板垪琛?)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "缁勪欢瀹氫箟"
        verbose_name_plural = "缁勪欢瀹氫箟"
        unique_together = ['cmg_model', 'component_name']
    
    def __str__(self):
        return f"{self.cmg_model.model_name} - {self.component_name}"

