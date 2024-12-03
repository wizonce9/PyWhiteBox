import numpy as np

def label_nodes(paths):
    """为每个节点标号"""
    nodes = {}
    node_count = 0

    for path in paths:
        for node in path:
            if node not in nodes:
                nodes[node] = node_count
                node_count += 1

    return nodes


def path_to_vector(path, nodes):
    """将路径转换为向量"""
    vector = np.zeros(len(nodes), dtype=int)
    for node in path:
        vector[nodes[node]] = 1
    return vector

def get_max_independent_rows(matrix):
    """
    获取给定二进制矩阵的最大线性无关行组。

    参数:
    matrix (list of lists 或 numpy.ndarray): 输入的二维0-1矩阵。

    返回:
    list of lists: 最大线性无关的行组成的列表。
    """
    # 将输入转换为 NumPy 数组（如果尚未是的话）
    A = np.array(matrix, dtype=float)
    rows, cols = A.shape
    pivot_rows = []
    pivot_cols = []

    for col in range(cols):
        # 寻找当前列中第一个不为0的行
        for row in range(len(pivot_rows), rows):
            if A[row, col] != 0:
                # 交换当前行与pivot_rows列表中下一行的位置
                A[[len(pivot_rows), row]] = A[[row, len(pivot_rows)]]
                break
        else:
            # 如果该列全为0，则继续下一列
            continue

        pivot = A[len(pivot_rows), col]
        pivot_rows.append(len(pivot_rows))
        pivot_cols.append(col)

        # 将pivot行标准化
        A[len(pivot_rows)-1] = A[len(pivot_rows)-1] / pivot

        # 对其他行进行消元
        for r in range(rows):
            if r != len(pivot_rows)-1 and A[r, col] != 0:
                A[r] = A[r] - A[len(pivot_rows)-1] * A[r, col]

    # 提取最大线性无关的行
    independent_rows = [matrix[i] for i in pivot_rows]
    return independent_rows, pivot_rows


def find_linearly_independent_paths(paths):
    """找出线性无关的路径"""
    nodes = label_nodes(paths)
    path_vectors = np.array([path_to_vector(path, nodes) for path in paths])
    independent_vectors, independent_indices = get_max_independent_rows(path_vectors)

    # 根据线性无关的行的索引返回相应的路径
    independent_paths = [paths[i] for i in independent_indices]

    return independent_paths


#
#
#
# # 示例路径
# paths = [
#     "io5 -> cond9 -> op13 -> cond41 -> op45 -> io75",
#     "io5 -> cond9 -> op13 -> cond41 -> cond50 -> op54 -> io75",
#     "io5 -> cond9 -> op13 -> cond41 -> cond50 -> cond59 -> op63 -> io75",
#     "io5 -> cond9 -> op13 -> cond41 -> cond50 -> cond59 -> op67 -> io75",
#     "io5 -> cond9 -> cond18 -> op22 -> cond41 -> op45 -> io75",
#     "io5 -> cond9 -> cond18 -> op22 -> cond41 -> cond50 -> op54 -> io75",
#     "io5 -> cond9 -> cond18 -> op22 -> cond41 -> cond50 -> cond59 -> op63 -> io75",
#     "io5 -> cond9 -> cond18 -> op22 -> cond41 -> cond50 -> cond59 -> op67 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op31 -> cond41 -> op45 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op31 -> cond41 -> cond50 -> op54 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op31 -> cond41 -> cond50 -> cond59 -> op63 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op31 -> cond41 -> cond50 -> cond59 -> op67 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op35 -> cond41 -> op45 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op35 -> cond41 -> cond50 -> op54 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op35 -> cond41 -> cond50 -> cond59 -> op63 -> io75",
#     "io5 -> cond9 -> cond18 -> cond27 -> op35 -> cond41 -> cond50 -> cond59 -> op67 -> io75"
# ]
#
# # 找出线性无关的路径
# independent_paths = find_linearly_independent_paths(paths)
#
# # 输出线性无关的路径集合
# print("线性无关的路径集合如下：")
# for path in independent_paths:
#     print(path)
