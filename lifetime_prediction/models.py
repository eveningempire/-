"""
瀵垮懡棰勬祴妯″潡鐨勬暟鎹ā鍨?

璇ユā鍧楃敤浜庡瓨鍌ㄥ鍛介娴嬬殑閰嶇疆鍜岀粨鏋滐紝浣嗕笉瀛樺偍棰勬祴妯″瀷鏈韩銆?
棰勬祴妯″瀷灏嗙敱澶栭儴绠楁硶鎻愪緵銆?
"""

from django.db import models
from data_management.models import PHM


class LifetimePredictionConfig(models.Model):
    """瀵垮懡棰勬祴閰嶇疆妯″瀷"""
    
    name = models.CharField(max_length=100, verbose_name="閰嶇疆鍚嶇О")
    description = models.TextField(blank=True, null=True, verbose_name="閰嶇疆鎻忚堪")
    
    # 绐楀彛閰嶇疆
    window_size = models.IntegerField(default=64, verbose_name="绐楀彛澶у皬")
    
    # 閬ユ祴閲忛厤缃?
    required_telemetry = models.JSONField(
        default=list,
        verbose_name="鎵€闇€閬ユ祴閲?,
        help_text="JSON鏍煎紡鐨勯仴娴嬮噺鍚嶇О鍒楄〃"
    )
    
    # 妯″瀷閰嶇疆
    model_path = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name="妯″瀷鏂囦欢璺緞"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="鏄惁鍚敤")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="鍒涘缓鏃堕棿")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="鏇存柊鏃堕棿")
    
    class Meta:
        verbose_name = "瀵垮懡棰勬祴閰嶇疆"
        verbose_name_plural = "瀵垮懡棰勬祴閰嶇疆"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class LifetimePredictionResult(models.Model):
    """瀵垮懡棰勬祴缁撴灉妯″瀷锛堜复鏃跺瓨鍌紝涓嶆寔涔呭寲鍒版暟鎹簱锛?""
    
    # 娉ㄦ剰锛氳繖涓ā鍨嬩富瑕佺敤浜嶢PI鍝嶅簲锛屼笉鍒涘缓鏁版嵁搴撹〃
    class Meta:
        managed = False  # 涓嶅垱寤烘暟鎹簱琛?
    
    # 棰勬祴缁撴灉瀛楁
    cmg_id = models.CharField(max_length=100, verbose_name="PHM ID")
    rul_value = models.FloatField(verbose_name="RUL鍊?)
    confidence = models.FloatField(verbose_name="缃俊搴?, null=True, blank=True)
    prediction_time = models.DateTimeField(verbose_name="棰勬祴鏃堕棿")
    window_data = models.JSONField(verbose_name="绐楀彛鏁版嵁")
    telemetry_used = models.JSONField(verbose_name="浣跨敤鐨勯仴娴嬮噺")
    
    def __str__(self):
        return f"{self.cmg_id} - RUL: {self.rul_value}"

