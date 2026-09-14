"""姿控（GNC）残差特征 v1/v2：在降采样后的 DataFrame 上按行计算。"""

from typing import List

import numpy as np
import pandas as pd

# v1（保留对照）
GNC_RESIDUAL_COLUMNS_V1: List[str] = [
    "err_roll",
    "err_pitch",
    "err_yaw",
    "fin_diff",
    "att_rate_roll",
    "att_rate_pitch",
    "att_rate_yaw",
    "att_rate_mag",
    "cmd_roll_std",
    "cmd_pitch_std",
    "cmd_yaw_std",
    "tvc_cmd_mag",
    "gyro_s16",
    "gyro_s17",
    "Roll",
    "Pitch",
    "Yaw",
    "S10_X",
    "S10_Y",
]

# v2：修正 S13 语义、作动器/陀螺区分增强
GNC_RESIDUAL_COLUMNS: List[str] = [
    "err_roll",
    "err_pitch",
    "err_pitch_s13",
    "fin_diff",
    "fin_s14_rate",
    "fin_s15_rate",
    "fin_couple_pitch",
    "att_rate_roll",
    "att_rate_pitch",
    "att_rate_yaw",
    "att_rate_mag",
    "gyro_rate_err_roll",
    "gyro_rate_err_pitch",
    "gyro_s17",
    "cmd_roll_std",
    "cmd_pitch_std",
    "cmd_frozen",
    "tvc_cmd_mag",
    "tvc_cmd_rate",
    "dS10_X",
    "dS10_Y",
]

# v2.1：v2 + RCS / 执行器活跃度（Phase 3b-2a）
GNC_RESIDUAL_COLUMNS_V21: List[str] = GNC_RESIDUAL_COLUMNS + [
    "rcs_cmd",
    "rcs_cmd_rate",
    "rcs_activity",
    "fin_activity",
    "actuator_dominance_rcs",
    "actuator_dominance_fin",
]

GNC_FEATURE_PHYSICS = {
    "err_roll": "Roll tracking error (S11 - Roll)",
    "err_pitch": "Pitch tracking error (S12 - Pitch)",
    "err_pitch_s13": "Pitch cmd path residual (S13 - Pitch); S13≈Pitch in data",
    "fin_diff": "Grid-fin differential (S14 - S15)",
    "fin_s14_rate": "d(S14)/dt",
    "fin_s15_rate": "d(S15)/dt",
    "fin_couple_pitch": "Pitch error × fin_diff (grid-fin coupling)",
    "att_rate_roll": "d(Roll)/dt",
    "att_rate_pitch": "d(Pitch)/dt",
    "att_rate_yaw": "d(Yaw)/dt",
    "att_rate_mag": "Angular-rate magnitude",
    "gyro_rate_err_roll": "d(Roll)/dt - d(S17)/dt",
    "gyro_rate_err_pitch": "d(Pitch)/dt - d(S17)/dt",
    "gyro_s17": "Gyro channel S17",
    "cmd_roll_std": "Rolling std of S11 (~2s)",
    "cmd_pitch_std": "Rolling std of S12 (~2s)",
    "cmd_frozen": "Frozen-command cue: 1/(1+cmd_roll_std+cmd_pitch_std)",
    "tvc_cmd_mag": "|S10| magnitude",
    "tvc_cmd_rate": "d|S10|/dt",
    "dS10_X": "d(S10_X)/dt",
    "dS10_Y": "d(S10_Y)/dt",
    "rcs_cmd": "RCS command proxy (S10_Y)",
    "rcs_cmd_rate": "d(S10_Y)/dt",
    "rcs_activity": "Rolling std of S10_Y (~2s)",
    "fin_activity": "Rolling std S14 + S15",
    "actuator_dominance_rcs": "RCS activity share among actuators",
    "actuator_dominance_fin": "Grid-fin activity share among actuators",
}


def _rolling_std(series: pd.Series, sample_dt: float, sec: float = 2.0) -> pd.Series:
    win = max(4, int(round(sec / sample_dt)))
    return series.rolling(win, min_periods=4).std().bfill().ffill().fillna(0.0)


def _grad1d(values: np.ndarray, dt: float) -> np.ndarray:
    return np.gradient(values.astype(np.float64), dt)


def build_gnc_residual_features(df: pd.DataFrame, sample_dt: float = 0.125) -> pd.DataFrame:
    """v2 残差特征（默认入口）。"""
    return build_gnc_residual_features_v2(df, sample_dt=sample_dt)


