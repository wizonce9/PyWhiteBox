import numpy as np

def find_all_paths(graph, start, end, path=[], visited=None):
    if visited is None:
        visited = {node: 0 for node in graph}

    path = path + [start]
    visited[start] += 1

    if start == end:
        return [path]

    if start not in graph:
        return []

    paths = []
    for node in graph[start]:
        if visited[node] < 2:  # 允许节点最多被访问两次
            new_paths = find_all_paths(graph, node, end, path, visited.copy())
            for p in new_paths:
                if is_valid_path(p):  # 只加入有效的路径
                    paths.append(p)
    return paths

def is_valid_path(path):
    """
    确保路径中的重复片段长度不超过1。
    """
    path_len = len(path)
    for i in range(path_len):
        for j in range(i + 2, path_len):
            if path[i:j] == path[j:j + (j - i)]:  # 检查重复子路径
                return False
    return True

def detect_start_end_nodes(adjacency_matrix):
    nodes = list(range(len(adjacency_matrix)))
    start_nodes = []
    end_nodes = []

    for i in nodes:
        out_degree = np.sum(adjacency_matrix[i])
        in_degree = np.sum(adjacency_matrix[:, i])

        if out_degree > 0 and in_degree == 0:
            start_nodes.append(i)
        if in_degree > 0 and out_degree == 0:
            end_nodes.append(i)

    return start_nodes, end_nodes

def get_edges_from_path(path):
    """
    获取路径中的所有边。
    """
    return set(zip(path, path[1:]))

def contains_all_edges(edge_set, paths):
    """
    检查edge_set中的所有边是否都包含在给定的路径集合中的任意路径中。
    """
    for edge in edge_set:
        if not any(edge in get_edges_from_path(p) for p in paths):
            return False
    return True

def get_basic_paths(adjacency_matrix, nodes):
    nodes_list = list(range(len(adjacency_matrix)))
    graph = {i: [] for i in nodes_list}

    for i in nodes_list:
        for j in nodes_list:
            if adjacency_matrix[i][j] == 1:
                graph[i].append(j)

    start_nodes, end_nodes = detect_start_end_nodes(adjacency_matrix)

    all_paths = []
    for start in start_nodes:
        for end in end_nodes:
            paths = find_all_paths(graph, start, end)
            for path in paths:
                all_paths.append(path)

    # 分离简单路径和包含重复节点的复杂路径
    simple_paths = []
    complex_paths = []
    for path in all_paths:
        if len(path) == len(set(path)):  # 如果路径中没有重复节点
            simple_paths.append(path)
        else:
            complex_paths.append(path)

    # 处理复杂路径，保留非冗余的路径
    non_redundant_paths = simple_paths[:]  # 先保留所有简单路径
    for path in complex_paths:
        edges = get_edges_from_path(path)
        if contains_all_edges(edges, simple_paths):
            continue  # 如果所有边都在简单路径中，跳过
        elif not contains_all_edges(edges, non_redundant_paths):
            non_redundant_paths.append(path)  # 如果当前保留的非冗余路径中没有所有的边，则保留当前路径

    # 用节点名代替编号输出路径
    named_paths = []
    for path in non_redundant_paths:
        named_path = [list(nodes.keys())[list(nodes.values()).index(node)] for node in path]
        named_paths.append(named_path)

    return named_paths

# # 示例邻接矩阵表示的图
# adjacency_matrix = np.array(adjacency_matrix_cc)
#
# basic_paths = get_basic_paths(adjacency_matrix, nodes_cc)
#
# print("基本路径:",basic_paths)
# for path in basic_paths:
#     print(" -> ".join(path))
