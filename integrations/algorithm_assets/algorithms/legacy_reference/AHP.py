import numpy as np

def assign_values_to_vector(length, values, positions):
    vector = np.zeros(length)
    for value, pos in zip(values, positions):
        vector[pos] = value
    return vector

# 步骤 1: 构建判断矩阵
# 假设有 3 个准则：C1, C2, C3，下面的矩阵表示准则之间的相对重要性
# 例如，C1 比 C2 重要（3），C1 比 C3 重要（1/5），依此类推。
# 矩阵中的每个元素为两两准则的比较结果
# 如果 C1 对 C2 的重要性是 3，则 C2 对 C1 的重要性为 1/3
# 1：两个标准同等重要。
# 3：一个标准比另一个标准稍微重要。
# 5：一个标准比另一个标准明显重要。
# 7：一个标准比另一个标准极为重要。
# 9：一个标准比另一个标准绝对重要。
# 2、4、6、8：表示介于上述两者之间的程度。

# 判断矩阵
matrix = np.array([
    [1,1,5,5,5],   # C1 对 C1, C1 对 C2, C1 对 C3
    [1,1,5,5,5], # C2 对 C1, C2 对 C2, C2 对 C3
    [1/5,1/5,1,1,1],  # C3 对 C1, C3 对 C2, C3 对 C3
    [1/5,1/5,1,1,1],
    [1/5,1/5,1,1,1],
])

# 步骤 2: 归一化判断矩阵
# 每一列的元素除以该列的总和
column_sums = matrix.sum(axis=0)  # 按列求和
normalized_matrix = matrix / column_sums  # 归一化矩阵

# 步骤 3: 计算特征向量（每行求平均值）
weights = normalized_matrix.mean(axis=1)  # 每行求平均值，即为权重向量

# 步骤 4: 一致性检验
# 1. 计算最大特征值 λ_max
# 计算特征向量与判断矩阵的乘积，得到估计的权重向量
lambda_max = np.mean(np.dot(matrix, weights) / weights)

# 2. 计算一致性指标 CI
n = matrix.shape[0]
CI = (lambda_max - n) / (n - 1)

# 3. 计算一致性比例 CR
# 随机一致性指标 RI 参考下表（假设 n=3）
RI = 0.58  # 对于 3x3 矩阵，RI = 0.58
CR = CI / RI

# 输出结果
print("判断矩阵：\n", matrix)
print("\n归一化矩阵：\n", normalized_matrix)
print("\n权重向量：", weights)
print("\n最大特征值 λ_max:", lambda_max)
print("一致性指标 CI:", CI)
print("一致性比例 CR:", CR)

if CR < 0.1:
    print("\n一致性检验通过，结果可信")
    weights = np.full(4,1/4)
    positions = [4,5,12,15]
    vector = assign_values_to_vector(37, weights, positions)
    vector_str = ', '.join(map(str, vector))
    print(vector_str)
else:
    print("\n一致性检验未通过，需要调整判断矩阵")


