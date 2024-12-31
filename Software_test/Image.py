import ast
from random import random

import astor
import numpy as np

from Control_flow import parse_edges_from_output_code, generate_adjacency_matrix, parse_edges
from jjj import Trans, generate_test_cases_from_paths
from nsz import find_linearly_independent_paths
from zzz import get_basic_paths


def transform_code(code):
    # 将代码解析为AST
    tree = ast.parse(code)

    class ForLoopTransformer(ast.NodeTransformer):
        def visit_For(self, node):
            self.generic_visit(node)  # 递归地访问子节点

            if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                range_func = node.iter
                start = range_func.args[0]
                end = range_func.args[1]
                if len(range_func.args) == 3:
                    step = range_func.args[2]
                else:
                    step = ast.Constant(value=1)

                if isinstance(step, ast.Constant) and step.value > 0:
                    op = ast.Add()
                else:
                    op = ast.Sub()

                # 创建初始赋值节点
                init_node = ast.Assign(
                    targets=[ast.Name(id=node.target.id, ctx=ast.Store())],
                    value=start
                )

                # 创建 while 循环
                cond_node = ast.While(
                    test=ast.Compare(
                        left=ast.Name(id=node.target.id, ctx=ast.Load()),
                        ops=[ast.Gt() if isinstance(op, ast.Sub) else ast.Lt()],
                        comparators=[end]
                    ),
                    body=node.body + [
                        ast.AugAssign(
                            target=ast.Name(id=node.target.id, ctx=ast.Store()),
                            op=op,
                            value=ast.Constant(value=1)
                        )
                    ],
                    orelse=[]
                )

                return [init_node, cond_node]

            elif isinstance(node.iter, ast.Name):
                iter_name = node.iter.id
                # 生成唯一的索引变量名
                index_var = f'{iter_name}_index'

                # 创建初始赋值节点 iter_name_index = 0
                init_node = ast.Assign(
                    targets=[ast.Name(id=index_var, ctx=ast.Store())],
                    value=ast.Constant(value=0)
                )

                # 创建 while 循环
                cond_node = ast.While(
                    test=ast.Compare(
                        left=ast.Name(id=index_var, ctx=ast.Load()),
                        ops=[ast.Lt()],
                        comparators=[
                            ast.Call(
                                func=ast.Name(id='len', ctx=ast.Load()),
                                args=[ast.Name(id=iter_name, ctx=ast.Load())],
                                keywords=[]
                            )
                        ]
                    ),
                    body=[
                        ast.Assign(
                            targets=[ast.Name(id=node.target.id, ctx=ast.Store())],
                            value=ast.Subscript(
                                value=ast.Name(id=iter_name, ctx=ast.Load()),
                                slice=ast.Index(value=ast.Name(id=index_var, ctx=ast.Load())),
                                ctx=ast.Load()
                            )
                        )
                    ] + node.body + [
                        ast.AugAssign(
                            target=ast.Name(id=index_var, ctx=ast.Store()),
                            op=ast.Add(),
                            value=ast.Constant(value=1)
                        )
                    ],
                    orelse=[]
                )

                return [init_node, cond_node]

            return node

    # 创建一个自定义的NodeTransformer来拆分复杂的if条件并使用elif
    class IfConditionSplitter(ast.NodeTransformer):
        def visit_If(self, node):
            self.generic_visit(node)  # 先递归处理子节点

            conditions = self.split_or_conditions(node.test)

            new_ifs = []
            for i, or_condition in enumerate(conditions):
                and_conditions = self.split_and_conditions(or_condition)
                new_body = node.body
                for and_condition in reversed(and_conditions):
                    if i == 0:
                        new_if = ast.If(test=and_condition, body=new_body, orelse=node.orelse)
                    else:
                        new_if = ast.If(test=and_condition, body=new_body, orelse=[])
                    new_body = [new_if]
                new_ifs.extend(new_body)

            if len(new_ifs) == 1:
                return new_ifs[0]
            else:
                # 将多个if转换为 if-elif 结构
                for i in range(1, len(new_ifs)):
                    new_ifs[i-1].orelse = [new_ifs[i]]
                return new_ifs[0]

        def split_or_conditions(self, node):
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_or_conditions(value))
                return conditions
            return [node]

        def split_and_conditions(self, node):
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_and_conditions(value))
                return conditions
            return [node]

    class WhileConditionSplitter(ast.NodeTransformer):
        def visit_While(self, node):
            self.generic_visit(node)  # 递归访问子节点

            # 检查 while 循环条件是否包含 and 或 or
            if isinstance(node.test, ast.BoolOp):
                if isinstance(node.test.op, ast.And):
                    # 处理 and 条件
                    conditions = self.split_and_conditions(node.test)

                    # 创建嵌套的 while 结构
                    nested_while = node.body
                    for condition in reversed(conditions):
                        nested_while = [ast.While(test=condition, body=nested_while, orelse=[])]

                    return nested_while[0]
                elif isinstance(node.test.op, ast.Or):
                    # 处理 or 条件
                    conditions = self.split_or_conditions(node.test)

                    # 创建 if-elif-else 结构
                    if_elif_chain = []
                    for condition in conditions:
                        if_elif_chain.append(ast.If(test=condition, body=node.body, orelse=[]))

                    # 将 if-elif 语句串联起来
                    for i in range(len(if_elif_chain) - 1):
                        if_elif_chain[i].orelse = [if_elif_chain[i + 1]]

                    # 最后的 else 用来跳出 while 循环
                    if_elif_chain[-1].orelse = [ast.Break()]

                    # 替换原始 while 循环为 while True 和 if-elif-else 结构
                    new_while = ast.While(test=ast.Constant(value=True), body=[if_elif_chain[0]], orelse=[])

                    return new_while

            # 如果没有 and 或 or 条件，则返回原始节点
            return node

        def split_and_conditions(self, node):
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_and_conditions(value))
                return conditions
            return [node]

        def split_or_conditions(self, node):
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_or_conditions(value))
                return conditions
            return [node]

    # 应用所有转换器
    tree = ForLoopTransformer().visit(tree)
    tree = IfConditionSplitter().visit(tree)
    tree = WhileConditionSplitter().visit(tree)

    # 将AST转换回代码
    new_code = astor.to_source(tree)
    return new_code

