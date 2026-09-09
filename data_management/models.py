"""
Models related to data ingestion and storage.

These models provide a thin abstraction over the PHM data stored in the
underlying MySQL database. While the actual telemetry tables are managed by
another team, these models capture high-level metadata such as PHM
identifiers, import sessions and pointers to the raw measurements.
"""

from __future__ import annotations

from django.db import models


class PHMType(models.Model):
    """Types of PHM, e.g. SPIN, MAG etc."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Satellite(models.Model):
    """Represents a satellite or star that hosts PHMs."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class PHMModel(models.Model):
    """Defines a PHM model.

    Includes a set of flags describing whether the model is active, default,
    custom, system provided, deprecated, hidden or public. These flags can
    be used by the front end to filter models.
    """

    model_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # Type layer removed from business logic; keep optional FK for backward compatibility
    cmg_type = models.ForeignKey(PHMType, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Flags describing the nature of this model
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_custom = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    is_deprecated = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.model_name


class PHM(models.Model):
    """Represents a control moment gyroscope (PHM) individual of a model."""

    # Satellite concept removed from business logic; keep optional for legacy data
    satellite = models.ForeignKey(Satellite, on_delete=models.SET_NULL, null=True, blank=True, related_name="cmgs")
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.PROTECT, related_name="cmgs")
    cmg_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True, help_text="Whether this PHM is currently enabled for monitoring")

    class Meta:
        verbose_name = "PHM"
        verbose_name_plural = "PHMs"

    def __str__(self) -> str:
        return f"{self.name} ({self.cmg_id})"


