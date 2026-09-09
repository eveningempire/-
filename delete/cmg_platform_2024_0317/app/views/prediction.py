import os
import sys
import datetime
from flask import Blueprint, render_template, request, jsonify
from app import redis_engine
from app.config import TRAIN_DATA_PATH, TEST_DATA_PATH, MODEL_PATH

# 添加predict路径到sys.path
sys.path.append(os.path.join(os.getcwd(), 'predict'))

# 导入预测相关函数
try:
    from io_utils import ioooo, ioooo2
except ImportError:
    print("Warning: io_utils module could not be imported. Prediction functionality may be limited.")

# 创建蓝图
prediction_bp = Blueprint('prediction', __name__)

# 预测页面
@prediction_bp.route('/predict', methods=['GET', 'POST'])
def predict():
    return render_template("predict.html")

# 自动预测页面
@prediction_bp.route('/predictauto', methods=['GET', 'POST'])
def predictauto():
    return render_template("predictauto.html")

# 列出文件
@prediction_bp.route('/predict/list-files', methods=['GET'])
def predict_list_files():
    # 列出traindata和testdata下的文件
    train_files = os.listdir(TRAIN_DATA_PATH)
    test_files = os.listdir(TEST_DATA_PATH)
    # 列出predict/model下的文件
    model_files = os.listdir(MODEL_PATH) if os.path.exists(MODEL_PATH) else []

    return jsonify({
        "traindata": train_files,
        "testdata": test_files,
        "models": model_files
    })

# 训练接口
@prediction_bp.route('/api/train', methods=['POST'])
def api_train():
    train_or_test = request.form.get('train_or_test')
    algorithm = request.form.get('algorithm')
    modelName = request.form.get('modelName')
    trainingDataFileName = request.form.get('trainingData')
    testingDataFileName = request.form.get('testingData')
    epochs = int(request.form.get('epochs', 1))

    allowed_training_data_dir = TRAIN_DATA_PATH
    allowed_testing_data_dir = TEST_DATA_PATH

    if trainingDataFileName:
        trainingDataFullPath = os.path.join(allowed_training_data_dir, trainingDataFileName)
        if testingDataFileName:
            testingDataFullPath = os.path.join(allowed_testing_data_dir, testingDataFileName)
        else:
            testingDataFullPath = None
        if not os.path.isfile(trainingDataFullPath):
            return jsonify({'result': 'Invalid training data path'}), 400
    else:
        return jsonify({'result': '未上传训练数据'}), 400

    # 为模型名称添加时间戳和.pth后缀(如果没有的话)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if not modelName.endswith('.pth'):
        modelName = f"{modelName}_{timestamp}.pth"
    else:
        modelName = modelName.replace('.pth', f'_{timestamp}.pth')
    
    # 构造模型完整路径
    modelFullPath = os.path.join(MODEL_PATH, modelName)

    result = ioooo(  # 这里使用ioooo
        train_or_test='train',
        algorithm=algorithm,
        train_data_dir=trainingDataFullPath,
        test_data_dir=testingDataFullPath,
        train_model_save_dir=modelFullPath,
        test_model_load_dir=None,
        epochs=epochs
    )

    return jsonify({'result': result})

# 测试接口
@prediction_bp.route('/api/test', methods=['POST'])
def api_test():
    train_or_test = request.form.get('train_or_test')
    algorithm = request.form.get('algorithm')  # 前端传来的算法名称
    modelName = request.form.get('modelName')
    testingDataFileName = request.form.get('testingData')

    # 检验测试数据
    allowed_testing_data_dir = TEST_DATA_PATH
    if testingDataFileName:
        testingDataFullPath = os.path.join(allowed_testing_data_dir, testingDataFileName)
        if not os.path.isfile(testingDataFullPath):
            return jsonify({'result': 'Invalid testing data path'}), 400
    else:
        return jsonify({'result': '未上传测试数据'}), 400

    # 构造模型完整路径
    modelFullPath = os.path.join(MODEL_PATH, modelName)
    if not os.path.isfile(modelFullPath):
        return jsonify({'result': '模型文件不存在'}), 400

    try:
        # 使用ioooo进行测试，并传入algorithm参数
        result_ = ioooo(
            train_or_test='test',
            algorithm=algorithm,  # 明确传入算法参数
            train_data_dir=None,
            train_model_save_dir=None,
            test_data_dir=testingDataFullPath,
            test_model_load_dir=modelFullPath
        )

        result = {}
        result['test_label'] = result_[0]
        result['test_output'] = result_[1]
        result['RMSE'] = result_[2]
        result['MAE'] = result_[3]
        result['xlogo'] = result_[4]
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"测试过程中出现错误: {e}\n{error_detail}")
        return jsonify({'result': f'测试失败: {str(e)}'}), 500