from pyflowchart import Flowchart

def generate_flowchart_from_code(code):
    """
    将Python代码转换为流程图，并以flowchart.js格式输出。

    参数:
    code (str): 要转换为流程图的Python代码。

    返回:
    str: 以flowchart.js格式表示的流程图代码。
    """
    # 使用 pyflowchart 将代码转换为流程图
    flowchart = Flowchart.from_code(code)

    # 将流程图转换为flowchart.js格式
    flowchart_code = flowchart.flowchart()

    return flowchart_code

def process_flowchart(flowchart_code):
    import re
    import copy

    # Split the code into nodes and edges
    lines = flowchart_code.strip().split('\n')
    node_lines = [line for line in lines if '=>' in line]
    edge_lines = [line for line in lines if '->' in line]

    # Parse nodes
    nodes = {}
    for line in node_lines:
        match = re.match(r'(\w+)=>(\w+):\s*(.*)', line)
        if match:
            node_id, node_type, content = match.groups()
            nodes[node_id] = {'type': node_type, 'content': content.strip()}
        else:
            raise ValueError(f"Invalid node line: {line}")

    # Parse edges
    edges = []
    for line in edge_lines:
        # Updated regex to accept any label inside parentheses
        match = re.match(r'(\w+)(\(([^)]+)\))?->(\w+)', line)
        if match:
            from_node, _, label, to_node = match.groups()
            edges.append({'from': from_node, 'to': to_node, 'label': label})
        else:
            raise ValueError(f"Invalid edge line: {line}")

    # Build adjacency for incoming and outgoing edges
    incoming_edges = {node_id: [] for node_id in nodes}
    outgoing_edges = {node_id: [] for node_id in nodes}
    for edge in edges:
        outgoing_edges[edge['from']].append(edge)
        incoming_edges[edge['to']].append(edge)

    # Process nodes with 'if' in operation
    new_nodes = copy.deepcopy(nodes)
    new_edges = [edge.copy() for edge in edges]
    node_id_counter = max([int(re.findall(r'\d+', nid)[0]) for nid in nodes if re.findall(r'\d+', nid)]) + 1

    for node_id, node in nodes.items():
        if node['type'] == 'operation' and 'if' in node['content']:
            # Extract condition
            op_content = node['content']
            match = re.match(r'(.*)\s+if\s+\((.*)\)', op_content)
            if match:
                operation, condition = match.groups()
                operation = operation.strip()
                condition = condition.strip()
            else:
                continue  # Skip if pattern doesn't match

            # Create new condition node
            new_cond_id = f"cond{node_id_counter}"
            node_id_counter += 1
            new_nodes[new_cond_id] = {'type': 'condition', 'content': f'if ({condition})'}

            # Update operation node
            new_nodes[node_id]['content'] = operation

            # Redirect incoming edges to the new condition node
            for edge in new_edges:
                if edge['to'] == node_id:
                    edge['to'] = new_cond_id

            # Collect outgoing edges from the operation node
            original_outgoing_edges = [edge for edge in new_edges if edge['from'] == node_id]
            next_nodes = [edge['to'] for edge in original_outgoing_edges]

            # Remove outgoing edges from the operation node
            new_edges = [edge for edge in new_edges if edge not in original_outgoing_edges]

            # Add 'yes' edge from condition node to operation node
            new_edges.append({'from': new_cond_id, 'to': node_id, 'label': 'yes'})

            # Add 'no' edges from condition node to next_nodes
            for next_node in next_nodes:
                new_edges.append({'from': new_cond_id, 'to': next_node, 'label': 'no'})

            # Re-add the original outgoing edges from the operation node
            for next_node in next_nodes:
                new_edges.append({'from': node_id, 'to': next_node, 'label': None})

    # Generate updated flowchart code
    updated_code = ''
    for node_id, node in new_nodes.items():
        updated_code += f"{node_id}=>{node['type']}: {node['content']}\n"

    for edge in new_edges:
        label = f"({edge['label']})" if edge['label'] else ''
        updated_code += f"{edge['from']}{label}->{edge['to']}\n"

    return updated_code.strip()

