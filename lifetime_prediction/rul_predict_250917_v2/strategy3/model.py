import numpy as np


class SOM:
    def __init__(self, grid_size=(5, 5), input_dim=8, learning_rate=0.5, sigma=1.0, random_state=None):
        """
        自组织映射网络（Self-Organizing Map）

        参数:
        - grid_size: 网格大小，指定SOM神经元的排列形状，例如(5,5)表示5×5=25个神经元
        - input_dim: 输入特征维度
        - learning_rate: 学习率
        - sigma: 高斯邻域函数的初始宽度
        - random_state: 随机数种子，用于初始化
        """
        self.grid_size = grid_size
        self.input_dim = input_dim
        self.learning_rate_init = learning_rate
        self.sigma_init = sigma
        self.random_state = random_state

        # 初始化权重矩阵，每个神经元对应一个输入维度的权重向量
        np.random.seed(random_state)
        self.weights = np.random.rand(grid_size[0], grid_size[1], input_dim)

        # 神经元位置矩阵
        self.neuron_positions = np.array([[(i, j) for j in range(grid_size[1])] for i in range(grid_size[0])])

        # 记录每个神经元的激活次数和相关样本
        self.neuron_activations = np.zeros(grid_size)
        self.samples_per_neuron = [[] for _ in range(grid_size[0] * grid_size[1])]
        self.max_mahalanobis_dist = None  # 正常样本的最大马氏距离
        self.neuron_cov_matrices = []  # 每个神经元的协方差矩阵

    def _find_bmu(self, x):
        """查找最佳匹配单元(Best Matching Unit)"""
        # 计算输入样本与每个神经元权重的欧氏距离
        distances = np.sum((self.weights - x) ** 2, axis=2)
        # 找到距离最小的神经元位置
        bmu_idx = np.unravel_index(np.argmin(distances), distances.shape)
        return bmu_idx

    def _update_weights(self, x, bmu_idx, iteration, max_iterations):
        """更新权重"""
        # 计算当前迭代的学习率和邻域半径
        t = iteration / max_iterations
        learning_rate = self.learning_rate_init * np.exp(-t)
        sigma = self.sigma_init * np.exp(-t)

        # 计算每个神经元与BMU的距离
        bmu_position = np.array(bmu_idx)
        positions = self.neuron_positions
        distances = np.sum((positions - bmu_position.reshape(1, 1, 2)) ** 2, axis=2)

        # 计算邻域函数（高斯函数）
        neighborhood = np.exp(-distances / (2 * sigma**2))

        # 更新权重
        delta = (
            learning_rate * neighborhood.reshape(self.grid_size[0], self.grid_size[1], 1) * (x - self.weights)
        )
        self.weights += delta

    def fit(self, X, iterations=1000):
        """训练SOM模型"""
        for i in range(iterations):
            if i % 100 == 0:
                print(f"SOM训练迭代: {i}/{iterations}")
            # 从训练数据随机选择一个样本
            sample_idx = np.random.randint(0, X.shape[0])
            x = X[sample_idx]

            # 查找BMU
            bmu_idx = self._find_bmu(x)

            # 更新权重
            self._update_weights(x, bmu_idx, i, iterations)

        # 记录每个神经元的激活情况
        for i in range(X.shape[0]):
            x = X[i]
            bmu_idx = self._find_bmu(x)
            self.neuron_activations[bmu_idx] += 1
            # 保存样本到对应神经元
            flat_idx = bmu_idx[0] * self.grid_size[1] + bmu_idx[1]
            self.samples_per_neuron[flat_idx].append(i)

        # 为每个神经元计算协方差矩阵(用于马氏距离计算)
        self._compute_covariance_matrices(X)

        # 计算所有正常样本的马氏距离，并确定最大值作为阈值
        all_mahalanobis_distances = []
        for i in range(X.shape[0]):
            x = X[i]
            mahalanobis_dist = self._compute_min_mahalanobis_distance(x)
            all_mahalanobis_distances.append(mahalanobis_dist)

        self.max_mahalanobis_dist = np.max(all_mahalanobis_distances)
        return self

    def _compute_covariance_matrices(self, X):
        """为每个神经元计算协方差矩阵"""
        self.neuron_cov_matrices = []
        for neuron_idx in range(len(self.samples_per_neuron)):
            samples_idx = self.samples_per_neuron[neuron_idx]
            # 如果神经元没有样本，使用单位矩阵
            if len(samples_idx) <= 1:
                cov_matrix = np.eye(self.input_dim)
            else:
                samples = X[samples_idx]
                # 计算协方差矩阵
                cov_matrix = np.cov(samples, rowvar=False)
                # 确保协方差矩阵可逆，必要时添加小的对角线值
                if np.linalg.matrix_rank(cov_matrix) < self.input_dim:
                    cov_matrix += np.eye(self.input_dim) * 1e-6
            self.neuron_cov_matrices.append(cov_matrix)

    def _compute_mahalanobis_distance(self, x, neuron_idx):
        """计算样本x到指定神经元的马氏距离"""
        neuron_pos = (neuron_idx // self.grid_size[1], neuron_idx % self.grid_size[1])
        neuron_weight = self.weights[neuron_pos]

        cov_matrix = self.neuron_cov_matrices[neuron_idx]
        try:
            inv_cov = np.linalg.inv(cov_matrix)
            diff = x - neuron_weight
            mahalanobis_squared = np.dot(np.dot(diff, inv_cov), diff.T)
            return np.sqrt(mahalanobis_squared)
        except np.linalg.LinAlgError:
            # 如果协方差矩阵不可逆，返回欧氏距离
            return np.linalg.norm(x - neuron_weight)

    def _compute_min_mahalanobis_distance(self, x):
        """计算样本x到所有神经元的最小马氏距离"""
        min_dist = float("inf")
        for neuron_idx in range(len(self.samples_per_neuron)):
            if len(self.samples_per_neuron[neuron_idx]) > 0:  # 只考虑有样本的神经元
                dist = self._compute_mahalanobis_distance(x, neuron_idx)
                min_dist = min(min_dist, dist)
        return min_dist

    def _compute_weighted_mahalanobis_distance(self, x):
        """计算样本x到所有神经元的加权马氏距离
        权重为：正常样本在该聚类的占比
        """
        total_samples = sum(len(samples) for samples in self.samples_per_neuron)
        if total_samples == 0:
            return float("inf")

        weighted_dist = 0
        for neuron_idx in range(len(self.samples_per_neuron)):
            samples_count = len(self.samples_per_neuron[neuron_idx])
            if samples_count > 0:  # 只考虑有样本的神经元
                weight = samples_count / total_samples
                dist = self._compute_mahalanobis_distance(x, neuron_idx)
                weighted_dist += weight * dist

        return weighted_dist

    def predict_anomaly(self, X):
        """预测样本是否异常
        返回:
        - anomaly_flags: 异常标记，True表示异常
        - min_distances: 每个样本到最近聚类中心的马氏距离
        """
        anomaly_flags = np.zeros(X.shape[0], dtype=bool)
        min_distances = np.zeros(X.shape[0])

        for i in range(X.shape[0]):
            min_dist = self._compute_min_mahalanobis_distance(X[i])
            min_distances[i] = min_dist
            # 如果最小马氏距离大于正常样本的最大马氏距离，判定为异常
            if self.max_mahalanobis_dist is not None and min_dist > self.max_mahalanobis_dist:
                anomaly_flags[i] = True

        return anomaly_flags, min_distances

    def compute_health_index(self, X):
        """计算健康指数
        健康指数 = 1 - 异常点的比例
        """
        # health_indices = np.zeros(X.shape[0])
        # for i in range(X.shape[0]):
        #     weighted_dist = self._compute_weighted_mahalanobis_distance(X[i])
        #     # 健康指数计算，距离越大，健康指数越小
        #     health_index = 1 / (1 + weighted_dist)
        #     health_indices[i] = health_index
        # return health_indices
        flags = self.predict_anomaly(X)[0]
        hi = 1 - np.mean(flags)
        return hi


def train_som(X, grid_size=(5, 5), iterations=1000, learning_rate=0.5, sigma=1.0, random_state=None):
    """训练SOM模型的包装函数"""
    input_dim = X.shape[1]
    model = SOM(
        grid_size=grid_size,
        input_dim=input_dim,
        learning_rate=learning_rate,
        sigma=sigma,
        random_state=random_state,
    )
    model.fit(X, iterations=iterations)
    return model
