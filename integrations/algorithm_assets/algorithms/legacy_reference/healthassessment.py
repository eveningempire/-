import random
import time 
from datetime import datetime
import json
import numpy as np
from scipy.special import erf
file_path_start = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\start_stop.json'
file_path_list = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\default_select_faults.json'
data = {
    "parameters": [
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA001",
            "para_name": "充电输出电流_0",
            "para_value": "10",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "5"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA002",
            "para_name": "充电通道电压_0",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "240",
            "para_low": "200"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA003",
            "para_name": "负载电流_0",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "0"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA004",
            "para_name": "配电母线电流_0",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "0"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA005",
            "para_name": "配电母线电压_0",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "6",
            "para_low": "4"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA006",
            "para_name": "充电输出电流_d",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "5"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA007",
            "para_name": "充电通道电压_d",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "240",
            "para_low": "220"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA008",
            "para_name": "配电母线电压_d",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "6",
            "para_low": "4"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA009",
            "para_name": "充电输出电流_i",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "1"
        },
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "para_code": "PA010",
            "para_name": "负载电流_d",
            "para_value": "20",
            "belong_system": "电源系统",
            "para_up": "10",
            "para_low": "1"
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA011",
          "para_name": "负载电压_d",
          "para_value": "20",
          "belong_system": "电源系统",
          "para_up": "240",
          "para_low": "200",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA012",
          "para_name": "配电母线电流_d",
          "para_value": "20",
          "belong_system": "电源系统",
          "para_up": "10",
          "para_low": "1",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA013",
          "para_name": "U1示数",
          "para_value": "20",
          "belong_system": "电源系统",
          "para_up": "15",
          "para_low": "1",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA014",
          "para_name": "U2示数",
          "para_value": "20",
          "belong_system": "电源系统",
          "para_up": "15",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA015",
          "para_name": "配电母线电流_i",
          "para_value": "20",
          "belong_system": "电源系统",
          "para_up": "10",
          "para_low": "1",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA016",
          "para_name": "遥控门限灵敏度",
          "para_value": "20",
          "belong_system": "测控系统",
          "para_up": "10",
          "para_low": "1",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA017",
          "para_name": "遥控测试",
          "para_value": "20",
          "belong_system": "测控系统",
          "para_up": "1",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA018",
          "para_name": "测距测试",
          "para_value": "20",
          "belong_system": "测控系统",
          "para_up": "1",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA019",
          "para_name": "外涂层温度",
          "para_value": "20",
          "belong_system": "热控系统",
          "para_up": "500",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA020",
          "para_name": "储液器温度",
          "para_value": "20",
          "belong_system": "热控系统",
          "para_up": "1000",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA021",
          "para_name": "控温点1温度",
          "para_value": "20",
          "belong_system": "热控系统",
          "para_up": "100",
          "para_low": "0",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA022",
          "para_name": "氧化剂管路流量",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "20",
          "para_low": "5",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA023",
          "para_name": "氧化剂涡轮泵压",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "150",
          "para_low": "100",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA024",
          "para_name": "尾喷管推力1",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "80",
          "para_low": "60",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA025",
          "para_name": "燃料管路流量",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "10",
          "para_low": "5",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA026",
          "para_name": "燃料涡轮泵压",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "150",
          "para_low": "100",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA027",
          "para_name": "氧化剂主阀1开度",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "90",
          "para_low": "30",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA028",
          "para_name": "氧化剂主阀2开度",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "90",
          "para_low": "30",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA029",
          "para_name": "氧化剂涡轮泵汽含量",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "100",
          "para_low": "50",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA030",
          "para_name": "尾喷管推力2",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "80",
          "para_low": "60",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA031",
          "para_name": "燃料主阀1开度",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "90",
          "para_low": "30",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA032",
          "para_name": "燃料主阀2开度",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "90",
          "para_low": "30",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA033",
          "para_name": "燃料涡轮泵口厚度",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "3",
          "para_low": "2",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA034",
          "para_name": "燃气生成量1",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "20",
          "para_low": "10",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA035",
          "para_name": "燃气生成量2",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "20",
          "para_low": "10",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA036",
          "para_name": "氧化剂喷嘴流量",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "20",
          "para_low": "5",
        },
        {
          "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "para_code": "PA037",
          "para_name": "燃料喷嘴流量",
          "para_value": "20",
          "belong_system": "动力系统",
          "para_up": "20",
          "para_low": "5",
        },
        # 可以继续添加更多的数据项
    ]
}
max_length = 10
X=[
  [7.2912, 218.069, 2.7839, 4.8381, 4.8027, 8.2179, 225.7336, 5.1305, 5.5289, 3.4775, 219.3768, 6.7481, 7.085, 6.9545, 5.5497, 7.2843, 0.6375, 0.588, 162.1391, 514.4881, 35.9765, 12.2249, 121.6235, 73.6468, 7.8755, 120.6438, 52.5863, 45.4324, 66.8019, 68.7638, 66.1196, 50.0438, 2.4576, 13.0973, 16.5993, 8.857, 11.3012],
  [7.5193, 226.4643, 4.9994, 3.1824, 4.6091, 8.0562, 234.2074, 5.4037, 7.2322, 4.7627, 217.8941, 4.1453, 7.3293, 6.8115, 4.8487, 5.8428, 0.4087, 0.5698, 251.3467, 562.9322, 31.3604, 13.4506, 128.4435, 68.0206, 8.2992, 130.8032, 58.9751, 51.8543, 67.7843, 73.0382, 57.8369, 49.5408, 2.4386, 14.7606, 15.2482, 16.0292, 10.0572],
  [7.9709, 222.306, 5.1383, 7.4203, 5.3693, 6.7715, 228.4351, 4.796, 7.3862, 5.8384, 215.439, 6.4936, 7.8588, 8.4958, 3.3704, 7.5994, 0.2706, 0.3913, 166.4748, 699.5998, 47.6832, 14.8383, 119.6799, 68.2334, 8.0835, 119.996, 60.6432, 65.0397, 78.2237, 69.1201, 52.0704, 57.6583, 2.5739, 12.6664, 15.5433, 11.3207, 12.5228],
  [7.9247, 227.9117, 5.4565, 7.2049, 4.5518, 8.6741, 230.7102, 4.9122, 5.8468, 4.3528, 223.662, 3.5725, 10.3758, 5.1174, 6.7281, 3.992, 0.4649, 0.6686, 351.8985, 296.6615, 71.4455, 9.7682, 121.9932, 70.4144, 7.1028, 128.3385, 70.8774, 67.8405, 75.1784, 65.4579, 61.4009, 46.8844, 2.3623, 12.9222, 12.5908, 11.9385, 14.5192],
  [7.5353, 211.6637, 5.0893, 7.3311, 5.4905, 6.9134, 225.7857, 5.0512, 3.329, 7.6602, 210.6904, 3.5424, 10.4646, 6.9803, 3.7242, 6.1547, 0.5964, 0.3137, 294.3249, 646.4345, 47.043, 13.3502, 113.044, 72.7357, 6.3486, 116.7759, 54.2865, 67.252, 79.1587, 72.7497, 64.6283, 60.1784, 2.4078, 13.7183, 15.9618, 13.507, 11.3933],
  [8.197, 226.1773, 6.9098, 3.9926, 4.5899, 6.7829, 229.8776, 4.7756, 3.4409, 5.6743, 229.3918, 4.7288, 9.2096, 7.615, 3.7322, 6.4347, 0.6661, 0.3528, 275.9566, 519.7814, 47.0848, 13.2065, 128.71, 71.3682, 8.6414, 136.1494, 73.5367, 74.9446, 79.302, 70.9136, 55.7033, 67.0857, 2.257, 16.0966, 14.914, 13.5771, 9.1192],
  [8.1305, 229.6059, 5.0742, 3.5242, 4.8156, 7.4107, 226.2468, 5.0934, 7.3273, 4.3985, 226.3286, 3.9278, 11.3933, 4.8672, 6.4473, 7.2834, 0.5065, 0.6564, 183.8955, 621.8475, 52.9538, 9.6314, 137.4602, 71.1589, 8.3541, 131.6681, 70.7263, 71.7568, 66.2907, 73.8872, 59.9639, 47.1049, 2.2519, 17.2727, 14.4507, 12.6356, 13.0907],
  [7.6862, 229.1613, 3.0172, 5.3536, 5.3986, 7.0728, 230.0392, 4.8311, 6.4934, 4.2278, 223.4409, 4.3662, 8.5071, 8.014, 7.7454, 6.7976, 0.3013, 0.5436, 335.9359, 360.4184, 70.5576, 10.5338, 112.679, 71.2822, 7.0891, 113.9206, 60.9594, 71.2514, 74.2042, 72.8451, 52.7348, 58.5525, 2.2884, 15.7444, 13.1139, 15.1302, 13.8023],
  [8.3707, 221.5552, 5.2905, 6.7062, 4.8882, 7.8628, 231.8589, 4.7485, 5.3832, 7.7204, 215.6192, 6.0356, 5.4723, 4.8336, 4.6041, 3.5795, 0.7473, 0.4115, 127.7081, 646.2517, 57.5293, 14.0473, 127.3995, 70.9718, 6.5982, 121.7399, 53.3305, 48.1897, 66.351, 67.6574, 48.491, 72.4914, 2.4005, 17.4703, 13.2334, 10.65, 13.3813],
  [6.5655, 217.8535, 7.3944, 7.0984, 4.5161, 7.8841, 233.2415, 4.9568, 3.7265, 6.1972, 210.0927, 4.7459, 10.4017, 6.8013, 4.1302, 6.1961, 0.6053, 0.2716, 146.2565, 577.5175, 43.9292, 11.8983, 137.1828, 65.9468, 8.2589, 120.1966, 47.9091, 55.0335, 66.6414, 68.0838, 68.7161, 74.9257, 2.7431, 14.0077, 13.204, 10.6782, 9.2503],
]
def load_bool_from_json(file_path_start):
    try:
        with open(file_path_start, 'r') as f:
            data = json.load(f)  # 读取 JSON 数据
            return data.get("start_stop", False)  # 获取布尔变量的值
    except FileNotFoundError:
        print(f"File not found: {file_path_start}")
        return False
    except json.JSONDecodeError:
        print(f"Error reading JSON file: {file_path_start}")
        return False
