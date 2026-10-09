"""
Simulink 火箭仿真核心逻辑（无 GUI）。
由 simulate_main.SimThread 抽取，供 batch_generate 等脚本复用。
"""
import csv
import json
import math
import os

try:
    import matlab.engine
except (ImportError, OSError):  # MATLAB Engine is an optional runtime dependency.
    matlab = None

# 故障类型 -> Simulink Constant / Step 模块路径
FAULT_MAP = {
    "泵气蚀": "rocket_sim/动力系统模块/F1",
    "涡轮转速下降": "rocket_sim/动力系统模块/F2",
    "管路堵塞": "rocket_sim/动力系统模块/F3",
    "主阀门卡滞": "rocket_sim/动力系统模块/F4",
    "燃气泄漏": "rocket_sim/动力系统模块/F5",
    "燃烧不稳定": "rocket_sim/动力系统模块/F6",
    "喷管堵塞": "rocket_sim/动力系统模块/F7",
    "TVC偏角不足": "rocket_sim/TVC模块/F8",
    "RCS推力不足": "rocket_sim/姿态推进器/RCS/F10",
    "栅格舵偏角不足": "rocket_sim/栅格舵控制器/栅格舵/F9",
    "控制器无信号": "rocket_sim/栅格舵控制器/栅格舵/F11",
    "陀螺仪恒偏差": "rocket_sim/栅格舵控制器/栅格舵/F12",
    "陀螺仪卡死": "rocket_sim/栅格舵控制器/栅格舵/F13",
}

STEP1_MAP = {
    "泵气蚀": "rocket_sim/动力系统模块/液氧泵/F01/Step1",
    "涡轮转速下降": "rocket_sim/动力系统模块/氧涡轮/F01/Step1",
    "管路堵塞": "rocket_sim/动力系统模块/煤油管路/F01/Step1",
    "主阀门卡滞": "rocket_sim/动力系统模块/煤油主阀/F01/Step1",
    "燃气泄漏": "rocket_sim/动力系统模块/燃气发生器/F01/Step1",
    "燃烧不稳定": "rocket_sim/动力系统模块/燃烧室/F01/Step1",
    "喷管堵塞": "rocket_sim/动力系统模块/喷管/F01/Step1",
    "TVC偏角不足": "rocket_sim/TVC模块/F01/Step1",
    "RCS推力不足": "rocket_sim/姿态推进器/RCS/F01/Step1",
    "栅格舵偏角不足": "rocket_sim/栅格舵控制器/栅格舵/F01/Step1",
    "控制器无信号": "rocket_sim/栅格舵控制器/栅格舵/F02/Step1",
    "陀螺仪恒偏差": "rocket_sim/栅格舵控制器/栅格舵/F03/Step1",
    "陀螺仪卡死": "rocket_sim/栅格舵控制器/栅格舵/F04/Step1",
}

STEP2_MAP = {
    "泵气蚀": "rocket_sim/动力系统模块/液氧泵/F01/Step2",
    "涡轮转速下降": "rocket_sim/动力系统模块/氧涡轮/F01/Step2",
    "管路堵塞": "rocket_sim/动力系统模块/煤油管路/F01/Step2",
    "主阀门卡滞": "rocket_sim/动力系统模块/煤油主阀/F01/Step2",
    "燃气泄漏": "rocket_sim/动力系统模块/燃气发生器/F01/Step2",
    "燃烧不稳定": "rocket_sim/动力系统模块/燃烧室/F01/Step2",
    "喷管堵塞": "rocket_sim/动力系统模块/喷管/F01/Step2",
    "TVC偏角不足": "rocket_sim/TVC模块/F01/Step2",
    "RCS推力不足": "rocket_sim/姿态推进器/RCS/F01/Step2",
    "栅格舵偏角不足": "rocket_sim/栅格舵控制器/栅格舵/F01/Step2",
    "控制器无信号": "rocket_sim/栅格舵控制器/栅格舵/F02/Step2",
    "陀螺仪恒偏差": "rocket_sim/栅格舵控制器/栅格舵/F03/Step2",
    "陀螺仪卡死": "rocket_sim/栅格舵控制器/栅格舵/F04/Step2",
}

POWER_FAULTS = [
    "无故障", "泵气蚀", "涡轮转速下降", "管路堵塞",
    "主阀门卡滞", "燃气泄漏", "燃烧不稳定", "喷管堵塞",
]
CONTROL_FAULTS = [
    "无故障", "TVC偏角不足", "RCS推力不足", "栅格舵偏角不足",
    "控制器无信号", "陀螺仪恒偏差", "陀螺仪卡死",
]

