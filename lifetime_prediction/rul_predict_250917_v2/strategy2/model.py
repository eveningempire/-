import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestModel:
    def __init__(self, n_estimators=100, contamination="auto", random_state=0, **kwargs):
        """
        初始化孤立森林模型

        参数:
            n_estimators: 树的数量
            contamination: 数据集中异常样本的比例
            random_state: 随机种子
            **kwargs: 其他参数传递给IsolationForest
        """
        self.model = IsolationForest(
            n_estimators=n_estimators, contamination=contamination, random_state=random_state, **kwargs
        )

    def fit(self, X):
        """
        训练孤立森林模型

        参数:
            X: 特征矩阵，shape=(n_samples, n_features)
        返回:
            self
        """
        self.model.fit(X)
        return self

    def predict(self, X):
        """
        预测样本是否异常

        参数:
            X: 特征矩阵，shape=(n_samples, n_features)
        返回:
            预测结果: 1表示正常，-1表示异常
        """
        return self.model.predict(X)

    def score_samples(self, X):
        """
        计算异常分数

        参数:
            X: 特征矩阵，shape=(n_samples, n_features)
        返回:
            异常分数，越小表示越异常
        """
        return self.model.score_samples(X)

    def decision_function(self, X):
        """
        计算决策函数值

        参数:
            X: 特征矩阵，shape=(n_samples, n_features)
        返回:
            决策函数值，越小表示越异常
        """
        return self.model.decision_function(X)

    def get_anomaly_score(self, X):
        """
        获取异常分数（归一化到0-1区间，1表示最异常）

        参数:
            X: 特征矩阵，shape=(n_samples, n_features)
        返回:
            归一化异常分数，越大表示越异常
        """
        # score_samples返回的是原始异常分数的负数，值越小表示越异常
        # 我们需要将其映射到[0,1]区间，1表示最异常
        raw_scores = self.model.score_samples(X)
        # 对分数取负数，使得分数越大表示越异常
        negative_scores = -raw_scores

        # 如果我们有足够的样本，可以用min-max归一化
        if len(negative_scores) > 1:
            min_score = np.min(negative_scores)
            max_score = np.max(negative_scores)
            if max_score > min_score:
                normalized_scores = (negative_scores - min_score) / (max_score - min_score)
                return normalized_scores

        # 如果只有一个样本或所有样本分数相同，使用指数变换将分数映射到[0,1]
        return 1 - np.exp(-negative_scores)


def save_model(model, save_path, **kwargs):
    """
    保存模型和相关参数

    参数:
        model: 训练好的孤立森林模型
        save_path: 保存路径
        **kwargs: 需要保存的其他参数
    """
    save_dict = {"model": model, **kwargs}

    # 确保目录存在
    save_path = Path(save_path)
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        pickle.dump(save_dict, f)

    print(f"模型已保存到: {save_path}")


def load_model(model_path):
    """
    加载模型和相关参数

    参数:
        model_path: 模型文件路径
    返回:
        加载的模型和参数字典
    """
    with open(model_path, "rb") as f:
        model_dict = pickle.load(f)
    return model_dict