def modify_flowchart_code(code: str) -> str:
    import re
    from collections import defaultdict, deque

    # Split code lines and initialize nodes and edges
    lines = code.strip().split("\n")
    nodes = {}
    edges = []
    for line in lines:
        line = line.strip()
        if "=>" in line:
            node_id, node_info = line.split("=>", 1)
            nodes[node_id.strip()] = node_info.strip()
        elif "->" in line:
            edges.append(line.strip())

    # Build adjacency lists for traversal
    outgoing_edges = defaultdict(list)
    incoming_edges = defaultdict(list)
    for edge in edges:
        # Match edge with optional label, e.g., cond8947(yes)->cond8980
        match = re.match(r'(\w+)(\(([^)]+)\))?->(\w+)', edge)
        if match:
            from_node, _, label, to_node = match.groups()
            label = label.strip() if label else None
            outgoing_edges[from_node].append((to_node, label))
            incoming_edges[to_node].append((from_node, label))
        else:
            raise ValueError(f"Invalid edge line: {edge}")

    # Ensure all nodes are in outgoing_edges and incoming_edges
    for node_id in nodes:
        outgoing_edges[node_id]  # Initializes empty list if no outgoing edges
        incoming_edges[node_id]  # Initializes empty list if no incoming edges

    # Helper functions to modify edges
    def remove_edge(from_node, to_node, label=None):
        """Removes an edge from outgoing and incoming adjacency lists."""
        if label:
            outgoing_edges[from_node] = [
                (t, l) for (t, l) in outgoing_edges[from_node] if not (t == to_node and l == label)
            ]
            incoming_edges[to_node] = [
                (f, l) for (f, l) in incoming_edges[to_node] if not (f == from_node and l == label)
            ]
        else:
            outgoing_edges[from_node] = [
                (t, l) for (t, l) in outgoing_edges[from_node] if t != to_node
            ]
            incoming_edges[to_node] = [
                (f, l) for (f, l) in incoming_edges[to_node] if f != from_node
            ]

    def add_edge(from_node, to_node, label):
        """Adds an edge to outgoing and incoming adjacency lists."""
        outgoing_edges[from_node].append((to_node, label))
        incoming_edges[to_node].append((from_node, label))

    # Identify all 'break' nodes
    break_nodes = [node_id for node_id, info in nodes.items() if 'break' in info.lower()]

    # Function to find the innermost 'while True' loop for a given 'break' node
    def find_innermost_loop(break_node_id):
        visited = set()
        queue = deque()
        queue.extend(incoming_edges[break_node_id])
        while queue:
            from_node, _ = queue.popleft()
            if from_node in visited:
                continue
            visited.add(from_node)
            node_info = nodes.get(from_node, '').lower()
            if 'while true' in node_info:
                return from_node
            else:
                queue.extend(incoming_edges[from_node])
        return None  # No enclosing 'while True' loop found

    # Function to find the next node after the loop exit
    def find_loop_exit_next_node(loop_node_id):
        # Find the node connected via 'no' label
        loop_exit_nodes = [
            to_node for to_node, label in outgoing_edges[loop_node_id]
            if label == 'no'
        ]
        if not loop_exit_nodes:
            return None
        loop_exit_node_id = loop_exit_nodes[0]  # Assuming only one exit node

        # Traverse 'no' edges to find the ultimate loop exit node
        ultimate_exit_node_id = loop_exit_node_id
        visited_exit = set()
        while True:
            no_edges = [
                to_node for to_node, label in outgoing_edges[ultimate_exit_node_id]
                if label == 'no'
            ]
            if not no_edges:
                break
            next_exit_node_id = no_edges[0]
            if next_exit_node_id in visited_exit:
                break  # Prevent infinite loop in case of cycles
            visited_exit.add(next_exit_node_id)
            ultimate_exit_node_id = next_exit_node_id
        return ultimate_exit_node_id

    # Process each 'break' node
    for break_node_id in break_nodes:
        # Find the 'if' node(s) before the 'break' node
        if_nodes = [
            from_node for from_node, label in incoming_edges[break_node_id]
            if 'if' in nodes[from_node].lower()
        ]
        if not if_nodes:
            continue  # No 'if' node found before 'break', skip
        # Handle all 'if' nodes leading to this 'break'
        for break_if_node_id in if_nodes:
            # Find the innermost 'while True' loop
            innermost_loop_node_id = find_innermost_loop(break_node_id)
            if not innermost_loop_node_id:
                continue  # No enclosing 'while True' loop found, skip

            # Find the node after the 'while True' loop
            ultimate_exit_node_id = find_loop_exit_next_node(innermost_loop_node_id)
            if not ultimate_exit_node_id:
                continue  # No exit node found for 'while True' loop, skip

            # Get the label of the edge from 'break_if_node_id' to 'break_node_id'
            edge_label = None
            for to_node, label in outgoing_edges[break_if_node_id]:
                if to_node == break_node_id:
                    edge_label = label
                    break

            # Redirect the edge from the 'if' node before 'break' to the ultimate loop exit node
            remove_edge(break_if_node_id, break_node_id, edge_label)
            add_edge(break_if_node_id, ultimate_exit_node_id, edge_label)

        # Remove the 'break' node and its edges
        nodes.pop(break_node_id, None)
        outgoing_edges.pop(break_node_id, None)
        incoming_edges.pop(break_node_id, None)

    while_true_nodes = [
        node_id for node_id, info in nodes.items() if 'while true' in info.lower()
    ]
    for while_node_id in while_true_nodes:
        # Find the first node it points to via the '(yes)' edge
        yes_targets = [
            to_node for to_node, label in outgoing_edges[while_node_id]
            if label == 'yes'
        ]
        if not yes_targets:
            continue  # No '(yes)' edge found, cannot replace
        first_node_id = yes_targets[0]

        # Find the node after the 'while True' loop (edge labeled '(no)')
        loop_exit_nodes = [
            to_node for to_node, label in outgoing_edges[while_node_id]
            if label == 'no'
        ]
        if not loop_exit_nodes:
            continue  # No '(no)' edge found, cannot determine loop exit
        loop_exit_node_id = loop_exit_nodes[0]

        # Traverse 'no' edges to find the ultimate loop exit node
        ultimate_exit_node_id = loop_exit_node_id
        visited_exit = set()
        while True:
            no_edges = [
                to_node for to_node, label in outgoing_edges[ultimate_exit_node_id]
                if label == 'no'
            ]
            if not no_edges:
                break
            next_exit_node_id = no_edges[0]
            if next_exit_node_id in visited_exit:
                break  # Prevent infinite loop in case of cycles
            visited_exit.add(next_exit_node_id)
            ultimate_exit_node_id = next_exit_node_id

        # Redirect incoming edges to 'while True' node to the first 'yes' target node
        for from_node, edges_list in list(outgoing_edges.items()):
            new_edges = []
            for to_node, label in edges_list:
                if to_node == while_node_id:
                    new_edges.append((first_node_id, label))
                    incoming_edges[first_node_id].append((from_node, label))
                else:
                    new_edges.append((to_node, label))
            outgoing_edges[from_node] = new_edges

        # Remove the 'while True' node and its edges
        nodes.pop(while_node_id, None)
        outgoing_edges.pop(while_node_id, None)
        incoming_edges.pop(while_node_id, None)

    # Reconstruct edges list
    new_edges = []
    for from_node, edges_list in outgoing_edges.items():
        for to_node, label in edges_list:
            edge_str = f"{from_node}"
            if label:
                edge_str += f"({label})"
            edge_str += f"->{to_node}"
            new_edges.append(edge_str)

    # Reassemble the code
    modified_code = "\n".join([
        f"{node_id}=>{info}" for node_id, info in nodes.items()
    ])
    modified_code += "\n" + "\n".join(new_edges)

    return modified_code


