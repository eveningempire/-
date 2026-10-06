import numpy as np
import time
def teams_rt_fault_rows(D, T):
    """
    TEAMS-RT算法(行=故障模式,列=测试)

    参数:
    - D: 二维列表或numpy数组,形状为 (num_faults, num_tests)
    - T: 列表或numpy数组,长度 = num_tests,0=pass,1=fail

    返回:
    - 一个字典,包含 Good, Bad, Suspected, Unknown 四个集合(故障索引)
    """
    D = np.array(D)
    T = np.array(T)
    num_faults, num_tests = D.shape  # ✅ 注意:这里行=故障,列=测试

    fault_indices = set(range(num_faults))
    Good = set()
    Bad = set()
    Suspected = set()
    Unknown = set(fault_indices)

    # (2) 遍历通过的测试
    for t_idx in range(num_tests):
        if T[t_idx] == 0:  # 通过的测试
            related_faults = np.where(D[:, t_idx] == 1)[0]  # 该测试关联的所有故障
            for f in related_faults:
                if f in Unknown:
                    Unknown.remove(f)
                    Good.add(f)

    # (3) 失败测试中唯一关联故障 → Bad
    bad_candidates = set()
    for t_idx in range(num_tests):
        if T[t_idx] == 1:
            related_faults = [f for f in np.where(D[:, t_idx] == 1)[0] if f in Unknown]
            if len(related_faults) == 1:
                bad_candidates.add(related_faults[0])

    for f in bad_candidates:
        if f in Unknown:
            Unknown.remove(f)
            Bad.add(f)

    # (4) 失败测试中多个关联故障 → Suspected
    for t_idx in range(num_tests):
        if T[t_idx] == 1:
            related_faults = [f for f in np.where(D[:, t_idx] == 1)[0] if f in Unknown]
            for f in related_faults:
                Unknown.remove(f)
                Suspected.add(f)

    return {
        "Good": [int(item)+1 for item in Good],
        "Bad": [int(item)+1 for item in Bad],
        "Suspected": [int(item)+1 for item in Suspected],
        "Unknown": [int(item)+1 for item in Unknown]
    }

def teams_rt_v2(D, T):
    D = np.array(D)
    T = np.array(T)
    num_faults, num_tests = D.shape

    # (1)初始化
    Unknown = set(range(num_faults))
    Good = set()
    Bad = set()
    Suspected = set()

    # 失败测试集合(列的索引)
    failed_tests = set(np.where(T == 1)[0])

    # (2)处理失败测试
    for t in failed_tests:
        # 找到与该失败测试相关的故障(该列中为1的行索引)
        related_faults = set(np.where(D[:, t] == 1)[0])
        related_unknown_faults = related_faults & Unknown

        if len(related_unknown_faults) == 1:
            # 唯一故障,标记为Bad
            f = list(related_unknown_faults)[0]
            Bad.add(f)
            Unknown.remove(f)
        elif len(related_unknown_faults) > 1:
            # 非唯一,将它们移到Suspected
            for f in related_unknown_faults:
                Suspected.add(f)
                Unknown.discard(f)

    # Unknown 剩下的都认为是 Good
    Good.update(Unknown)
    Unknown.clear()

    # (3)扩充失败测试集合
    FT_ext = set()
    for f in list(Suspected):
        # 该故障关联的测试
        related_tests = set(np.where(D[f, :] == 1)[0])
        not_failed_tests = related_tests - failed_tests

        if len(not_failed_tests) == 1:
            # 满足条件,将该故障选中
            # 扩充 FT 集合:Suspected fault 和 Bad faults 的所有关联测试
            faults_to_extend = {f} | Bad
            for ff in faults_to_extend:
                FT_ext.update(set(np.where(D[ff, :] == 1)[0]))

    failed_tests = failed_tests | FT_ext  # FT ∪ FT_ext

    # (4)更新 Suspected 集合
    for f in list(Suspected):
        related_tests = set(np.where(D[f, :] == 1)[0])
        # 如果某故障的关联测试不能被扩充后的失败测试集合覆盖 → 移到 Good
        if not related_tests.issubset(failed_tests):
            Good.add(f)
            Suspected.remove(f)

    return {
        "Good": [int(item)+1 for item in Good],
        "Bad": [int(item)+1 for item in Bad],
        "Suspected": [int(item)+1 for item in Suspected],
        "Unknown": [int(item)+1 for item in Unknown]
    }


if __name__ == "__main__":
    D = [ 
        [1,0,0,0], 
        [1,1,0,0], 
        [0,1,0,0], 
        [0,1,1,0], 
        [0,0,1,0], 
        [0,0,1,0], 
        [0,0,0,1], 
        [0,0,1,0], 
    ]
    T = [1,0,0,0]  # 所有测试都通过

    D = np.array(D)
    num_faults, num_tests = D.shape


    start_time = time.time()  # 记录开始时间
    result = teams_rt_v2(D, T)
    end_time = time.time()    # 记录结束时间
    # 计算并打印耗时(秒)
    execution_time = end_time - start_time
    print(f"算法执行时间: {execution_time:.6f} 秒")


    print("TEAMS-RT 结果:")
    for k, v in result.items():
        print(f"{k}: {v}")