# 自动训练接口
@prediction_bp.route('/api/train_auto', methods=['POST'])
def api_train_auto():
    train_or_test = request.form.get('train_or_test')
    algorithm = request.form.get('algorithm')
    modelName = request.form.get('modelName')
    trainingDataFileName = request.form.get('trainingData')
    testingDataFileName = request.form.get('testingData')
    epochs = int(request.form.get('epochs', 1))

    allowed_training_data_dir = TRAIN_DATA_PATH
    allowed_testing_data_dir = TEST_DATA_PATH

    if trainingDataFileName:
        trainingDataFullPath = os.path.join(allowed_training_data_dir, trainingDataFileName)
        if not os.path.isfile(trainingDataFullPath):
            return jsonify({'result': 'Invalid training data path'}), 400
    else:
        return jsonify({'result': '未上传训练数据'}), 400

    # 在训练模式中，测试数据可能为空，但ioooo2需要测试数据路径
    # 因此，如果没有提供测试数据，使用训练数据作为测试数据
    if testingDataFileName:
        testingDataFullPath = os.path.join(allowed_testing_data_dir, testingDataFileName)
        if not os.path.isfile(testingDataFullPath):
            # 如果测试数据路径无效，使用训练数据作为测试数据
            testingDataFullPath = trainingDataFullPath
    else:
        # 如果没有提供测试数据，使用训练数据作为测试数据
        testingDataFullPath = trainingDataFullPath

    # 为模型名称添加时间戳和.pth后缀
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if not modelName.endswith('.pth'):
        modelName = f"{modelName}_{timestamp}.pth"
    else:
        modelName = modelName.replace('.pth', f'_{timestamp}.pth')
    
    # 构造模型完整路径
    modelFullPath = os.path.join(MODEL_PATH, modelName)

    try:
        # 使用ioooo2函数
        result = ioooo2(
            train_or_test='train',
            algorithm=algorithm,
            train_data_dir=trainingDataFullPath,
            test_data_dir=testingDataFullPath,
            train_model_save_dir=modelFullPath,
            test_model_load_dir=None,
            epochs=epochs
        )
        
        # 处理结果
        if isinstance(result, tuple) and len(result) > 0:
            # 从元组中获取训练结果字符串
            result_str = result[0]
            print(f"训练完成")
        else:
            result_str = str(result)
            print(f"训练完成，非元组结果: {result_str}")
        
        # 确保结果是字符串类型并且完整返回
        response_data = {'result': result_str}
        return jsonify(response_data)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"训练过程中出现错误: {e}\n{error_detail}")
        return jsonify({'result': f'训练失败: {str(e)}'}), 500

# 自动测试接口
@prediction_bp.route('/api/test_auto', methods=['POST'])
def api_test_auto():
    train_or_test = request.form.get('train_or_test')
    algorithm = request.form.get('algorithm') 
    modelName = request.form.get('modelName')
    testingDataFileName = request.form.get('testingData')

    # 检验测试算法
    if not algorithm:
        return jsonify({'result': '请选择测试算法'}), 400

    # 检验测试数据
    allowed_testing_data_dir = TEST_DATA_PATH
    if testingDataFileName:
        testingDataFullPath = os.path.join(allowed_testing_data_dir, testingDataFileName)
        if not os.path.isfile(testingDataFullPath):
            return jsonify({'result': 'Invalid testing data path'}), 400
    else:
        return jsonify({'result': '未上传测试数据'}), 400

    # 构造模型完整路径
    modelFullPath = os.path.join(MODEL_PATH, modelName)
    if not os.path.isfile(modelFullPath):
        return jsonify({'result': '模型文件不存在'}), 400

    try:
        print(f"开始测试: 算法={algorithm}, 数据={testingDataFileName}, 模型={modelName}")
        # 使用ioooo2进行测试，明确传递算法名称
        result_ = ioooo2(
            train_or_test='test',
            algorithm=algorithm,
            train_data_dir=None,  # 测试时不需要训练数据
            train_model_save_dir=None,
            test_data_dir=testingDataFullPath,
            test_model_load_dir=modelFullPath
        )

        result = {}
        result['test_label'] = result_[0]
        result['test_output'] = result_[1]
        result['RMSE'] = result_[2]
        result['MAE'] = result_[3]
        result['xlogo'] = result_[4]
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"测试过程中出现错误: {e}\n{error_detail}")
        return jsonify({'result': f'测试失败: {str(e)}'}), 500
