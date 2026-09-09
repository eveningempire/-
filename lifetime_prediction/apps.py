from django.apps import AppConfig


class LifetimePredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lifetime_prediction'
    verbose_name = '寿命预测'
    
    def ready(self):
        """应用启动时的初始化"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("寿命预测模块已加载")