def load_select_faults(file_path):
    try:
        # 打开并读取 JSON 文件
        with open(file_path, 'r') as json_file:
            select_faults = json.load(json_file)  # 加载文件内容为 Python 对象（列表或字典）
        return select_faults
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return []
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def health_mapping(md_values, alpha=0.5):
    """
    将马氏距离 (MD) 映射到 [0, 1]，健康程度与映射值负相关。
    趋近于 0 表示越健康，趋近于 1 表示越不健康。
    
    参数:
    - md_values: numpy 数组或单个数值，马氏距离 (MD) 的值。
    - alpha: 控制映射速率的参数，默认为 0.5。
    
    返回:
    - 映射到 [0, 1] 范围内的值。
    """
    return 0.5 * (1 - erf(alpha * md_values))

def health_mapping_exponential(md_values, beta=1.0):
    """
    指数映射，将马氏距离映射到 [0, 1]，健康程度与映射值负相关。
    """
    return 1 - np.exp(-beta * md_values)

def calculate_para_value(para_low, para_up, fault):
    # 生成一个 [0, 1) 区间的随机数
    random_number = random.random()
    # 将 para_low 和 para_up 转换为浮动类型
    para_low = float(para_low)
    para_up = float(para_up)
    # 根据公式计算 para_value
    para_value = para_low + 0.25 * (para_up - para_low) + random_number * 0.5 * (para_up - para_low) + (para_up - para_low) * fault
    return para_value
