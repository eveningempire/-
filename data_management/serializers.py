"""
Serializers for the data_management application.

Serializers convert Django model instances to JSON representations and
validate incoming API payloads. They are used by the REST framework views
defined in views.py.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    PHM,
    PHMType,
    Satellite,
    PHMModel,
    ImportSession,
    PHMData,
)


class PHMTypeSerializer(serializers.ModelSerializer):
    """Serializes PHMType instances."""

    class Meta:
        model = PHMType
        fields = ["id", "name", "description"]


class SatelliteSerializer(serializers.ModelSerializer):
    """Serializes Satellite instances."""

    class Meta:
        model = Satellite
        fields = ["id", "name"]


class PHMModelSerializer(serializers.ModelSerializer):
    """Serializes PHMModel instances without enforcing type layer."""

    cmg_type = serializers.PrimaryKeyRelatedField(queryset=PHMType.objects.all(), allow_null=True, required=False)

    class Meta:
        model = PHMModel
        fields = [
            "id",
            "model_name",
            "description",
            "cmg_type",
            "is_active",
            "is_default",
            "is_custom",
            "is_system",
            "is_deprecated",
            "is_hidden",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PHMSerializer(serializers.ModelSerializer):
    """Serializes PHM instances to JSON and vice versa."""

    satellite = serializers.PrimaryKeyRelatedField(queryset=Satellite.objects.all(), allow_null=True, required=False)
    cmg_model = serializers.PrimaryKeyRelatedField(queryset=PHMModel.objects.all(), required=True)
    cmg_model_detail = PHMModelSerializer(source='cmg_model', read_only=True)

    class Meta:
        model = PHM
        fields = ["id", "satellite", "cmg_model", "cmg_model_detail", "cmg_id", "name", "enabled"]


class ImportSessionSerializer(serializers.ModelSerializer):
    """Serializes ImportSession instances."""

    cmg = serializers.PrimaryKeyRelatedField(queryset=PHM.objects.all())

    class Meta:
        model = ImportSession
        fields = [
            "id",
            "cmg",
            "method",
            "timestamp",
            "protocol_description",
            "file",
            "processing_status",
            "total_records",
            "processed_records",
            "failed_records",
            "processing_progress",
            "error_message",
            "detection_summary",
            "started_at",
            "completed_at",
            "max_rows",
            "import_mode",
            "add_milliseconds",
        ]
        read_only_fields = [
            "timestamp",
            "processing_status", 
            "total_records", 
            "processed_records", 
            "failed_records",
            "processing_progress", 
            "error_message", 
            "detection_summary",
            "started_at",
            "completed_at"
        ]


class PHMDataSerializer(serializers.ModelSerializer):
    """Serializes individual PHMData entries."""

    # 鎺ュ彈涓婚敭鍊兼垨瀵硅薄锛岃緭鍑轰负涓婚敭
    cmg = serializers.PrimaryKeyRelatedField(queryset=PHM.objects.all())
    import_session = serializers.PrimaryKeyRelatedField(
        queryset=ImportSession.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = PHMData
        fields = ["id", "cmg", "timestamp", "data", "import_session", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def to_representation(self, instance):
        # 鍏佽缂撳瓨杩斿洖鐨勮交閲忓璞★細鑻?cmg 涓哄瓧绗︿覆/鏁板瓧锛岀洿鎺ユ寜涓婚敭杈撳嚭
        rep = super().to_representation(instance) if hasattr(instance, "_meta") else None
        if rep is None:
            cmg_val = getattr(instance, "cmg", None)
            return {
                "id": getattr(instance, "id", None),
                "cmg": cmg_val if isinstance(cmg_val, (int, str)) else getattr(cmg_val, "id", None),
                "timestamp": getattr(instance, "timestamp", None),
                "data": getattr(instance, "data", None),
                "import_session": getattr(instance, "import_session", None),
                "created_at": getattr(instance, "created_at", None),
                "updated_at": getattr(instance, "updated_at", None),
            }
        return rep