class ImportSession(models.Model):
    """Tracks a single data import event.

    Data can arrive either via a network (TCP) stream or via a file upload.
    This model stores metadata about each import, such as the import method,
    timestamp and protocol description. When using file import, an optional
    ``file`` field can store the uploaded file for later processing.
    """

    class Method(models.TextChoices):
        TCP = "TCP", "TCP缃戠粶瀵煎叆"
        FILE = "FILE", "鏈湴鏂囦欢瀵煎叆"

    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "寰呭鐞?
        PARSING = "PARSING", "瑙ｆ瀽涓?
        STORING = "STORING", "瀛樺偍涓?
        DETECTING = "DETECTING", "妫€娴嬩腑"
        COMPLETED = "COMPLETED", "宸插畬鎴?
        FAILED = "FAILED", "澶辫触"

    class ImportMode(models.TextChoices):
        IMPORT_AND_DETECT = "IMPORT_AND_DETECT", "瀵煎叆骞舵娴?
        IMPORT_ONLY = "IMPORT_ONLY", "浠呭鍏?

    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, related_name="import_sessions")
    method = models.CharField(max_length=10, choices=Method.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    protocol_description = models.TextField(blank=True, null=True, help_text="Network protocol description (editable)")
    file = models.FileField(
        upload_to="imports/%Y/%m/%d",
        blank=True,
        null=True,
        help_text="Uploaded data file when the method is FILE",
    )
    
    # 鏂板瀛楁鐢ㄤ簬璺熻釜澶勭悊鐘舵€佸拰杩涘害
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        help_text="鏂囦欢澶勭悊鐘舵€?
    )
    total_records = models.IntegerField(default=0, help_text="鎬昏褰曟暟")
    processed_records = models.IntegerField(default=0, help_text="宸插鐞嗚褰曟暟")
    failed_records = models.IntegerField(default=0, help_text="澶辫触璁板綍鏁?)
    processing_progress = models.FloatField(default=0.0, help_text="澶勭悊杩涘害鐧惧垎姣?)
    error_message = models.TextField(blank=True, null=True, help_text="閿欒淇℃伅")
    detection_summary = models.JSONField(default=dict, blank=True, help_text="妫€娴嬬粨鏋滄憳瑕?)
    started_at = models.DateTimeField(null=True, blank=True, help_text="寮€濮嬪鐞嗘椂闂?)
    completed_at = models.DateTimeField(null=True, blank=True, help_text="瀹屾垚鏃堕棿")
    max_rows = models.IntegerField(null=True, blank=True, help_text="鏈€澶у鐞嗚鏁帮紝null琛ㄧず澶勭悊鏁翠釜鏂囦欢")
    import_mode = models.CharField(
        max_length=20,
        choices=ImportMode.choices,
        default=ImportMode.IMPORT_AND_DETECT,
        help_text="瀵煎叆妯″紡锛氫粎瀵煎叆鎴栧鍏ュ苟妫€娴?
    )
    add_milliseconds = models.BooleanField(
        default=True,
        help_text="鏄惁鑷姩涓洪噸澶嶆椂闂存埑娣诲姞姣"
    )

    class Meta:
        verbose_name = "Import session"
        verbose_name_plural = "Import sessions"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.get_method_display()} - {self.cmg.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class PHMData(models.Model):
    """Represents an individual data point collected from a PHM.

    This model stores the timestamped telemetry values for a given PHM.
    The ``data`` field holds a JSON blob keyed by parameter name. A
    reference to the import session is optional but recommended to trace
    the origin of the data.
    """

    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, related_name="data")
    import_session = models.ForeignKey(
        ImportSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="data",
    )
    timestamp = models.DateTimeField(help_text="Data timestamp")
    data = models.JSONField(help_text="Raw or parsed telemetry content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cmg", "timestamp")
        indexes = [
            models.Index(fields=["cmg", "timestamp"]),
        ]
        ordering = ["timestamp"]
        verbose_name = "PHM data"
        verbose_name_plural = "PHM data"

    def __str__(self) -> str:
        return f"{self.cmg.name} - {self.timestamp}"

    results = models.JSONField(default=dict, blank=True, help_text="Detection results and metrics")


class DatabaseStatistics(models.Model):
    """鏁版嵁搴撶粺璁′俊鎭〃 - 缁存姢鍚勭鏁版嵁鐨勬€绘暟"""
    
    class Meta:
        verbose_name = "鏁版嵁搴撶粺璁?
        verbose_name_plural = "鏁版嵁搴撶粺璁?
    
    # 缁熻绫诲瀷
    STAT_TYPE_CHOICES = [
        ('cmg_data', 'PHM閬ユ祴鏁版嵁'),
        ('ims_results', 'IMS妫€娴嬬粨鏋?),
        ('rule_results', '瑙勫垯妫€娴嬬粨鏋?),
        ('msfg_results', 'MSFG妫€娴嬬粨鏋?),
        ('anomaly_frames', '寮傚父甯?),
        ('total_frames', '鎬诲抚鏁?),
    ]
    
    stat_type = models.CharField(max_length=20, choices=STAT_TYPE_CHOICES, verbose_name="缁熻绫诲瀷")
    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, null=True, blank=True, verbose_name="PHM")
    count = models.BigIntegerField(default=0, verbose_name="鏁伴噺")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="鏈€鍚庢洿鏂版椂闂?)
    
    class Meta:
        unique_together = ['stat_type', 'cmg']
        verbose_name = "鏁版嵁搴撶粺璁?
        verbose_name_plural = "鏁版嵁搴撶粺璁?
    
    def __str__(self):
        cmg_name = self.cmg.name if self.cmg else "鍏ㄥ眬"
        return f"{self.get_stat_type_display()} - {cmg_name}: {self.count}"
    
    @classmethod
    def update_statistics(cls, stat_type: str, cmg=None, count: int = None):
        """鏇存柊缁熻淇℃伅"""
        if count is None:
            # 鑷姩璁＄畻鏁伴噺
            if stat_type == 'cmg_data':
                count = PHMData.objects.filter(cmg=cmg).count() if cmg else PHMData.objects.count()
            elif stat_type == 'ims_results':
                try:
                    from health_management.models import IMSDetectionResult
                    count = IMSDetectionResult.objects.filter(data_point__cmg=cmg).count() if cmg else IMSDetectionResult.objects.count()
                except ImportError:
                    count = 0
            elif stat_type == 'rule_results':
                try:
                    from rule_detection.models import RuleDetectionResult
                    count = RuleDetectionResult.objects.filter(data_point__cmg=cmg).count() if cmg else RuleDetectionResult.objects.count()
                except ImportError:
                    count = 0
            elif stat_type == 'msfg_results':
                try:
                    from msfg_analysis.models import MSFGAnalysisResult
                    count = MSFGAnalysisResult.objects.filter(data_point__cmg=cmg).count() if cmg else MSFGAnalysisResult.objects.count()
                except ImportError:
                    count = 0
            elif stat_type == 'anomaly_frames':
                try:
                    from health_management.models import IMSDetectionResult
                    count = IMSDetectionResult.objects.filter(data_point__cmg=cmg, is_anomaly=True).count() if cmg else IMSDetectionResult.objects.filter(is_anomaly=True).count()
                except ImportError:
                    count = 0
            elif stat_type == 'total_frames':
                count = PHMData.objects.filter(cmg=cmg).count() if cmg else PHMData.objects.count()
        
        # 鏇存柊鎴栧垱寤虹粺璁¤褰?        stat, created = cls.objects.get_or_create(
            stat_type=stat_type,
            cmg=cmg,
            defaults={'count': count}
        )
        if not created:
            stat.count = count
            stat.save(update_fields=['count', 'last_updated'])
        
        return stat
    
    @classmethod
    def get_statistics(cls, cmg=None):
        """鑾峰彇缁熻淇℃伅"""
        queryset = cls.objects.filter(cmg=cmg) if cmg else cls.objects.filter(cmg__isnull=True)
        stats = {}
        for stat in queryset:
            stats[stat.stat_type] = {
                'count': stat.count,
                'last_updated': stat.last_updated,
                'display_name': stat.get_stat_type_display()
            }
        return stats
    
    @classmethod
    def refresh_all_statistics(cls):
        """鍒锋柊鎵€鏈夌粺璁′俊鎭?""
        try:
            from health_management.models import IMSDetectionResult
            from rule_detection.models import RuleDetectionResult
            from msfg_analysis.models import MSFGAnalysisResult
            
            # 鏇存柊鍏ㄥ眬缁熻
            cls.update_statistics('cmg_data')
            cls.update_statistics('ims_results')
            cls.update_statistics('rule_results')
            cls.update_statistics('msfg_results')
            cls.update_statistics('anomaly_frames')
            cls.update_statistics('total_frames')
            
            # 鏇存柊姣忎釜PHM鐨勭粺璁?            for cmg in PHM.objects.all():
                cls.update_statistics('cmg_data', cmg)
                cls.update_statistics('ims_results', cmg)
                cls.update_statistics('rule_results', cmg)
                cls.update_statistics('msfg_results', cmg)
                cls.update_statistics('anomaly_frames', cmg)
                cls.update_statistics('total_frames', cmg)
        except ImportError as e:
            print(f"瀵煎叆妯″瀷澶辫触: {e}")
        except Exception as e:
            print(f"鍒锋柊缁熻淇℃伅澶辫触: {e}")

