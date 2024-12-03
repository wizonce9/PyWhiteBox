import numpy as np

def parse_edges_from_output_code(output_code):
    edges = []
    lines = output_code.strip().splitlines()

    for line in lines:
        if '->' in line:
            edges.append(line.strip())

    return edges


def parse_edges(edges):
    nodes = {}
    node_count = 0

    # 分析每个边并记录节点
    for edge in edges:
        start, end = edge.split('->')
        start = start.split('(')[0].strip()  # 去除条件判断括号并去除多余空格
        end = end.split('(')[0].strip()

        # 忽略以 'st' 或 'e' 开头的节点
        if start.startswith('st') or start.startswith('e'):
            continue
        if end.startswith('st') or end.startswith('e'):
            continue

        if start not in nodes:
            nodes[start] = node_count
            node_count += 1
        if end not in nodes:
            nodes[end] = node_count
            node_count += 1

    return nodes


def generate_adjacency_matrix(edges, nodes):
    size = len(nodes)
    matrix = np.zeros((size, size), dtype=int)

    for edge in edges:
        start, end = edge.split('->')
        start = start.split('(')[0].strip()  # 去除条件判断括号并去除多余空格
        end = end.split('(')[0].strip()

        # 忽略以 'st' 或 'e' 开头的节点
        if start.startswith('st') or start.startswith('e'):
            continue
        if end.startswith('st') or end.startswith('e'):
            continue

        start_index = nodes[start]
        end_index = nodes[end]

        matrix[start_index, end_index] = 1

    return matrix


# # 从 output_code 中提取 edges
# edges = parse_edges_from_output_code(output_code)
#
# # 解析节点并生成矩阵
# nodes_cc = parse_edges(edges)
# adjacency_matrix_cc = generate_adjacency_matrix(edges, nodes_cc)
#
# print("节点编号:")
# print(nodes_cc)
# print("\n邻接矩阵:")
# print(adjacency_matrix_cc)