SCOPE_CSV_HEADER = [
    "Time", "X", "Y", "H", "Vx", "Vy", "Vz", "FT", "Roll", "Pitch", "Yaw",
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
    "S10_X", "S10_Y", "S10_Z",
    "S11", "S12", "S13", "S14", "S15", "S16", "S17",
    "FaultFlag",
]

P_CSV_HEADER = [
    "Time",
    "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9",
    "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17",
    "FaultFlag",
]


def clear_all_faults_and_steps(eng, fault_map=None, step1_map=None, step2_map=None):
    fault_map = fault_map or FAULT_MAP
    step1_map = step1_map or STEP1_MAP
    step2_map = step2_map or STEP2_MAP
    for block in fault_map.values():
        eng.set_param(block, "Value", "1", nargout=0)
    for block in list(step1_map.values()) + list(step2_map.values()):
        eng.set_param(block, "Time", "1e9", nargout=0)
        eng.set_param(block, "Before", "0", nargout=0)
        eng.set_param(block, "After", "0", nargout=0)


def _fault_flag(power_fault, control_fault, start_time, end_time, t):
    if (power_fault != "无故障" or control_fault != "无故障") and (
        start_time <= t <= end_time
    ):
        return 1
    return 0


def _inject_fault(eng, fault_name, start_time, end_time):
    if fault_name == "无故障":
        return
    eng.set_param(FAULT_MAP[fault_name], "Value", "0", nargout=0)
    step1 = STEP1_MAP[fault_name]
    step2 = STEP2_MAP[fault_name]
    for step, t in ((step1, start_time), (step2, end_time)):
        eng.set_param(step, "Time", str(t), nargout=0)
        eng.set_param(step, "Before", "0", nargout=0)
        eng.set_param(step, "After", "1", nargout=0)


def _extract_signal_lists(sim_out, eng):
    xe_data = eng.getfield(sim_out, "Xe")
    ve_data = eng.getfield(sim_out, "Ve")
    FT_data = eng.getfield(sim_out, "FT")
    angle = eng.getfield(sim_out, "Angle")
    s_signals = [eng.getfield(sim_out, f"S{i}") for i in range(1, 18)]
    p_signals = [eng.getfield(sim_out, f"P{i}") for i in range(1, 18)]

    time_vals = xe_data["time"]
    time_list = [t[0] for t in time_vals]
    # zip() would otherwise silently truncate signals with different sample grids.
    for sig in [ve_data, FT_data, angle, *s_signals, *p_signals]:
        if [t[0] for t in sig["time"]] != time_list:
            raise ValueError("仿真输出信号的时间轴不一致，无法导出同步 CSV")
    data_list = list(map(list, xe_data["signals"]["values"]))
    ve_list = list(map(list, ve_data["signals"]["values"]))
    FT_list = [f[0] for f in FT_data["signals"]["values"]]
    angle_list = list(map(list, angle["signals"]["values"]))

    s_lists = []
    for sig, idx in zip(s_signals, range(1, 18)):
        vals = sig["signals"]["values"]
        if idx == 10:
            s_lists.append(list(map(list, vals)))
        else:
            s_lists.append([s[0] for s in vals])

    p_lists = [[p[0] for p in sig["signals"]["values"]] for sig in p_signals]
    return time_list, data_list, ve_list, FT_list, angle_list, s_lists, p_lists


def write_csv_outputs(
    csv_output_path,
    time_list,
    data_list,
    ve_list,
    FT_list,
    angle_list,
    s_lists,
    p_lists,
    power_fault,
    control_fault,
    start_time,
    end_time,
    write_p_values=True,
):
    signals = [data_list, ve_list, FT_list, angle_list, *s_lists, *p_lists]
    if not time_list or any(len(values) != len(time_list) for values in signals):
        raise ValueError("仿真输出为空或信号采样长度不一致")
    os.makedirs(os.path.dirname(csv_output_path) or ".", exist_ok=True)
    (
        S1_list, S2_list, S3_list, S4_list, S5_list, S6_list, S7_list,
        S8_list, S9_list, S10_list, S11_list, S12_list, S13_list,
        S14_list, S15_list, S16_list, S17_list,
    ) = s_lists
    P1_list, P2_list, P3_list, P4_list, P5_list, P6_list, P7_list = p_lists[:7]
    P8_list, P9_list, P10_list, P11_list, P12_list, P13_list, P14_list = p_lists[7:14]
    P15_list, P16_list, P17_list = p_lists[14:]

    with open(csv_output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SCOPE_CSV_HEADER)
        for t, (x, y, z), (vx, vy, vz), ft, (roll, pitch, yaw), s1, s2, s3, s4, s5, s6, s7, s8, s9, (
            s10x, s10y, s10z
        ), s11, s12, s13, s14, s15, s16, s17 in zip(
            time_list, data_list, ve_list, FT_list, angle_list,
            S1_list, S2_list, S3_list, S4_list, S5_list, S6_list, S7_list,
            S8_list, S9_list, S10_list, S11_list, S12_list, S13_list,
            S14_list, S15_list, S16_list, S17_list,
        ):
            flag = _fault_flag(power_fault, control_fault, start_time, end_time, t)
            writer.writerow([
                t, x, y, -z, vx, vy, vz, ft, roll, pitch, yaw,
                s1, s2, s3, s4, s5, s6, s7, s8, s9,
                s10x, s10y, s10z, s11, s12, s13, s14, s15, s16, s17, flag,
            ])

    p_csv_path = None
    if write_p_values:
        p_csv_path = os.path.join(os.path.dirname(csv_output_path), "P_values.csv")
        with open(p_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(P_CSV_HEADER)
            for t, *p_vals in zip(time_list, *p_lists):
                flag = _fault_flag(power_fault, control_fault, start_time, end_time, t)
                writer.writerow([t, *p_vals, flag])

    return csv_output_path, p_csv_path


def write_flight_count_json(flight_count, json_path):
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"flight_count": flight_count}, f, ensure_ascii=False, indent=4)


