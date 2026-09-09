"""
View definitions for the health_management application.

These viewsets expose CRUD operations for rules, diagnosis graphs and
read-only access to algorithm results (anomalies, rule results,
diagnoses, health evaluations and life predictions). They rely on the
Django REST framework and simple permission classes. Business logic
resides in services.py.
"""

from __future__ import annotations

import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from data_management.models import PHM, PHMData
from .models import (
    AnomalyResult,
    Rule,
    RuleResult,
    DiagnosisGraph,
    DiagnosisResult,
    HealthEvaluation,
    LifePrediction,
    IMSModel,
    IMSDetectionResult,
)
from .serializers import (
    AnomalyResultSerializer,
    RuleSerializer,
    RuleResultSerializer,
    DiagnosisGraphSerializer,
    DiagnosisResultSerializer,
    HealthEvaluationSerializer,
    LifePredictionSerializer,
    IMSModelSerializer,
    IMSDetectionResultSerializer,
)
from .ims_service import ims_service, get_anomaly_data_with_ims
from .services import compute_health_evaluation, update_life_prediction


class RuleViewSet(viewsets.ModelViewSet):
    """Allows creation, listing, updating and deletion of rules."""

    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [AllowAny]


class DiagnosisGraphViewSet(viewsets.ModelViewSet):
    """Allows management of diagnosis graphs."""

    queryset = DiagnosisGraph.objects.all()
    serializer_class = DiagnosisGraphSerializer
    permission_classes = [AllowAny]


class AnomalyResultViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only access to anomaly results."""

    queryset = AnomalyResult.objects.select_related("data_point", "data_point__cmg").all()
    serializer_class = AnomalyResultSerializer
    permission_classes = [AllowAny]


class RuleResultViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only access to rule evaluation results."""

    queryset = RuleResult.objects.select_related("anomaly", "rule").all()
    serializer_class = RuleResultSerializer
    permission_classes = [AllowAny]


class DiagnosisResultViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only access to diagnosis results."""

    queryset = DiagnosisResult.objects.select_related("anomaly", "graph").all()
    serializer_class = DiagnosisResultSerializer
    permission_classes = [AllowAny]


class HealthEvaluationViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only access to health evaluations."""

    queryset = HealthEvaluation.objects.select_related("cmg").all()
    serializer_class = HealthEvaluationSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], url_path="recompute")
    def recompute(self, request):
        """Endpoint to trigger recomputation of health for a given PHM."""
        cmg_id = request.data.get("cmg_id")
        if not cmg_id:
            return Response({"detail": "cmg_id is required"}, status=400)
        try:
            cmg = PHM.objects.get(pk=cmg_id)
        except PHM.DoesNotExist:
            return Response({"detail": "PHM not found"}, status=404)
        compute_health_evaluation(cmg)
        return Response({"detail": "Health evaluation recomputed"})


class LifePredictionViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only access to life predictions."""

    queryset = LifePrediction.objects.select_related("cmg").all()
    serializer_class = LifePredictionSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], url_path="update")
    def update_prediction(self, request):
        """Endpoint to force an update of life prediction for a PHM."""
        cmg_id = request.data.get("cmg_id")
        if not cmg_id:
            return Response({"detail": "cmg_id is required"}, status=400)
        try:
            cmg = PHM.objects.get(pk=cmg_id)
        except PHM.DoesNotExist:
            return Response({"detail": "PHM not found"}, status=404)
        update_life_prediction(cmg)
        return Response({"detail": "Life prediction updated"})


class IMSModelViewSet(viewsets.ModelViewSet):
    """IMS妯″瀷绠＄悊瑙嗗浘闆?""
    
    queryset = IMSModel.objects.all()
    serializer_class = IMSModelSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=["post"], url_path="upload", parser_classes=[MultiPartParser, FileUploadParser])
    def upload_model(self, request):
        """涓婁紶璁粌濂界殑IMS妯″瀷鏂囦欢"""
        cmg_model_id = request.data.get("cmg_model_id")
        model_name = request.data.get("name")
        model_file = request.FILES.get("model_file")
        
        if not cmg_model_id or not model_file:
            return Response(
                {"error": "cmg_model_id and model_file are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 淇濆瓨涓婁紶鐨勬枃浠?            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                for chunk in model_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # 鍒涘缓妯″瀷璁板綍
            ims_model = ims_service.create_model_from_file(
                tmp_file_path, 
                int(cmg_model_id), 
                model_name
            )
            
            # 娓呯悊涓存椂鏂囦欢
            os.unlink(tmp_file_path)
            
            if ims_model:
                serializer = self.get_serializer(ims_model)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"error": "Failed to create IMS model"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Upload failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=["post"], url_path="train")
    def train_model(self, request):
        """璁粌鏂扮殑IMS妯″瀷"""

        try:
            cmg_model_id = request.data.get("cmg_model_id")
            model_name = request.data.get("name", "IMS_Auto")
            selected_params = request.data.get("parameters", [])
            contamination = float(request.data.get("contamination", 0.05))
            n_estimators = int(request.data.get("n_estimators", 150))
            
            if not cmg_model_id:
                return Response(
                    {"error": "cmg_model_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from data_management.models import PHMModel
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
            
            # 鑾峰彇璁粌鏁版嵁 - 浼樺厛浣跨敤CSV鏂囦欢
            training_data_path = request.data.get("training_data_path", "")
            use_csv_data = request.data.get("use_csv_data", True)
            
            if use_csv_data:
                # 浣跨敤CSV鏂囦欢涓殑璁粌鏁版嵁
                try:
                    training_data_matrix, available_params = self._load_csv_training_data(training_data_path)
                    if len(training_data_matrix) < 100:
                        return Response(
                            {"error": f"CSV璁粌鏁版嵁涓嶈冻锛岄渶瑕佽嚦灏?00鏉¤褰曪紝褰撳墠浠呮湁{len(training_data_matrix)}鏉?}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    return Response(
                        {"error": f"鍔犺浇CSV璁粌鏁版嵁澶辫触: {str(e)}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # 浣跨敤鏁版嵁搴撲腑鐨勬暟鎹?                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)  # 鏈€杩?0澶?                
                training_data = PHMData.objects.filter(
                    cmg__cmg_model=cmg_model,
                    timestamp__gte=start_time,
                    timestamp__lte=end_time
                ).order_by('timestamp')
                
                if training_data.count() < 100:
                    return Response(
                        {"error": f"璁粌鏁版嵁涓嶈冻锛岄渶瑕佽嚦灏?00鏉¤褰曪紝褰撳墠浠呮湁{training_data.count()}鏉?}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 澶勭悊鍙傛暟閫夋嫨鍜屾暟鎹煩闃靛噯澶?            if use_csv_data:
                # CSV鏁版嵁宸茬粡鏄煩闃靛舰寮?                if selected_params:
                    valid_params = [p for p in selected_params if p in available_params]
                    if not valid_params:
                        return Response(
                            {"error": f"鎸囧畾鐨勫弬鏁颁笉瀛樺湪銆傚彲鐢ㄥ弬鏁? {available_params}"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # 閲嶆柊鎺掑垪鏁版嵁鐭╅樀浠ュ尮閰嶉€夊畾鍙傛暟
                    param_indices = [available_params.index(p) for p in valid_params]
                    data_matrix = training_data_matrix[:, param_indices]
                else:
                    # 鑷姩閫夋嫨鏁板€煎瀷鍙傛暟锛圕SV鏁版嵁榛樿宸茶繃婊わ級
                    valid_params = available_params[:10]  # 鏈€澶氶€夋嫨10涓弬鏁?                    data_matrix = training_data_matrix[:, :len(valid_params)]
            else:
                # 鍒嗘瀽鏁版嵁搴撲腑鐨勫彲鐢ㄥ弬鏁?                all_params = set()
                for data in training_data[:1000]:  # 鍙栨牱鍒嗘瀽鍙傛暟
                    if isinstance(data.data, dict):
                        all_params.update(data.data.keys())
                
                available_params = list(all_params)
                
                # 杩囨护閫夋嫨鐨勫弬鏁?                if selected_params:
                    valid_params = [p for p in selected_params if p in available_params]
                    if not valid_params:
                        return Response(
                            {"error": f"鎸囧畾鐨勫弬鏁颁笉瀛樺湪銆傚彲鐢ㄥ弬鏁? {available_params}"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    # 鑷姩閫夋嫨鏁板€煎瀷鍙傛暟
                    valid_params = self._filter_numeric_params(training_data, available_params)
                
                if len(valid_params) < 2:
                    return Response(
                        {"error": f"鏈夋晥鍙傛暟涓嶈冻锛岄渶瑕佽嚦灏?涓弬鏁般€傚彲鐢ㄥ弬鏁? {available_params}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 鍑嗗璁粌鏁版嵁鐭╅樀
                data_matrix = []
                for data in training_data:
                    row = [data.data.get(param, float('nan')) for param in valid_params]
                    data_matrix.append(row)
                
                import numpy as np
                data_matrix = np.array(data_matrix, dtype=np.float32)
            
            # 绉婚櫎鍖呭惈杩囧NaN鐨勮
            valid_threshold = len(valid_params) * 0.7
            import numpy as np
            valid_mask = np.sum(~np.isnan(data_matrix), axis=1) >= valid_threshold
            clean_data = data_matrix[valid_mask]
            
            if len(clean_data) < 100:
                return Response(
                    {"error": f"娓呯悊鍚庤缁冩暟鎹笉瓒筹紝浠呮湁{len(clean_data)}鏉℃湁鏁堣褰?}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 鍒涘缓鍜岃缁冩ā鍨?            from .algorithms.IMS.ims_algorithm import create_ims_model
            
            model_config = {
                "contamination": contamination,
                "n_estimators": n_estimators,
                "max_samples": "auto",
                "max_features": 0.8,
                "bootstrap": False,
                "random_state": 42,
                "scaler_type": "standard"
            }
            
            model = create_ims_model(valid_params, model_config)
            model.fit(clean_data, save=False)
            
            # 鍒涘缓鏁版嵁搴撹褰?            ims_model = IMSModel.objects.create(
                cmg_model=cmg_model,
                name=model_name,
                parameters=valid_params,
                model_config=model_config,
                model_data=model.to_json(),
                threshold=float(model.threshold_value) if model.threshold_value else 0.5,
                is_active=True
            )
            
            # 娓呯┖妯″瀷缂撳瓨锛岀‘淇濇柊妯″瀷琚姞杞?            ims_service.clear_cache()
            
            serializer = self.get_serializer(ims_model)
            return Response({
                **serializer.data,
                "training_summary": {
                    "training_samples": len(clean_data),
                    "parameters": valid_params,
                    "threshold": float(model.threshold_value) if model.threshold_value else 0.5,
                    "contamination": contamination,
                    "n_estimators": n_estimators
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Training failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="train-legacy")
    def train_model_legacy(self, request):
        """浠嶤SV璁粌鑰両MS(KMeans)妯″瀷骞舵敞鍐岋紝鏀寔婵€娲汇€?""
        try:
            cmg_model_id = int(request.data.get("cmg_model_id"))
            model_name = request.data.get("name") or "LegacyIMS_Auto"
            data_dir = request.data.get("data_dir") or os.path.join("delete", "IMS", "Health")
            columns = request.data.get("columns") or []
            if isinstance(columns, str):
                columns = [c.strip() for c in columns.split(",") if c.strip()]
            n_clusters = request.data.get("n_clusters")
            n_clusters = int(n_clusters) if n_clusters not in (None, "",) else None
            shrink_ratio = float(request.data.get("shrink_ratio", 0.20))      # 浼樺寲锛氶粯璁?.20
            calib_percentile = float(request.data.get("calib_percentile", 99.0))  # 浼樺寲锛氶粯璁?9.0
            threshold = float(request.data.get("threshold", 0.65))            # 浼樺寲锛氶粯璁?.65
            deactivate_others = bool(request.data.get("deactivate_others", False))

            from data_management.models import PHMModel
            try:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            except PHMModel.DoesNotExist:
                return Response({"error": "PHMModel not found"}, status=404)

            from .algorithms.IMS.legacy_trainer import train_legacy_ims_from_csv
            model_bytes, final_cols = train_legacy_ims_from_csv(
                data_dir=data_dir,
                columns=columns or None,
                n_clusters=n_clusters,
                shrink_ratio=shrink_ratio,
                calib_percentile=calib_percentile,
            )

            if deactivate_others:
                IMSModel.objects.filter(cmg_model=cmg_model, is_active=True).update(is_active=False)

            ims_model = IMSModel.objects.create(
                cmg_model=cmg_model,
                name=model_name,
                parameters=final_cols,
                model_config={
                    "type": "kmeans_ims",
                    "n_clusters": n_clusters,
                    "shrink_ratio": shrink_ratio,
                    "calib_percentile": calib_percentile,
                },
                model_data=model_bytes,
                threshold=threshold,
                is_active=True,
            )

            ims_service.clear_cache()
            serializer = self.get_serializer(ims_model)
            return Response({
                **serializer.data,
                "training_summary": {
                    "parameters": final_cols,
                    "threshold": threshold,
                    "n_clusters": n_clusters,
                    "shrink_ratio": shrink_ratio,
                    "calib_percentile": calib_percentile,
                    "data_dir": data_dir,
                }
            }, status=status.HTTP_201_CREATED)

        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Training failed: {str(e)}"}, status=500)
    
    def _filter_numeric_params(self, training_data, available_params):
        """杩囨护鏁板€煎瀷鍙傛暟"""
        import numpy as np
        
        numeric_params = []
        
        for param in available_params:
            values = []
            for data in training_data[:500]:  # 鍙栨牱妫€鏌?                if isinstance(data.data, dict) and param in data.data:
                    val = data.data[param]
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) > 10:  # 鑷冲皯鏈?0涓湁鏁堟暟鍊?                values = np.array(values)
                # 妫€鏌ユ柟宸?                if np.var(values) > 1e-6:
                    numeric_params.append(param)
        
        return numeric_params
    
    def _load_csv_training_data(self, data_path=""):
        """浠嶤SV鏂囦欢鍔犺浇璁粌鏁版嵁"""
        import pandas as pd
        import numpy as np
        from pathlib import Path
        
        # 榛樿浣跨敤Health鐩綍涓嬬殑CSV鏂囦欢
        if not data_path:
            health_dir = Path(__file__).parent / "algorithms" / "IMS" / "Health"
        else:
            health_dir = Path(data_path)
        
        if not health_dir.exists():
            raise FileNotFoundError(f"璁粌鏁版嵁鐩綍涓嶅瓨鍦? {health_dir}")
        
        # 鏌ユ壘鎵€鏈塁SV鏂囦欢
        csv_files = list(health_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"鍦?{health_dir} 涓湭鎵惧埌CSV鏂囦欢")
        
        all_data = []
        all_columns = set()
        
        for csv_file in csv_files:
            try:
                # 灏濊瘯涓嶅悓鐨勭紪鐮?                for encoding in ['gbk', 'utf-8', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(csv_file, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    continue  # 璺宠繃鏃犳硶璇诲彇鐨勬枃浠?                
                # 鍘绘帀闈炴暟鍊煎垪鍜屾椂闂村垪
                time_columns = ['鏃堕棿', 'time', 'timestamp', '鏃堕棿鎴?, 'ts_iso', '婧愮爜', '缂栧彿', 
                               '甯ц鏁?, '鑷瀛?, 'OSTM_Frame0', 'OSTM_Frame1', '褰撳墠浣嶇疆閿佸畾绮惧害']
                
                # 绉婚櫎鏃堕棿鐩稿叧鍒?                for col in time_columns:
                    if col in df.columns:
                        df = df.drop(columns=[col])
                
                # 鍙繚鐣欐暟鍊煎垪
                numeric_columns = []
                for col in df.columns:
                    try:
                        # 灏濊瘯杞崲涓烘暟鍊?                        numeric_data = pd.to_numeric(df[col], errors='coerce')
                        # 妫€鏌ユ槸鍚︽湁瓒冲鐨勬湁鏁堟暟鍊煎拰鏂瑰樊
                        if numeric_data.notna().sum() > len(df) * 0.5 and numeric_data.var() > 1e-6:
                            numeric_columns.append(col)
                    except:
                        continue
                
                if numeric_columns:
                    df_numeric = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
                    all_data.append(df_numeric)
                    all_columns.update(numeric_columns)
                    
            except Exception as e:
                print(f"璇诲彇鏂囦欢 {csv_file} 鏃跺嚭閿? {e}")
                continue
        
        if not all_data:
            raise ValueError("娌℃湁鏈夋晥鐨勮缁冩暟鎹?)
        
        # 鍚堝苟鎵€鏈夋暟鎹?        combined_data = pd.concat(all_data, ignore_index=True)
        
        # 纭繚鎵€鏈夊垪閮藉瓨鍦?        final_columns = list(all_columns)
        combined_data = combined_data.reindex(columns=final_columns)
        
        # 绉婚櫎鍖呭惈杩囧NaN鐨勮
        threshold = len(final_columns) * 0.7
        combined_data = combined_data.dropna(thresh=threshold)
        
        # 杞崲涓簄umpy鏁扮粍
        data_matrix = combined_data.values.astype(np.float32)
        
        return data_matrix, final_columns
    
    @action(detail=False, methods=["get"], url_path="available-params")
    def get_available_params(self, request):
        """鑾峰彇鍙敤鐨勮缁冨弬鏁?""
        cmg_model_id = request.query_params.get("cmg_model_id")
        if not cmg_model_id:
            return Response(
                {"error": "cmg_model_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from data_management.models import PHMModel
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
            
            # 鑾峰彇鏈€杩戠殑鏁版嵁鏉ュ垎鏋愬弬鏁?            recent_data = PHMData.objects.filter(
                cmg__cmg_model=cmg_model
            ).order_by('-timestamp')[:1000]
            
            if not recent_data:
                return Response({"parameters": []})
            
            # 鍒嗘瀽鍙傛暟
            all_params = set()
            for data in recent_data:
                if isinstance(data.data, dict):
                    all_params.update(data.data.keys())
            
            # 杩囨护鏁板€煎瀷鍙傛暟
            numeric_params = self._filter_numeric_params(recent_data, list(all_params))
            
            return Response({
                "parameters": numeric_params,
                "data_count": recent_data.count()
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"], url_path="activate")
    def activate_model(self, request, pk=None):
        """婵€娲籌MS妯″瀷"""
        try:
            ims_model = self.get_object()
            ims_model.is_active = True
            ims_model.save()
            
            # 娓呯悊缂撳瓨锛屽己鍒堕噸鏂板姞杞?            ims_service.clear_cache()
            
            return Response({"detail": "Model activated"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate_model(self, request, pk=None):
        """鍋滅敤IMS妯″瀷"""
        try:
            ims_model = self.get_object()
            ims_model.is_active = False
            ims_model.save()
            
            # 娓呯悊缂撳瓨
            ims_service.clear_cache()
            
            return Response({"detail": "Model deactivated"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IMSDetectionResultViewSet(viewsets.ReadOnlyModelViewSet):
    """IMS妫€娴嬬粨鏋滆鍥鹃泦"""
    
    queryset = IMSDetectionResult.objects.select_related(
        'data_point', 'data_point__cmg', 'ims_model'
    ).all()
    serializer_class = IMSDetectionResultSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """杩囨护鏌ヨ闆嗭細鍏堟帓搴忓啀鍒囩墖锛岄伩鍏嶅垏鐗囧悗鍐嶆鎺掑簭瀵艰嚧鐨勯敊璇?""
        queryset = super().get_queryset()

        # 缁熶竴鍏堝仛杩囨护
        cmg_id = self.request.query_params.get('cmg_id')
        if cmg_id:
            queryset = queryset.filter(data_point__cmg__cmg_id=cmg_id)

        anomaly_only = self.request.query_params.get('anomaly_only')
        if isinstance(anomaly_only, str) and anomaly_only.lower() == 'true':
            queryset = queryset.filter(is_anomaly=True)

        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(data_point__timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(data_point__timestamp__lte=end_time)

        # 缁熶竴鍦ㄦ渶鍚庢帓搴忎竴娆?        queryset = queryset.order_by('-created_at')

        return queryset
    
    def list(self, request, *args, **kwargs):
        """閲嶅啓list鏂规硶鏀寔鍒嗛〉"""
        queryset = self.get_queryset()
        
        # 鑾峰彇鍒嗛〉鍙傛暟
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')
        
        # 濡傛灉娌℃湁鍒嗛〉鍙傛暟锛屼娇鐢ㄥ師鏈夐€昏緫
        if not offset:
            if limit:
                try:
                    limit_val = int(limit)
                    queryset = queryset[:limit_val]
                except (TypeError, ValueError):
                    pass
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        # 鍒嗛〉閫昏緫
        try:
            limit = int(limit) if limit else 500
            offset = int(offset) if offset else 0
        except (TypeError, ValueError):
            limit = 500
            offset = 0
            
        # 鑾峰彇鎬绘暟
        total_count = queryset.count()
        
        # 鍒嗛〉鏁版嵁
        paginated_queryset = queryset[offset:offset + limit]
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'limit': limit,
            'offset': offset
        })
    
    @action(detail=False, methods=["get"], url_path="anomaly-data")
    def get_anomaly_data(self, request):
        """鑾峰彇鍖呭惈IMS妫€娴嬬粨鏋滅殑寮傚父鏁版嵁"""
        cmg_id = request.query_params.get('cmg_id')
        if not cmg_id:
            return Response(
                {"error": "cmg_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        limit = int(request.query_params.get('limit', 1000))
        
        try:
            if start_time:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if end_time:
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {"error": "Invalid datetime format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        anomaly_only = request.query_params.get('anomaly_only', 'false').lower() == 'true'
        data = get_anomaly_data_with_ims(cmg_id, start_time, end_time, limit, anomaly_only)
        return Response(data)
    
    @action(detail=False, methods=["get"], url_path="overview-anomalies")
    def get_overview_anomalies(self, request):
        """涓衡€滄娴嬬粨鏋滄€昏鈥濋〉闈㈡彁渚涚嫭绔嬬殑寮傚父鏁版嵁鎺ュ彛"""
        cmg_pk = request.query_params.get('cmg_id')
        if not cmg_pk:
            return Response({"error": "cmg_id (pk) is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cmg = PHM.objects.get(pk=cmg_pk)
        except (PHM.DoesNotExist, ValueError):
            return Response({"error": "PHM not found"}, status=status.HTTP_404_NOT_FOUND)

        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')

        queryset = IMSDetectionResult.objects.filter(
            data_point__cmg=cmg,
            is_anomaly=True
        ).select_related('ims_model').order_by('-data_point__timestamp')

        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                queryset = queryset.filter(data_point__timestamp__gte=start_time)
            except ValueError:
                pass
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                queryset = queryset.filter(data_point__timestamp__lte=end_time)
            except ValueError:
                pass
        
        # 鐩存帴搴忓垪鍖栨煡璇㈢粨鏋?        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="statistics")
    def get_statistics(self, request):
        """鑾峰彇IMS妫€娴嬬粺璁′俊鎭?""
        cmg_id = request.query_params.get('cmg_id')
        if not cmg_id:
            return Response(
                {"error": "cmg_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        hours = int(request.query_params.get('hours', 24))
        stats = ims_service.get_detection_statistics(cmg_id, hours)
        return Response(stats)