def build_gnc_residual_features_v1(df: pd.DataFrame, sample_dt: float = 0.125) -> pd.DataFrame:
    dt = float(sample_dt)
    out = pd.DataFrame(index=df.index)

    out["err_roll"] = df["S11"] - df["Roll"]
    out["err_pitch"] = df["S12"] - df["Pitch"]
    out["err_yaw"] = df["S13"] - df["Yaw"]
    out["fin_diff"] = df["S14"] - df["S15"]

    roll_r = _grad1d(df["Roll"].values, dt)
    pitch_r = _grad1d(df["Pitch"].values, dt)
    yaw_r = _grad1d(df["Yaw"].values, dt)
    out["att_rate_roll"] = roll_r
    out["att_rate_pitch"] = pitch_r
    out["att_rate_yaw"] = yaw_r
    out["att_rate_mag"] = np.sqrt(roll_r ** 2 + pitch_r ** 2 + yaw_r ** 2)

    for src, dst in [("S11", "cmd_roll_std"), ("S12", "cmd_pitch_std"), ("S13", "cmd_yaw_std")]:
        out[dst] = _rolling_std(df[src], dt)

    out["tvc_cmd_mag"] = np.sqrt(
        df["S10_X"].values ** 2 + df["S10_Y"].values ** 2 + df["S10_Z"].values ** 2
    )
    out["gyro_s16"] = df["S16"]
    out["gyro_s17"] = df["S17"]
    out["Roll"] = df["Roll"]
    out["Pitch"] = df["Pitch"]
    out["Yaw"] = df["Yaw"]
    out["S10_X"] = df["S10_X"]
    out["S10_Y"] = df["S10_Y"]

    return out[GNC_RESIDUAL_COLUMNS_V1].astype(np.float32)


def build_gnc_residual_features_v2(df: pd.DataFrame, sample_dt: float = 0.125) -> pd.DataFrame:
    dt = float(sample_dt)
    out = pd.DataFrame(index=df.index)

    err_roll = df["S11"] - df["Roll"]
    err_pitch = df["S12"] - df["Pitch"]
    err_pitch_s13 = df["S13"] - df["Pitch"]
    fin_diff = df["S14"] - df["S15"]

    out["err_roll"] = err_roll
    out["err_pitch"] = err_pitch
    out["err_pitch_s13"] = err_pitch_s13
    out["fin_diff"] = fin_diff
    out["fin_s14_rate"] = _grad1d(df["S14"].values, dt)
    out["fin_s15_rate"] = _grad1d(df["S15"].values, dt)
    out["fin_couple_pitch"] = err_pitch * fin_diff / 180.0

    roll_r = _grad1d(df["Roll"].values, dt)
    pitch_r = _grad1d(df["Pitch"].values, dt)
    yaw_r = _grad1d(df["Yaw"].values, dt)
    s17_r = _grad1d(df["S17"].values, dt)

    out["att_rate_roll"] = roll_r
    out["att_rate_pitch"] = pitch_r
    out["att_rate_yaw"] = yaw_r
    out["att_rate_mag"] = np.sqrt(roll_r ** 2 + pitch_r ** 2 + yaw_r ** 2)
    out["gyro_rate_err_roll"] = roll_r - s17_r
    out["gyro_rate_err_pitch"] = pitch_r - s17_r
    out["gyro_s17"] = df["S17"]

    cmd_roll_std = _rolling_std(df["S11"], dt)
    cmd_pitch_std = _rolling_std(df["S12"], dt)
    out["cmd_roll_std"] = cmd_roll_std
    out["cmd_pitch_std"] = cmd_pitch_std
    out["cmd_frozen"] = 1.0 / (1.0 + cmd_roll_std + cmd_pitch_std)

    tvc_mag = np.sqrt(
        df["S10_X"].values ** 2 + df["S10_Y"].values ** 2 + df["S10_Z"].values ** 2
    )
    out["tvc_cmd_mag"] = tvc_mag
    out["tvc_cmd_rate"] = _grad1d(tvc_mag, dt)
    out["dS10_X"] = _grad1d(df["S10_X"].values, dt)
    out["dS10_Y"] = _grad1d(df["S10_Y"].values, dt)

    return out[GNC_RESIDUAL_COLUMNS].astype(np.float32)


def build_gnc_residual_features_v21(df: pd.DataFrame, sample_dt: float = 0.125) -> pd.DataFrame:
    """v2.1 = v2 + RCS / 执行器活跃度特征。"""
    out = build_gnc_residual_features_v2(df, sample_dt=sample_dt)
    dt = float(sample_dt)

    rcs_cmd = df["S10_Y"].astype(np.float64)
    rcs_cmd_rate = _grad1d(rcs_cmd.values, dt)
    rcs_activity = _rolling_std(rcs_cmd, dt)
    fin_activity = _rolling_std(df["S14"], dt) + _rolling_std(df["S15"], dt)

    tvc_mag = out["tvc_cmd_mag"].values.astype(np.float64)
    denom = rcs_activity.values + tvc_mag + fin_activity.values + 1e-6

    out["rcs_cmd"] = rcs_cmd.values.astype(np.float32)
    out["rcs_cmd_rate"] = rcs_cmd_rate.astype(np.float32)
    out["rcs_activity"] = rcs_activity.values.astype(np.float32)
    out["fin_activity"] = fin_activity.values.astype(np.float32)
    out["actuator_dominance_rcs"] = (rcs_activity.values / denom).astype(np.float32)
    out["actuator_dominance_fin"] = (fin_activity.values / denom).astype(np.float32)

    return out[GNC_RESIDUAL_COLUMNS_V21].astype(np.float32)