def load_model(eng, model_path):
    model_dir = os.path.dirname(model_path)
    if model_dir:
        eng.cd(model_dir, nargout=0)
    model_name = os.path.splitext(os.path.basename(model_path))[0]
    try:
        eng.load_system(model_name, nargout=0)
    except Exception:
        eng.load_system(model_path, nargout=0)
    return model_name


def run_simulation(
    model_path,
    csv_output_path,
    power_fault="无故障",
    control_fault="无故障",
    flight_count=0,
    start_time=0,
    end_time=480,
    eng=None,
    flight_count_json_path=None,
    write_p_values=True,
    close_engine=False,
    on_stage=None,
    allow_newer_model=False,
):
    """
    执行单次仿真并写入 CSV。

    返回: (csv_output_path, p_csv_path_or_none, eng)
    eng 可传入已有引擎以加速批量仿真；close_engine=True 时在结束后 quit。
    """
    if power_fault not in POWER_FAULTS or control_fault not in CONTROL_FAULTS:
        raise ValueError("故障名称与 Simulink 故障映射不匹配")
    if not all(math.isfinite(float(t)) for t in (start_time, end_time)) or not 0 <= start_time < end_time <= 480:
        raise ValueError("时间必须满足 0 <= 注入时刻 < 恢复时刻 <= 480 秒")
    if isinstance(flight_count, bool) or int(flight_count) != flight_count or not 0 <= flight_count <= 20:
        raise ValueError("飞行次数必须为 0 到 20 的整数")
    if os.path.splitext(os.path.basename(model_path))[0] != "rocket_sim":
        raise ValueError("故障块路径要求模型名为 rocket_sim")
    notify = on_stage or (lambda stage: None)
    notify("starting_engine")
    own_engine = eng is None
    if own_engine:
        if matlab is None:
            raise RuntimeError("未安装 MATLAB Engine for Python；请在 MATLAB 对应 Python 环境安装 matlabengineforpython")
        eng = matlab.engine.start_matlab("-nodesktop -nosplash")

    version_setting = None
    try:
        notify("configuring")
        if allow_newer_model:
            version_setting = eng.get_param(0.0, "ErrorIfLoadNewModel")
            eng.set_param(0.0, "ErrorIfLoadNewModel", "off", nargout=0)
        model_name = load_model(eng, model_path)
        clear_all_faults_and_steps(eng)
        _inject_fault(eng, power_fault, start_time, end_time)
        _inject_fault(eng, control_fault, start_time, end_time)

        run_time = flight_count * 480
        eng.set_param("rocket_sim/Th", "Value", str(run_time), nargout=0)
        eng.set_param(model_name, "StopTime", "480", nargout=0)

        if flight_count_json_path:
            write_flight_count_json(flight_count, flight_count_json_path)

        notify("solving")
        sim_out = eng.sim(model_name, nargout=1)
        notify("exporting")
        extracted = _extract_signal_lists(sim_out, eng)
        paths = write_csv_outputs(
            csv_output_path,
            *extracted,
            power_fault=power_fault,
            control_fault=control_fault,
            start_time=start_time,
            end_time=end_time,
            write_p_values=write_p_values,
        )
        return (*paths, eng)
    finally:
        if version_setting is not None:
            try:
                eng.set_param(0.0, "ErrorIfLoadNewModel", version_setting, nargout=0)
            except Exception:
                pass
        if close_engine and eng is not None:
            try:
                eng.quit()
            except Exception:
                pass