def unify_end_node(flowchart_code):
    # 将输入的流程图代码按行分割成列表
    lines = flowchart_code.split('\n')

    # 找到所有的 end 节点，并记录它们的名称
    end_nodes = [line for line in lines if '=>end:' in line]

    # 如果没有或只有一个 end 节点，直接返回原代码
    if len(end_nodes) <= 1:
        return flowchart_code

    # 统一所有 end 节点的名称为第一个 end 节点的名称
    unified_end = end_nodes[0].split('=>')[0]

    # 构造新的流程图代码
    new_lines = []
    for line in lines:
        if '->' in line:
            for end_node in end_nodes:
                end_node_name = end_node.split('=>')[0]
                line = line.replace('->' + end_node_name, '->' + unified_end)
        if '=>end:' in line and not line.startswith(unified_end):
            continue  # 跳过额外的 end 节点定义
        new_lines.append(line)

    # 返回修改后的流程图代码
    return '\n'.join(new_lines)


from graphviz import Digraph


import os
from graphviz import Digraph

def generate_and_save_flowchart(flowchart_code, output_filename='flowchart_output'):
    """
    根据输入的流程图描述，生成并保存对应的流程图图片。

    参数:
    flowchart_code (str): 输入的流程图描述代码。
    output_filename (str): 输出文件的基础名称（默认保存为 'flowchart_output.png'）。
    """
    # 定义保存图片的目录
    save_directory = r"D:\2024_Study\2024_9_project_computer\SoftWare_test\pic_create"

    # 确保保存目录存在，不存在则创建
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # 创建一个Graphviz的Digraph对象
    dot = Digraph()

    # 解析节点定义并添加到图中
    for line in flowchart_code.splitlines():
        if '=>' in line:
            node_id, description = line.split('=>')
            node_id = node_id.strip()

            # 移除 while 和 if 关键字及括号
            if description.startswith('condition: while') or description.startswith('condition: if'):
                first_bracket_pos = description.find('(')
                if first_bracket_pos != -1 and description.endswith(')'):
                    description = description[:first_bracket_pos] + description[first_bracket_pos + 1:-1]

            description = description.replace('while', '').replace('if', '')

            parts = description.split(':', 1)
            node_type = parts[0].strip()
            label = parts[1].strip() if len(parts) > 1 else ''

            # 根据类型设置节点形状
            if node_type == 'start' or node_type == 'end':
                shape = 'ellipse'
            elif node_type == 'inputoutput':
                shape = 'parallelogram'
            elif node_type == 'condition':
                shape = 'diamond'
            elif node_type == 'operation' or node_type == 'subroutine':
                shape = 'box'
            else:
                shape = 'box'  # 默认形状

            # 添加节点到图中
            dot.node(node_id, label, shape=shape)

    # 解析边关系并添加到图中
    for line in flowchart_code.splitlines():
        if '->' in line:
            source, target = line.split('->')
            condition = None

            # 检查是否有条件
            if '(' in source and ')' in source:
                source, condition = source.split('(')
                condition = condition.strip(')')
                source = source.strip()

            target = target.strip()

            # 添加边到图中（如果有条件则在边上标注）
            if condition:
                dot.edge(source, target, label=condition)
            else:
                dot.edge(source, target)

    # 完整的保存路径
    output_filepath = os.path.join(save_directory, output_filename)

    # 检查文件名是否已经存在，如果存在则添加序号
    base_filepath = output_filepath
    counter = 1
    while os.path.exists(f"{output_filepath}.png"):
        output_filepath = f"{base_filepath}_{counter}"
        counter += 1

    # 渲染并保存流程图
    dot.render(output_filepath, format='png', cleanup=True)

    print(f"Flowchart generated and saved as '{output_filepath}.png'")

    return f"{output_filepath}.png"