def update_para_values():
    # 每个参数项
    for index, param in enumerate(data["parameters"]):
        # 获取 para_low 和 para_up
        select_faults = load_select_faults(file_path_list)
        para_low = param["para_low"]
        para_up = param["para_up"]
        fault = 0
        start_stop = load_bool_from_json(file_path_start)
        if start_stop:
          if index in select_faults:
            fault = 1
          else:
            fault = 0
        else:
          pass
        # 生成新的 para_value
        new_para_value = calculate_para_value(para_low, para_up, fault)
        # 更新字典中的 para_value
        param["para_value"] = round(new_para_value, 4)  # 保留两位小数
        # 更新当前时间
        param["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    length=len(data["parameters"])
    Xt = [0] * length
    for index, param in enumerate(data["parameters"]):
      Xt[index] = param["para_value"]
    global X
    X.insert(0, Xt)
    if len(X) > max_length:
      X = X[:max_length]
    Xtm = np.array(X).astype(float)
    m = Xtm.shape[1]
    Tu = np.array(['10', '240', '10', '10', '6', '10', '240', '6', '10', '10', '240', '10', '15', '15', '10', '10', '1', '1', '500', '1000', '100', '20', '150', '80', '10', '150', '90', '90', '100', '80', '90', '90', '3', '20', '20', '20', '20'])
    Tl = np.array(['5',  '200', '0',  '0',  '4', '5',  '220', '4', '1',  '1',  '200', '1',  '1',  '0',  '1',  '1',  '0', '0', '0',   '0',    '0',   '5',  '100', '60', '5',  '100', '30', '30', '50',  '60', '30', '30', '2', '10', '10', '5',  '5'])
    Dtm = np.zeros((max_length, m), dtype=float)
    Ztm = np.zeros((max_length, m), dtype=float)
    Tu = Tu.astype(float)   
    Tl = Tl.astype(float) 
    for i in range(Xtm.shape[0]): 
        for j in range(Xtm.shape[1]): 
          Dtm[i,j] = max(0,Xtm[i,j]-Tu[j],Tl[j]-Xtm[i,j])/(Tu[j]-Tl[j])
          # Dtm[i,j] = max(0,Xtm[i,j]-Tu[j],Tl[j]-Xtm[i,j])
          Ztm[i,j] = abs(Xtm[i,j]-Tl[j])/(Tu[j]-Tl[j])
          # mean = np.mean(Xtm[:,j])
          # std_dev = np.std(Xtm[:,j])
          # if std_dev != 0:
          #   Ztm[i,j] = abs(Xtm[i,j] - mean)/std_dev
          # else:
          #   Ztm[i,j] = 0       
    # print(Dtm) 
    MD = np.zeros(m)
    s = np.zeros((max_length, max_length))
    for i in range(m):
      s = s + np.outer(Ztm[:, i], Ztm[:, i]) 
    s = s/(m-1)
    # s = np.cov(Ztm, rowvar=False)
    for i in range(m):
      d_column_transpose = Dtm[:, i].reshape(1, -1)
      MD[i] = (d_column_transpose @ s @ Dtm[:, i])/max_length
    # print(MD)
    # mapped_values = health_mapping(MD, alpha=0.5)
    # mapped_values_exp = health_mapping_exponential(erf(MD), beta=0.5)
    print(erf(MD))
    pararight_dict = {
    '氧化剂管路':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7142857142857143, 0.14285714285714285, 0.14285714285714285, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '燃料管路':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.14285714285714285, 0.7142857142857143, 0.0, 0.14285714285714285, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '氧化剂主阀':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.08333333333333333, 0.08333333333333333, 0.0, 0.0, 0.4166666666666667, 0.4166666666666667, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '燃料主阀':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.08333333333333333, 0.0, 0.08333333333333333, 0.0, 0.0, 0.0, 0.0, 0.4166666666666667, 0.4166666666666667, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '燃烧室':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625, 0.0625]),
    '推力室氧化剂喷嘴':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.125, 0.125, 0.125, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.625, 0.0]),
    '推力室燃料喷嘴':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.125, 0.125, 0.125, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.625]),
    '喷尾管':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6666666666666666, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '氧化剂涡轮泵':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.45454545454545453, 0.0909090909090909, 0.0, 0.0, 0.0, 0.0, 0.45454545454545453, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '燃料涡轮泵':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0909090909090909, 0.0, 0.45454545454545453, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.45454545454545453, 0.0, 0.0, 0.0, 0.0]),
    '燃气发生器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.07692307692307693, 0.0, 0.3846153846153846, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3846153846153846, 0.0, 0.0, 0.0, 0.0]),
    '太阳电池组':np.zeros(m),
    '太阳电池母线':np.array([0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.0, 0.0, 0.07692307692307693, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0]),
    '控制分流控制器':np.zeros(m),
    '模式控制单元':np.zeros(m),
    '电池管理单元':np.zeros(m),
    '电池充电调节器':np.array([0.2, 0.2, 0.0, 0.0, 0.0, 0.2, 0.2, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0]),
    '电流放电调节器':np.array([0.16666666666666666, 0.0, 0.0, 0.16666666666666666, 0.0, 0.16666666666666666, 0.0, 0.0, 0.16666666666666666, 0.0, 0.0, 0.16666666666666666, 0.0, 0.0, 0.16666666666666666, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0]),
    '电流供电母线':np.array([0.0, 0.0, 0.0, 0.25, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0]),
    '主母线':np.array([0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.07692307692307693, 0.0, 0.0, 0.07692307692307693, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,0.0]),
    '监测传感器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '固定电源模块':np.zeros(m),
    '电流传感器A':np.zeros(m),
    '电压传感器A':np.zeros(m),
    '信号变换器':np.zeros(m),
    '上行接收机':np.zeros(m),
    '测距信号调节器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '高稳定度振荡器':np.zeros(m),
    '接收机':np.zeros(m),
    '载波解调器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    'PCM信号处理器':np.zeros(m),
    '直接指令译码器':np.zeros(m),
    '热控涂层':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '热管':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '多层隔热组件':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '相变材料':np.zeros(m),
    '换热器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '工质流动驱动泵':np.zeros(m),
    '流量安全阀':np.zeros(m),
    '安全阀':np.zeros(m),
    '储液器':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    '测控应答机':np.zeros(m),
    'AOCS计算机':np.zeros(m),
    'TM/TC接口':np.zeros(m),
    '计算机':np.zeros(m),
    '接口电路':np.zeros(m),
    '远置单元A':np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    }
    result_dict = {}
    MD1 = np.array(erf(MD))
    for key, value in pararight_dict.items():
      if isinstance(value, np.ndarray) and value.shape == (37,):  # 确保 value 的形状为 37
          # 使用 np.dot 计算内积
          result = np.dot(value, MD1)
          result_dict[key] = 1-result
    # print(result_dict)
    result_value = np.array(list(result_dict.values()))
    # print(result_value)
    range_1_11 = result_value[0:11]
    range_12_22 = result_value[11:22]
    range_23_32 = result_value[22:32]
    range_33_41 = result_value[32:41]
    range_41_47 = result_value[41:47]
    comright_power = np.full(11, 1/11)
    comright_electric = np.full(11, 1/11)
    comright_measure = np.full(10, 1/10)
    comright_thermal = np.full(9, 1/9)
    comright_communicate = np.full(6, 1/6)
    comright_control = 1
    subvalue = [np.dot(range_1_11,comright_power),np.dot(range_12_22,comright_electric),np.dot(range_23_32,comright_measure),np.dot(range_33_41,comright_thermal),np.dot(range_41_47,comright_communicate),comright_control]
    print(subvalue)
    subright = [0.3,0.25,0.20,0.10,0.05,0.10]    #动力系统，电源系统，测控系统，热控系统，通信系统，控制系统
    all_value = np.dot(subvalue,subright)
    print(all_value)



if __name__ == "__main__":
    try:
        while True:
            update_para_values()
            time.sleep(1) 
    except KeyboardInterrupt:
        print("实时更新已停止。")

      

    