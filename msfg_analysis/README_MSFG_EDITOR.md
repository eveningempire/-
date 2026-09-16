"""
澶氫俊鍙锋祦鍥?MSFG)鍒嗘瀽Django妯″瀷
瀛樺偍MSFG鍥剧粨鏋勩€佸垎鏋愮粨鏋?
"""

from django.db import models
from django.utils import timezone
from data_management.models import PHM, PHMModel, PHMData


class MSFGDefinition(models.Model):
    """澶氫俊鍙锋祦鍥惧畾涔夋ā鍨?""
    
    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="msfg_definitions",
        help_text="关联的CMG模型"
    )
    name = models.CharField(max_length=128, help_text="MSFG鍚嶇О")
    description = models.TextField(blank=True, help_text="MSFG鎻忚堪")
    raw_graph_data = models.JSONField(help_text="鍘熷鍥炬暟鎹?)
    processed_graph_data = models.JSONField(help_text="澶勭悊鍚庣殑鍥炬暟鎹?)
    detection_matrix = models.JSONField(null=True, blank=True, help_text="妫€娴嬬煩闃?)
    test_names = models.JSONField(default=list, help_text="娴嬭瘯鐐瑰悕绉板垪琛?)
    fault_names = models.JSONField(default=list, help_text="鏁呴殰鍚嶇О鍒楄〃")
    component_names = models.JSONField(default=list, help_text="组件名称列表")
    is_active = models.BooleanField(default=True, help_text="鏄惁婵€娲?)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "澶氫俊鍙锋祦鍥惧畾涔?
        verbose_name_plural = "澶氫俊鍙锋祦鍥惧畾涔?
        unique_together = ['cmg_model', 'name']
    
    def __str__(self):
        return f"{self.cmg_model.model_name} - {self.name}"


class MSFGNode(models.Model):
    """MSFG鑺傜偣妯″瀷"""
    
    NODE_TYPES = [
        ('test', '娴嬭瘯鐐?),
        ('fault', '鏁呴殰鐐?),
        ('system', '绯荤粺鑺傜偣'),
        ('component', '缁勪欢鑺傜偣'),
    ]
    
    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="nodes",
        help_text="关联的MSFG定义"
    )
    node_id = models.CharField(max_length=64, help_text="鑺傜偣ID")
    node_type = models.CharField(max_length=20, choices=NODE_TYPES, help_text="鑺傜偣绫诲瀷")
    name = models.CharField(max_length=128, help_text="鑺傜偣鍚嶇О")
    position_x = models.FloatField(default=0, help_text="X鍧愭爣")
    position_y = models.FloatField(default=0, help_text="Y鍧愭爣")
    properties = models.JSONField(default=dict, help_text="鑺傜偣灞炴€?)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "MSFG鑺傜偣"
        verbose_name_plural = "MSFG鑺傜偣"
        unique_together = ['msfg_definition', 'node_id']
    
    def __str__(self):
        return f"{self.msfg_definition.name} - {self.name} ({self.node_type})"


class MSFGEdge(models.Model):
    """MSFG杈规ā鍨?""
    
    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="edges",
        help_text="关联的MSFG定义"
    )
    edge_id = models.CharField(max_length=64, help_text="杈笽D")
    source_node = models.ForeignKey(
        MSFGNode,
        on_delete=models.CASCADE,
        related_name="outgoing_edges",
        help_text="婧愯妭鐐?
    )
    target_node = models.ForeignKey(
        MSFGNode,
        on_delete=models.CASCADE,
        related_name="incoming_edges",
        help_text="鐩爣鑺傜偣"
    )
    edge_type = models.CharField(max_length=64, blank=True, help_text="杈圭被鍨?)
    properties = models.JSONField(default=dict, help_text="杈瑰睘鎬?)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "MSFG杈?
        verbose_name_plural = "MSFG杈?
        unique_together = ['msfg_definition', 'edge_id']
    
    def __str__(self):
        return f"{self.msfg_definition.name} - {self.source_node.name} -> {self.target_node.name}"


class MSFGAnalysisResult(models.Model):
    """MSFG分析结果模型"""
    
    data_point = models.ForeignKey(
        PHMData,
        on_delete=models.CASCADE,
        related_name="msfg_results",
        help_text="关联的数据点"
    )
    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="analysis_results",
        help_text="浣跨敤鐨凪SFG瀹氫箟"
    )
    test_results = models.JSONField(default=dict, help_text="娴嬭瘯鐐圭粨鏋?)
    fault_results = models.JSONField(default=dict, help_text="鏁呴殰鐐圭粨鏋?)
    system_results = models.JSONField(default=dict, help_text="系统分析结果")
    component_results = models.JSONField(default=dict, help_text="部件级别分析结果")
    overall_health_score = models.FloatField(default=1.0, help_text="总体健康分数")
    detected_faults = models.JSONField(default=list, help_text="妫€娴嬪埌鐨勬晠闅滃垪琛?)
    critical_components = models.JSONField(default=list, help_text="关键异常部件列表")
    analysis_details = models.JSONField(
        default=dict,
        help_text="分析详细信息"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "MSFG分析结果"
        verbose_name_plural = "MSFG分析结果"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.data_point.timestamp} - 健康分数: {self.overall_health_score:.3f}"


class TestPointRuleMapping(models.Model):
    """瑙勫垯ID -> 娴嬭瘯鐐瑰悕绉?鐨勬槧灏勶紝鐢ㄤ簬灏嗚鍒欑粨鏋滆浆鎹负MSFG娴嬭瘯鐐瑰垎鏁般€?

    浠?PHMModel 涓轰綔鐢ㄥ煙锛氬悓涓€妯″瀷涓嬶紝瑙勫垯瀹氫箟鍒版祴璇曠偣鐨勬槧灏勫敮涓€銆?
    """

    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="msfg_testpoint_mappings",
        help_text="关联的CMG模型"
    )
    rule_definition = models.ForeignKey(
        'rule_detection.RuleDefinition',
        on_delete=models.CASCADE,
        related_name="msfg_testpoint_mappings",
        help_text="鍏宠仈鐨勮鍒欏畾涔?
    )
    test_name = models.CharField(max_length=128, help_text="娴嬭瘯鐐瑰悕绉?)
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛堝彲閫夛級")
    is_active = models.BooleanField(default=True, help_text="鏄惁鍚敤")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "瑙勫垯-娴嬭瘯鐐规槧灏?
        verbose_name_plural = "瑙勫垯-娴嬭瘯鐐规槧灏?
        unique_together = ["cmg_model", "rule_definition"]

    def __str__(self):
        return f"{self.cmg_model.model_name} - {self.rule_definition.rule_id} -> {self.test_name}"


class TestPointRule(models.Model):
    """鐙珛浜庤鍒欐娴嬫ā鍧楃殑"娴嬬偣瑙勫垯"瀹氫箟銆?

    缁戝畾鍒扮壒瀹氱殑MSFG瀹氫箟锛屾瘡鏉¤鍒欑洿鎺ョ粦瀹氬埌涓€涓祴璇曠偣鍚嶇О(test_name)锛?
    骞舵彁渚涘彲鎵ц鐨?rule_expression锛堝崟鐐硅〃杈惧紡锛夈€?
    """

    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="testpoint_rules",
        help_text="关联的MSFG定义",
        null=True,
        blank=True
    )
    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="msfg_testpoint_rules",
        help_text="关联的CMG模型"
    )
    test_name = models.CharField(max_length=128, help_text="娴嬭瘯鐐瑰悕绉?)
    rule_id = models.CharField(max_length=64, help_text="瑙勫垯ID")
    rule_expression = models.TextField(help_text="规则表达式（单点表达式）")
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛?..10锛?)
    is_online = models.BooleanField(default=True, help_text="鏄惁鍚敤")
    description = models.TextField(blank=True, help_text="瑙勫垯鎻忚堪")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MSFG娴嬬偣瑙勫垯"
        verbose_name_plural = "MSFG娴嬬偣瑙勫垯"
        # 鏇存敼鍞竴绾︽潫锛屽湪鍚屼竴PHM妯″瀷涓嬶紝test_name+rule_id鍞竴
        unique_together = ["cmg_model", "test_name", "rule_id"]

    def __str__(self):
        msfg_name = self.msfg_definition.name if self.msfg_definition else "鏈寚瀹歁SFG"
        return f"{msfg_name} - {self.test_name} ({self.rule_id})"


class TestPointComponentMapping(models.Model):
    """测试点到部件的映射表
    
    用于将MSFG中的测试点映射到具体的物理部件，
    浠ヤ究杩涜鍑嗙‘鐨勯儴浠剁骇鍒晠闅滃畾浣嶃€?
    """
    
    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="testpoint_component_mappings",
        help_text="关联的MSFG定义"
    )
    test_point_name = models.CharField(max_length=128, help_text="娴嬭瘯鐐瑰悕绉?)
    component_name = models.CharField(max_length=128, help_text="閮ㄤ欢鍚嶇О")
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('one_to_one', '涓€瀵逛竴'),
            ('one_to_many', '涓€瀵瑰'),
            ('many_to_one', '澶氬涓€')
        ],
        default='one_to_one',
        help_text="鏄犲皠绫诲瀷"
    )
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛?.1-10锛?)
    component_type = models.CharField(
        max_length=64, 
        choices=[
            ('motor', '鐢垫満绯荤粺'),
            ('bearing', '杞存壙绯荤粺'),
            ('gear', '浼犲姩绯荤粺'),
            ('sensor', '浼犳劅鍣ㄧ郴缁?),
            ('control', '鎺у埗绯荤粺'),
            ('power', '鐢垫簮绯荤粺'),
            ('structural', '结构系统'),
            ('thermal', '鐑鐞嗙郴缁?),
            ('other', '鍏朵粬閮ㄤ欢')
        ],
        default='other',
        help_text="閮ㄤ欢绫诲瀷"
    )
    importance_weight = models.FloatField(default=1.0, help_text="閲嶈搴︽潈閲嶏紙0.1-10锛?)
    is_critical = models.BooleanField(default=False, help_text="鏄惁涓哄叧閿儴浠?)
    description = models.TextField(blank=True, help_text="鏄犲皠鎻忚堪")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "娴嬭瘯鐐?閮ㄤ欢鏄犲皠"
        verbose_name_plural = "娴嬭瘯鐐?閮ㄤ欢鏄犲皠"
        unique_together = ["msfg_definition", "test_point_name", "component_name"]
    
    def __str__(self):
        return f"{self.msfg_definition.name} - {self.test_point_name} -> {self.component_name}"


class FaultComponentMapping(models.Model):
    """
    鐢辩敤鎴锋槑纭厤缃紝鐢ㄤ簬灏嗘晠闅滄鐜囧綊闆嗗埌閮ㄤ欢銆?
    """

    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="fault_component_mappings",
        help_text="关联的MSFG定义"
    )
    fault_name = models.CharField(max_length=128, help_text="鏁呴殰鍚嶇О")
    component_name = models.CharField(max_length=128, help_text="閮ㄤ欢鍚嶇О")
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('one_to_one', '涓€瀵逛竴'),
            ('one_to_many', '涓€瀵瑰'),
            ('many_to_one', '澶氬涓€')
        ],
        default='one_to_one',
        help_text="鏄犲皠绫诲瀷"
    )
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛?.1-10锛?)
    is_critical = models.BooleanField(default=False, help_text="鏄惁涓哄叧閿槧灏?)
    description = models.TextField(blank=True, help_text="鏄犲皠鎻忚堪")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "鏁呴殰-閮ㄤ欢鏄犲皠"
        verbose_name_plural = "鏁呴殰-閮ㄤ欢鏄犲皠"
        unique_together = ["msfg_definition", "fault_name", "component_name"]

    def __str__(self):
        return f"{self.msfg_definition.name} - {self.fault_name} -> {self.component_name}"


class TestPointFaultMapping(models.Model):
    """
    鐢辩敤鎴锋槑纭厤缃紝鐢ㄤ簬灏嗘祴璇曠偣鐩存帴鏄犲皠鍒版晠闅溿€?
    杩欐牱鍙互寤虹珛娴嬭瘯鐐?鏁呴殰鐨勭洿鎺ユ帹鐞嗗叧绯伙紝鎻愰珮鎺ㄧ悊绮惧害銆?
    """

    msfg_definition = models.ForeignKey(
        MSFGDefinition,
        on_delete=models.CASCADE,
        related_name="testpoint_fault_mappings",
        help_text="关联的MSFG定义"
    )
    test_point_name = models.CharField(max_length=128, help_text="娴嬭瘯鐐瑰悕绉?)
    fault_name = models.CharField(max_length=128, help_text="鏁呴殰鍚嶇О")
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('one_to_one', '涓€瀵逛竴'),
            ('one_to_many', '涓€瀵瑰'),
            ('many_to_one', '澶氬涓€')
        ],
        default='one_to_one',
        help_text="鏄犲皠绫诲瀷"
    )
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛?.1-10锛?)
    confidence = models.FloatField(default=0.8, help_text="缃俊搴︼紙0.1-1.0锛?)
    is_critical = models.BooleanField(default=False, help_text="鏄惁涓哄叧閿槧灏?)
    description = models.TextField(blank=True, help_text="鏄犲皠鎻忚堪")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "娴嬭瘯鐐?鏁呴殰鏄犲皠"
        verbose_name_plural = "娴嬭瘯鐐?鏁呴殰鏄犲皠"
        unique_together = ["msfg_definition", "test_point_name", "fault_name"]

    def __str__(self):
        return f"{self.msfg_definition.name} - {self.test_point_name} -> {self.fault_name}"