# # 示例代码
# code = """
def check_age(age,b):
    if age < 0:
        A = "Invalid"
    elif age <= 18:
        A = "zzz."
    elif age <= 50:
        A = "zzz."
    else:
        A = "zzz."
    if b < 0:
        B = "Invalid"
    elif b <= 18:
        B = "zzz."
    elif b <= 50:
        B = "zzz."
    else:
        B = "zzz."
    return A,B
# """
# print(code)


#
# # 转换代码
# transformed_code = transform_code(code)
#
# flowchart_code = generate_flowchart_from_code(transformed_code)
#
# processed_code = process_flowchart(flowchart_code)
#
# output_code = modify_flowchart_code(processed_code)
#
# output_code = unify_end_node(output_code)
#
# generate_and_save_flowchart(output_code)
#
# edges = parse_edges_from_output_code(output_code)
#
# # 解析节点并生成矩阵
# nodes_cc = parse_edges(edges)
# adjacency_matrix_cc = generate_adjacency_matrix(edges, nodes_cc)
#
# # 示例邻接矩阵表示的图
# adjacency_matrix = np.array(adjacency_matrix_cc)
#
# basic_paths = get_basic_paths(adjacency_matrix, nodes_cc)
#
# independent_paths = find_linearly_independent_paths(basic_paths)
#
# conditions, edges = Trans(output_code)
# # 生成测试用例
# test_cases = generate_test_cases_from_paths(independent_paths, edges, conditions)
#
# # 输出生成的测试用例
# for i, case in enumerate(test_cases):
#     print(f"测试用例 {i + 1}:")
#     if "Error" in case:
#         print(f"  错误: {case['Error']}")
#         print(f"  路径: {case['Path']}")
#     else:
#         print(f"  输入: {case['inputs']}")
#         print(f"  条件: {case['conditions']}")
#     print()