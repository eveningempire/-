"""
Views for the Intelligent Sensing module.

This module provides API endpoints for visualizing PHM intelligent sensing
research results, including prediction performance comparisons and multi-layer
degradation coupling effects.
"""

import json
import logging
import sys
from pathlib import Path

from django.http import JsonResponse
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Path to ganzhi module
BASE_DIR = Path(__file__).resolve().parent
GANZHI_DIR = BASE_DIR / "ganzhi"
QIANCAIYANG_DIR = BASE_DIR / "qiancaiyang"

# Add ganzhi and qiancaiyang to Python path
sys.path.insert(0, str(GANZHI_DIR))
sys.path.insert(0, str(QIANCAIYANG_DIR))


@api_view(['GET'])
def get_prediction_results(request):
    """
    Get prediction results comparison for different experiments.
    
    Query Parameters:
        exp: Experiment ID (015, 016, 017, 018), default='015'
    
    Returns:
        JSON with prediction results including:
        - base: baseline model results
        - fusion_b_k: fusion model with b_k parameters
        - fusion_u_v: fusion model with u_v parameters
    """
    exp = request.GET.get('exp', '015')
    
    if exp not in ['015', '016', '017', '018']:
        return Response(
            {'error': f'Invalid experiment ID: {exp}. Must be one of: 015, 016, 017, 018'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Import year1 module
        import year1
        
        # Call get_all_predict_result which returns a JSON string
        json_str = year1.get_all_predict_result(exp=exp)
        
        # Parse JSON string to dict
        data = json.loads(json_str)
        
        return Response(data)
            
    except ImportError as e:
        logger.error(f"Failed to import year1 module: {str(e)}")
        return Response(
            {'error': 'Failed to load prediction module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
        return Response(
            {'error': 'Required data files not found', 'detail': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error loading prediction results: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to load prediction results', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_coupling_layers(request):
    """
    Get multi-layer degradation coupling data.
    
    Returns:
        JSON with three layers of coupling effects:
        - layer1: Bearing degradation 鈫?Coupling torque increase
        - layer2: Frame tracking accuracy degradation
        - layer3: PHM output accuracy reduction
    """
    try:
        # Import year1 module
        import year1
        
        # Call get_coupling_layers which returns a JSON string
        json_str = year1.get_coupling_layers()
        
        # Parse JSON string to dict
        data = json.loads(json_str)
        
        return Response(data)
            
    except ImportError as e:
        logger.error(f"Failed to import year1 module: {str(e)}")
        return Response(
            {'error': 'Failed to load coupling layers module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
        return Response(
            {'error': 'Required data files not found (sim_results.pkl)', 'detail': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error loading coupling layer data: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to load coupling layer data', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_random_sampling_data(request):
    """
    Get random sampling results for different sampling rates.
    
    Query Parameters:
        group: Group number (1, 2, 3, or 4), default=1
    
    Returns:
        JSON with random sampling data for different sampling rates,
        including time domain and frequency domain comparisons with similarity metrics.
    """
    group = int(request.GET.get('group', 1))
    
    if group not in [1, 2, 3, 4, 11, 12]:
        return Response(
            {'error': 'Invalid group data file'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from table9 import get_random_sampling_res
        
        # Get JSON string result
        json_str = get_random_sampling_res(group=group)
        
        # Parse JSON string to dict
        data = json.loads(json_str)
        
        return Response(data)
            
    except ImportError as e:
        logger.error(f"Failed to import table9 module: {str(e)}")
        return Response(
            {'error': 'Failed to load random sampling module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error loading random sampling data: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to load random sampling data', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_undersampling_reconstruction_data_bak(request):
    """
    Get undersampling reconstruction results using new reconstruction engine.
    
    Query Parameters:
        group: Group number (1, 2, 3, or 4), default=1
    
    Returns:
        JSON with undersampling reconstruction data including original signal,
        downsampled signal, reconstructed signal, and reconstruction metrics.
    """
    group = int(request.GET.get('group', 1))
    
    if group not in [1, 2, 3, 4]:
        return Response(
            {'error': f'Invalid group: {group}. Must be 1, 2, 3, or 4'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        import numpy as np
        import pandas as pd
        import os
        from pathlib import Path
        
        # Define data paths based on group
        current_dir = Path(__file__).resolve().parent
        data_base_dir = current_dir / "qiancaiyang" / "data"
        
        file_map = {
            1: data_base_dir / "table9灞曠ず鏁版嵁" / "data1.csv",
            2: data_base_dir / "table9灞曠ず鏁版嵁" / "data2.csv",
            3: data_base_dir / "table9灞曠ず鏁版嵁" / "data3.csv",
            # 4: data_base_dir / "real_data_1Hz.csv",
            4: data_base_dir / "real_data_8Hz.csv",
        }
        
        target_file = file_map.get(group)
        if not target_file.exists():
             raise FileNotFoundError(f"Data file not found: {target_file}")
             
        # Load data
        # Assuming single column CSVs or handling specific formats
        if group == 4:
            # real_data_1Hz.csv might have specific format
            df = pd.read_csv(target_file, header=None)
            # Take a segment for display (e.g. first 1000 points)
            data_segment = df.iloc[:1000, 0].values.flatten()
            fs_original = 1.0 # 1Hz
        else:
            # data1.csv etc usually are high frequency data
            df = pd.read_csv(target_file, header=None)
            data_segment = df.iloc[:1000, 0].values.flatten()
            fs_original = 20.0 # Assumption for these datasets based on history
            
        # Standardize data length for display consistency
        n_points = len(data_segment)
        t_ori = np.arange(n_points) / fs_original
        signal_ori = data_segment
        
        # Undersampling logic (simulate sparse sampling)
        # Use different factors for different kinds of data to show effect
        downsample_factor = 8 if group == 4 else 10
        
        t_down = t_ori[::downsample_factor]
        signal_down = signal_ori[::downsample_factor]
        
        # Use reconstruction engine
        from .qiancaiyang.reconstruction_engine import SignalReconstructor
        
        # For guided reconstruction we ideally need a reference segment
        # Here we use the first part of signal itself as reference for demonstration
        # In a real scenario, this might come from a different historical period
        ref_len = min(200, len(signal_ori) // 5)
        t_ref = t_ori[:ref_len]
        y_ref = signal_ori[:ref_len]
        
        reconstructor = SignalReconstructor(y_ref, t_ref)
        
        # Choose reconstruction method based on what works best or show comparison
        # Here we use guided spectral for best results
        signal_recon = reconstructor.guided_spectral_reconstruct(t_down, signal_down, t_ori)
        
        # Metrics
        rmse = np.sqrt(np.mean((signal_ori - signal_recon) ** 2))
        mae = np.mean(np.abs(signal_ori - signal_recon))
        
        norm_ori = np.linalg.norm(signal_ori)
        norm_recon = np.linalg.norm(signal_recon)
        if norm_ori > 0 and norm_recon > 0:
            cos_sim = np.dot(signal_ori, signal_recon) / (norm_ori * norm_recon)
        else:
            cos_sim = 0.0
            
        # Construct response
        # Limit FFT points for performance
        fft_n = min(len(t_ori), 1024)
        
        result = [{
            'undersampling': {
                'x': t_ori.tolist(),
                'y_original': signal_ori.tolist(),
                'y_downsampled_points': t_down.tolist(),
                'y_downsampled_values': signal_down.tolist()
            },
            'reconstruction': {
                'x': t_ori.tolist(),
                'y_original': signal_ori.tolist(),
                'y_reconstructed': signal_recon.tolist()
            },
            'frequency': {
                'freq': np.fft.rfftfreq(fft_n, 1/fs_original).tolist()[:50],
                'mag_original': (np.abs(np.fft.rfft(signal_ori[:fft_n])) / fft_n).tolist()[:50],
                'mag_reconstructed': (np.abs(np.fft.rfft(signal_recon[:fft_n])) / fft_n).tolist()[:50]
            },
            'recon_metrics': {
                'rmse': float(rmse),
                'mae': float(mae),
                'cos_sim': float(cos_sim)
            }
        }]
        
        return Response(result)
            
    except ImportError as e:
        logger.error(f"Failed to import reconstruction_engine module: {str(e)}")
        return Response(
            {'error': 'Failed to load reconstruction engine module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error in reconstruction: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to perform reconstruction', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_undersampling_reconstruction_data(request):
    """
    Get undersampling reconstruction results using new reconstruction engine.
    
    Query Parameters:
        group: Group number (1, 2, 3, or 4), default=1
    
    Returns:
        JSON with undersampling reconstruction data including original signal,
        downsampled signal, reconstructed signal, and reconstruction metrics.
    """
    group = int(request.GET.get('group', 1))
    
    if group not in [1, 2, 3, 4]:
        return Response(
            {'error': f'Invalid group: {group}. Must be 1, 2, 3, or 4'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        import json
        # 瀵煎叆 table9 涓殑鏍稿績閫昏緫鍑芥暟
        from table9 import get_low_sampling_res
        
        # 璋冪敤 table9 涓殑閫昏緫 (杩斿洖 JSON 瀛楃涓?
        # table9.py 鍐呴儴浼氬鐞?DATA_DIR 璺緞
        json_res = get_low_sampling_res(group=group, plot=False)
        table9_res = json.loads(json_res)
        
        # 閲嶇粍鏁版嵁缁撴瀯浠ュ尮閰嶅師鏈夌殑 Response 鏍煎紡
        # table9_res[0]: 鍖呭惈 x1(閲囨牱鐐规椂闂?, y1(閲囨牱鍊?, x2(鍘熷鍏ㄩ噺鏃堕棿), y2(鍘熷鍏ㄩ噺鍊?
        # table9_res[1]: 鍖呭惈 x(璇︽儏鏃堕棿), y1(鍘熷璇︽儏), y2(閲嶅缓璇︽儏), recon_metrics(鎸囨爣)
        # table9_res[2]: 鍖呭惈 x1(鍘熷棰戠巼), y1(鍘熷骞呭€?, x2(閲嶅缓棰戠巼), y2(閲嶅缓骞呭€?
        
        result = [{
            'undersampling': {
                'x': table9_res[0]['x2']['value'],
                'y_original': table9_res[0]['y2']['value'],
                'y_downsampled_points': table9_res[0]['x1']['value'],
                'y_downsampled_values': table9_res[0]['y1']['value']
            },
            'reconstruction': {
                'x': table9_res[1]['x']['value'],
                'y_original': table9_res[1]['y1']['value'],
                'y_reconstructed': table9_res[1]['y2']['value']
            },
            'frequency': {
                'freq': table9_res[2]['x1']['value'],
                'mag_original': table9_res[2]['y1']['value'],
                'mag_reconstructed': table9_res[2]['y2']['value']
            },
            'recon_metrics': table9_res[1]['recon_metrics']
        }]
        
        return Response(result)
            
    except ImportError as e:
        logger.error(f"Failed to import module: {str(e)}")
        return Response(
            {'error': 'Failed to load reconstruction core module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:
        logger.error(f"Error in reconstruction: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to perform reconstruction', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_limited_sensing_data(request):
    """
    Get limited sensing information test results.
    
    Query Parameters:
        group: Group number (1, 2, 3, or 4), default=1
    
    Returns:
        JSON with limited sensing data showing performance comparison
        between limited channels (3) and augmented channels (5).
    """
    group = int(request.GET.get('group', 1))
    
    if group not in [1, 2, 3]:
        return Response(
            {'error': f'Invalid group: {group}. Must be 1, 2, 3'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from table10 import get_limited_sensing_res
        
        # Get JSON string result
        json_str = get_limited_sensing_res(group=group)
        
        # Parse JSON string to dict
        data = json.loads(json_str)
        
        return Response(data)
            
    except ImportError as e:
        logger.error(f"Failed to import table10 module: {str(e)}")
        return Response(
            {'error': 'Failed to load limited sensing module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error loading limited sensing data: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to load limited sensing data', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_online_learning_data(request):
    """
    Get online learning results comparing different model update strategies.
    
    Query Parameters:
        group: Group number (1, 2, 3, or 4), default=1 (Ignored in new version)
    
    Returns:
        JSON with online learning data comparing original model,
        SGD-updated model, and OSELM-updated model performance.
    """
    group = int(request.GET.get('group', 1))
    if group not in [1, 2]:
        return Response(
            {'error': f'Invalid group: {group}. Must be 1, 2'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from table11 import get_online_adaptive_results_service
        
        # Get JSON string result
        json_str = get_online_adaptive_results_service(group=group, force_run=False)
        
        # Parse JSON string to dict
        data = json.loads(json_str)
        
        return Response(data)
            
    except ImportError as e:
        logger.error(f"Failed to import table11 module: {str(e)}")
        return Response(
            {'error': 'Failed to load online learning module', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Error loading online learning data: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to load online learning data', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

