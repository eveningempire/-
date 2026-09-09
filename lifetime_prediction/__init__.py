"""
瀵垮懡棰勬祴API瑙嗗浘

鎻愪緵瀵垮懡棰勬祴鍔熻兘鐨凴ESTful API鎺ュ彛銆?
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .services import LifetimePredictionService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_algorithms(request):
    """鑾峰彇鍙敤鐨勭畻娉曞垪琛?""
    try:
        service = LifetimePredictionService()
        algorithms = service.get_available_algorithms()
        
        return Response({
            'status': 'success',
            'data': algorithms,
            'count': len(algorithms)
        })
    except Exception as e:
        logger.error(f"鑾峰彇绠楁硶鍒楄〃澶辫触: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'鑾峰彇绠楁硶鍒楄〃澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_cmgs(request):
    """鑾峰彇鍙敤鐨凜MG鍒楄〃"""
    try:
        service = LifetimePredictionService()
        cmgs = service.get_available_cmgs()
        
        return Response({
            'status': 'success',
            'data': cmgs,
            'count': len(cmgs)
        })
    except Exception as e:
        logger.error(f"鑾峰彇PHM鍒楄〃澶辫触: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'鑾峰彇PHM鍒楄〃澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_prediction_summary(request, cmg_id):
    """鑾峰彇鎸囧畾PHM鐨勯娴嬫憳瑕佷俊鎭?""
    try:
        service = LifetimePredictionService()
        summary = service.get_prediction_summary(cmg_id)
        
        if 'error' in summary:
            return Response({
                'status': 'error',
                'message': summary['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"鑾峰彇棰勬祴鎽樿澶辫触: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'鑾峰彇棰勬祴鎽樿澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def predict_lifetime(request):
    """鎵ц瀵垮懡棰勬祴"""
    try:
        cmg_id = request.data.get('cmg_id')
        design_life = request.data.get('design_life')
        start_time = request.data.get('start_time')  # PHM鍚敤鏃堕棿
        data_start_time = request.data.get('data_start_time')  # 鏁版嵁鏌ヨ寮€濮嬫椂闂?
        end_time = request.data.get('end_time')  # 鏁版嵁鏌ヨ缁撴潫鏃堕棿
        algorithm = request.data.get('algorithm', 'strategy0')  # 绠楁硶閫夋嫨锛岄粯璁や负strategy0
        
        # 娣诲姞鍙傛暟杩借釜鏃ュ織
        logger.info(f"[鍙傛暟杩借釜] API鎺ユ敹鍒扮殑鍙傛暟 - cmg_id: {cmg_id}, design_life: {design_life} (绫诲瀷: {type(design_life)}), start_time: {start_time}, algorithm: {algorithm}")
        
        if not cmg_id:
            return Response({
                'status': 'error',
                'message': '缂哄皯蹇呴渶鐨勫弬鏁? cmg_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not design_life:
            return Response({
                'status': 'error',
                'message': '缂哄皯蹇呴渶鐨勫弬鏁? design_life'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not start_time:
            return Response({
                'status': 'error',
                'message': '缂哄皯蹇呴渶鐨勫弬鏁? start_time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 鍒ゆ柇鏄惁浣跨敤鏃堕棿娈佃繃婊?
        # 濡傛灉鎻愪緵浜哾ata_start_time鍜宔nd_time锛屽垯浣跨敤鏃堕棿娈佃繃婊わ紙PHM璇︽儏椤甸潰锛?
        # 鍚﹀垯鍙幏鍙栨渶鍚?000鏉℃暟鎹紙瀵垮懡棰勬祴鐣岄潰锛?
        # 娉ㄦ剰锛氫袱涓晫闈㈤兘闇€瑕乻tart_time锛堝惎鐢ㄦ椂闂达級锛屼絾鍙湁PHM璇︽儏椤甸潰闇€瑕佹椂闂存杩囨护
        use_time_range = bool(data_start_time and end_time)
        
        service = LifetimePredictionService()
        result = service.predict_lifetime(
            cmg_id, 
            design_life=design_life,
            start_time=start_time,  # PHM鍚敤鏃堕棿
            data_start_time=data_start_time,  # 鏁版嵁鏌ヨ寮€濮嬫椂闂?
            end_time=end_time,  # 鏁版嵁鏌ヨ缁撴潫鏃堕棿
            use_time_range=use_time_range,  # 鏄惁浣跨敤鏃堕棿娈佃繃婊?
            algorithm=algorithm  # 绠楁硶閫夋嫨
        )
        
        if result.get('status') == 'error':
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"瀵垮懡棰勬祴澶辫触: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'瀵垮懡棰勬祴澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_telemetry_data(request, cmg_id):
    """鑾峰彇鎸囧畾PHM鐨勯仴娴嬫暟鎹紙鐢ㄤ簬璋冭瘯锛?""
    try:
        limit = int(request.GET.get('limit', 100))
        service = LifetimePredictionService()
        data = service.get_cmg_data(cmg_id, limit=limit)
        
        return Response({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"鑾峰彇閬ユ祴鏁版嵁澶辫触: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'鑾峰彇閬ユ祴鏁版嵁澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """鍋ュ悍妫€鏌ユ帴鍙?""
    return Response({
        'status': 'success',
        'message': '瀵垮懡棰勬祴鏈嶅姟姝ｅ父杩愯',
        'service': 'lifetime_prediction'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def finetune_model(request):
    """
    妯″瀷寰皟鎺ュ彛
    鏀寔AE鍜孷AE涓ょ绠楁硶鐨勫閲忓涔?鍦ㄧ嚎寰皟
    鏀寔鏁版嵁搴撴暟鎹拰鏂囦欢涓婁紶涓ょ鏁版嵁鏉ユ簮
    """
    try:
        cmg_id = request.data.get('cmg_id')
        algorithm = request.data.get('algorithm', 'strategy0')  # strategy0=AE, strategy1=VAE
        data_source = request.data.get('data_source', 'database')  # 'database' 鎴?'file'
        data_start_time = request.data.get('data_start_time')  # 鏂版暟鎹紑濮嬫椂闂?
        data_end_time = request.data.get('data_end_time')  # 鏂版暟鎹粨鏉熸椂闂?
        uploaded_file = request.FILES.get('file')  # 涓婁紶鐨勬枃浠?
        epochs = int(request.data.get('epochs', 50))  # 寰皟杞暟
        batch_size = int(request.data.get('batch_size', 64))  # 鎵瑰ぇ灏?
        learning_rate = float(request.data.get('learning_rate', 1e-4))  # 瀛︿範鐜?
        
        # 鍙傛暟楠岃瘉
        if not cmg_id:
            return Response({
                'status': 'error',
                'message': '缂哄皯蹇呴渶鐨勫弬鏁? cmg_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if algorithm not in ['strategy0', 'strategy1']:
            return Response({
                'status': 'error',
                'message': f'涓嶆敮鎸佺殑绠楁硶: {algorithm}锛屼粎鏀寔 strategy0 (AE) 鍜?strategy1 (VAE)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if data_source not in ['database', 'file']:
            return Response({
                'status': 'error',
                'message': f'涓嶆敮鎸佺殑鏁版嵁鏉ユ簮: {data_source}锛屼粎鏀寔 database 鍜?file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 楠岃瘉鏁版嵁鏉ユ簮瀵瑰簲鐨勫弬鏁?
        if data_source == 'file' and not uploaded_file:
            return Response({
                'status': 'error',
                'message': '閫夋嫨鏂囦欢涓婁紶鏃讹紝蹇呴』鎻愪緵鏂囦欢'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if data_source == 'database' and not data_start_time and not data_end_time:
            logger.info("浣跨敤鏁版嵁搴撴暟鎹絾鏈寚瀹氭椂闂磋寖鍥达紝灏嗕娇鐢ㄦ渶鏂版暟鎹?)
        
        logger.info(f"寮€濮嬫ā鍨嬪井璋?- PHM: {cmg_id}, 绠楁硶: {algorithm}, 鏁版嵁鏉ユ簮: {data_source}, 杞暟: {epochs}, 瀛︿範鐜? {learning_rate}")
        
        service = LifetimePredictionService()
        result = service.finetune_model(
            cmg_id=cmg_id,
            algorithm=algorithm,
            data_source=data_source,
            data_start_time=data_start_time,
            data_end_time=data_end_time,
            uploaded_file=uploaded_file,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        
        if result.get('status') == 'error':
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        logger.error(f"鍙傛暟閿欒: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'鍙傛暟閿欒: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"妯″瀷寰皟澶辫触: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': f'妯″瀷寰皟澶辫触: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
