import ast
import astor
import os

def transform_code(code):
    # 将代码解析为AST
    tree = ast.parse(code)

    class ForLoopTransformer(ast.NodeTransformer):
        def visit_For(self, node):
            self.generic_visit(node)  # 递归地访问子节点

            # 处理 for 循环：for i in range(start, end, step)
            if (
                isinstance(node.iter, ast.Call) and 
                isinstance(node.iter.func, ast.Name) and 
                node.iter.func.id == 'range'
            ):
                range_func = node.iter
                args = range_func.args
                num_args = len(args)
                
                # 提取 start, end, step
                if num_args == 1:
                    start = ast.Constant(value=0)
                    end = args[0]
                    step = ast.Constant(value=1)
                elif num_args == 2:
                    start, end = args
                    step = ast.Constant(value=1)
                elif num_args >= 3:
                    start, end, step = args[:3]
                else:
                    start = ast.Constant(value=0)
                    end = ast.Constant(value=0)
                    step = ast.Constant(value=1)

                # 确定步长的增减方向
                # 这里我们需要判断step是否为正或负，以决定条件和操作符
                # 如果step是一个复杂表达式或变量，可能需要更复杂的处理
                if isinstance(step, ast.Constant):
                    step_value = step.value
                    if step_value > 0:
                        op = ast.Add()
                        compare_op = ast.Lt()
                    else:
                        op = ast.Sub()
                        compare_op = ast.Gt()
                else:
                    # 如果step不是常量，我们假设为正步长
                    # 您可以根据需要扩展此逻辑
                    op = ast.Add()
                    compare_op = ast.Lt()

                # 创建初始赋值节点
                init_node = ast.Assign(
                    targets=[ast.Name(id=node.target.id, ctx=ast.Store())],
                    value=start
                )

                # 创建 while 循环
                cond_node = ast.While(
                    test=ast.Compare(
                        left=ast.Name(id=node.target.id, ctx=ast.Load()),
                        ops=[compare_op],
                        comparators=[end]
                    ),
                    body=node.body + [
                        ast.AugAssign(
                            target=ast.Name(id=node.target.id, ctx=ast.Store()),
                            op=op,
                            value=step  # 使用动态步长
                        )
                    ],
                    orelse=[]
                )

                return [init_node, cond_node]

            # 处理 for 循环：for item in iterable
            elif isinstance(node.iter, ast.Name):
                iter_name = node.iter.id
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

            # 处理 for 循环：for item in iterable.splitlines()
            elif (
                isinstance(node.iter, ast.Call) and 
                isinstance(node.iter.func, ast.Attribute) and 
                node.iter.func.attr == 'splitlines'
            ):
                iter_call = node.iter
                if isinstance(iter_call.func.value, ast.Name):
                    iter_name = iter_call.func.value.id
                else:
                    # 如果是更复杂的表达式，可以在这里添加更多处理逻辑
                    return node

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
                                args=[
                                    ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id=iter_name, ctx=ast.Load()),
                                            attr='splitlines',
                                            ctx=ast.Load()
                                        ),
                                        args=[],
                                        keywords=[]
                                    )
                                ],
                                keywords=[]
                            )
                        ]
                    ),
                    body=[
                        ast.Assign(
                            targets=[ast.Name(id=node.target.id, ctx=ast.Store())],
                            value=ast.Subscript(
                                value=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id=iter_name, ctx=ast.Load()),
                                        attr='splitlines',
                                        ctx=ast.Load()
                                    ),
                                    args=[],
                                    keywords=[]
                                ),
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

            # 拆分 or 条件
            or_conditions = self.split_or_conditions(node.test)

            new_ifs = []
            for or_condition in or_conditions:
                # 拆分 and 条件
                and_conditions = self.split_and_conditions(or_condition)
                if and_conditions:
                    # 创建嵌套的 if 结构来处理 and 条件
                    nested_if = self.create_nested_if(and_conditions, node.body, node.orelse)
                    new_ifs.append(nested_if)
                else:
                    # 如果没有 and 条件，直接使用原始的条件
                    new_if = ast.If(test=or_condition, body=node.body, orelse=[])
                    new_ifs.append(new_if)

            if len(new_ifs) == 1:
                # 只有一个条件，附加原始的 else
                new_if = new_ifs[0]
                new_if.orelse = node.orelse
                return new_if
            else:
                # 多个条件，转换为 if-elif 结构，并将 else 附加到最后一个 elif
                for i in range(len(new_ifs) - 1):
                    new_ifs[i].orelse = [new_ifs[i + 1]]
                # 将原始的 else 附加到最后一个 elif
                new_ifs[-1].orelse = node.orelse
                return new_ifs[0]

        def split_or_conditions(self, node):
            """递归拆分 or 条件"""
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_or_conditions(value))
                return conditions
            return [node]

        def split_and_conditions(self, node):
            """递归拆分 and 条件"""
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                conditions = []
                for value in node.values:
                    conditions.extend(self.split_and_conditions(value))
                return conditions
            return [node]

        def create_nested_if(self, conditions, body, orelse):
            # 从后向前创建嵌套的 if 语句
            current_if = ast.If(test=conditions[-1], body=body, orelse=orelse)
            for condition in reversed(conditions[:-1]):
                current_if = ast.If(test=condition, body=[current_if], orelse=orelse)
            return current_if

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
                    if len(conditions) == 2:
                        condition1, condition2 = conditions

                        new_while = ast.While(test=condition1, body=[
                            ast.If(test=condition2, body=nested_while, orelse=[ast.Break()])
                        ], orelse=[])

                        return new_while
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

    # 修复位置和上下文
    ast.fix_missing_locations(tree)

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

    # Split the code into lines
    lines = flowchart_code.strip().split('\n')
    
    node_lines = []
    edge_lines = []

    # Separate nodes and edges based on the first symbol
    for line in lines:
        line = line.strip()
        if '=>' in line:
            node_lines.append(line)
        elif '->' in line:
            edge_lines.append(line)

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
    node_id_counter = max(
        [int(re.findall(r'\d+', nid)[0]) for nid in nodes if re.findall(r'\d+', nid)],
        default=10000
    ) + 1

    for node_id, node in list(nodes.items()):
        if node['type'] == 'operation' and 'if' in node['content']:
            # Extract operation and condition
            op_content = node['content']
            match = re.match(r'(.*)\s+if\s+(.*)', op_content)
            if match:
                operation, condition = match.groups()
                operation = operation.strip()
                condition = condition.strip()

                # 1. Remove unnecessary parentheses around the condition
                if condition.startswith('(') and condition.endswith(')'):
                    condition = condition[1:-1].strip()

                # 2. Create a new condition node with single pair of parentheses
                new_cond_id = f"cond{node_id_counter}"
                node_id_counter += 1
                new_nodes[new_cond_id] = {'type': 'condition', 'content': f'if ({condition})'}

                # Update the original node to only contain the operation
                new_nodes[node_id]['content'] = operation

                # Redirect incoming edges to the new condition node
                for edge in new_edges:
                    if edge['to'] == node_id:
                        edge['to'] = new_cond_id

                # Remove outgoing edges from the original operation node
                original_outgoing_edges = [edge for edge in new_edges if edge['from'] == node_id]
                new_edges = [edge for edge in new_edges if edge not in original_outgoing_edges]

                # Add 'yes' edge from the condition node to the operation node
                new_edges.append({'from': new_cond_id, 'to': node_id, 'label': 'yes'})

                # Reconnect the original outgoing edges from the operation node
                for edge in original_outgoing_edges:
                    new_edges.append({'from': node_id, 'to': edge['to'], 'label': edge.get('label')})

                # Add 'no' edges from the condition node to the same nodes as the operation node
                for edge in original_outgoing_edges:
                    new_edges.append({'from': new_cond_id, 'to': edge['to'], 'label': 'no'})

            else:
                continue  # Skip if the pattern doesn't match

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
        match = re.match(r'(\w+)(\(([^)]+)\))?->(\w+)', edge)
        if match:
            from_node, _, label, to_node = match.groups()
            label = label.strip() if label else None
            outgoing_edges[from_node].append((to_node, label))
            incoming_edges[to_node].append((from_node, label))
        else:
            raise ValueError(f"Invalid edge line: {edge}")

    # Identify all 'break' nodes
    break_nodes = [node_id for node_id, info in nodes.items() if 'break' in info.lower()]

    # Function to find the innermost 'while' loop for a given 'break' node
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
            if 'while' in node_info:
                return from_node
            else:
                queue.extend(incoming_edges[from_node])
        return None

    # Function to remove an edge
    def remove_edge(from_node, to_node):
        outgoing_edges[from_node] = [
            (to, label) for to, label in outgoing_edges[from_node] if to != to_node
        ]

    # Function to add an edge
    def add_edge(from_node, to_node, label=None):
        outgoing_edges[from_node].append((to_node, label))

    # Process each 'break' node
    for break_node_id in break_nodes:
        # Find the innermost 'while' loop
        innermost_loop_node_id = find_innermost_loop(break_node_id)
        if not innermost_loop_node_id:
            continue

        # Find the exit node after the 'while' loop
        loop_exit_nodes = [
            to_node for to_node, label in outgoing_edges[innermost_loop_node_id]
            if label == 'no'
        ]
        if not loop_exit_nodes:
            continue
        loop_exit_node_id = loop_exit_nodes[0]  # Assuming only one exit node

        # Find the 'if' node(s) leading to the 'break' node
        if_nodes = [
            from_node for from_node, label in incoming_edges[break_node_id]
            if 'if' in nodes[from_node].lower()
        ]
        for break_if_node_id in if_nodes:
            # Redirect the 'no' edge of the 'if' node to the operation after 'break'
            remove_edge(break_if_node_id, break_node_id)
            add_edge(break_if_node_id, loop_exit_node_id, 'no')

        # Remove the 'break' node and its edges
        nodes.pop(break_node_id, None)
        outgoing_edges.pop(break_node_id, None)
        incoming_edges.pop(break_node_id, None)

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
    modified_code = "\n".join([f"{node_id}=>{info}" for node_id, info in nodes.items()])
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

import re
from collections import defaultdict

def parse_flowchart(flowchart_code):
    """
    解析流程图代码，返回节点字典和边列表。

    参数:
    flowchart_code (str): flowchart.js格式的流程图代码。

    返回:
    tuple: (nodes, edges)
        nodes (dict): 节点ID到节点属性的映射。
        edges (list): 边的列表，每个边是一个元组 (from_node, to_node, condition)。
    """
    node_pattern = re.compile(r'(\w+)=>(\w+):\s*(.+)')
    edge_pattern = re.compile(r'(\w+)->(\w+)')
    conditional_edge_pattern = re.compile(r'(\w+)\((yes|no)\)->(\w+)')

    nodes = {}
    edges = []

    for line in flowchart_code.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue  # 跳过空行和注释
        node_match = node_pattern.match(line)
        if node_match:
            node_id, node_type, description = node_match.groups()
            nodes[node_id] = {'type': node_type, 'description': description}
        else:
            # 处理带有条件的边，例如 cond1077(yes)->cond1082
            conditional_match = conditional_edge_pattern.match(line)
            if conditional_match:
                from_node, condition, to_node = conditional_match.groups()
                edges.append((from_node, to_node, condition))
            else:
                # 处理普通的边，例如 st1071->io1073
                edge_match = edge_pattern.match(line)
                if edge_match:
                    from_node, to_node = edge_match.groups()
                    edges.append((from_node, to_node, None))
    
    return nodes, edges

def find_duplicate_nodes(nodes):
    """
    查找具有相同类型和描述的节点，返回映射。

    参数:
    nodes (dict): 节点ID到节点属性的映射。

    返回:
    dict: (类型, 描述) 到节点ID列表的映射。
    """
    description_map = defaultdict(list)
    for node_id, attrs in nodes.items():
        key = (attrs['type'], attrs['description'])
        description_map[key].append(node_id)
    return description_map

def merge_duplicate_nodes(nodes, edges):
    """
    合并重复的节点，更新边以指向唯一的节点，并删除来自重复节点的边。

    参数:
    nodes (dict): 节点ID到节点属性的映射。
    edges (list): 边的列表，每个边是一个元组 (from_node, to_node, condition)。

    返回:
    tuple: (merged_nodes, merged_edges)
        merged_nodes (dict): 合并后的节点字典。
        merged_edges (list): 合并后的边列表。
    """
    description_map = find_duplicate_nodes(nodes)
    duplicates = {}
    master_nodes = set()

    for key, node_ids in description_map.items():
        if len(node_ids) > 1:
            master = node_ids[0]  # 选择第一个作为主节点
            master_nodes.add(master)
            for dup in node_ids[1:]:
                duplicates[dup] = master

    # 更新边指向主节点
    merged_edges = []
    for from_node, to_node, condition in edges:
        # 如果 to_node 是重复节点，指向 master node
        if to_node in duplicates:
            merged_to_node = duplicates[to_node]
            merged_edges.append((from_node, merged_to_node, condition))
        else:
            merged_edges.append((from_node, to_node, condition))
    
    # 移除来自重复节点的边
    merged_edges = [
        (from_node, to_node, condition)
        for from_node, to_node, condition in merged_edges
        if from_node not in duplicates  # 移除来自重复节点的边
    ]

    # 移除重复的节点
    merged_nodes = {nid: attrs for nid, attrs in nodes.items() if nid not in duplicates}

    return merged_nodes, merged_edges

def generate_flowchart_code(nodes, edges):
    """
    根据节点字典和边列表生成流程图代码。

    参数:
    nodes (dict): 节点ID到节点属性的映射。
    edges (list): 边的列表，每个边是一个元组 (from_node, to_node, condition)。

    返回:
    str: 以flowchart.js格式表示的流程图代码。
    """
    lines = []
    for node_id, attrs in nodes.items():
        lines.append(f"{node_id}=>{attrs['type']}: {attrs['description']}")
    for from_node, to_node, condition in edges:
        if condition:
            lines.append(f"{from_node}({condition})->{to_node}")
        else:
            lines.append(f"{from_node}->{to_node}")
    return '\n'.join(lines)

def optimize_flowchart_code(flowchart_code):
    """
    优化流程图代码，消除重复的节点并删除相关边。

    参数:
    flowchart_code (str): 原始的flowchart.js格式流程图代码。

    返回:
    str: 优化后的flowchart.js格式流程图代码。
    """
    # 解析流程图代码
    nodes, edges = parse_flowchart(flowchart_code)

    # 合并重复的节点
    merged_nodes, merged_edges = merge_duplicate_nodes(nodes, edges)

    # 重新生成优化后的流程图代码
    optimized_flowchart_code = generate_flowchart_code(merged_nodes, merged_edges)

    return optimized_flowchart_code

import re
from collections import defaultdict

def merge_duplicate_nodes_and_remove_duplicate_connections(flowchart_str):
    """
    合并流程图中具有相同类型和标签的重复节点，并移除重复的连接线和自循环连接。

    参数:
        flowchart_str (str): 原始的流程图定义字符串。

    返回:
        str: 处理后的流程图定义字符串。
    """
    # 分离节点定义和连接
    lines = flowchart_str.strip().split('\n')
    node_definitions = {}
    connections = []
    # 修改正则表达式以捕获完整的节点类型
    node_pattern = re.compile(r'(\w+)=>([^:]+):\s*(.+)')
    connection_pattern = re.compile(r'(\w+\??)(\([\w\s]+\))?->(\w+)')

    # 解析节点定义
    for line in lines:
        node_match = node_pattern.match(line)
        if node_match:
            node_id, node_type, label = node_match.groups()
            node_definitions[node_id] = (node_type.strip(), label.strip())
        else:
            connections.append(line.strip())

    # 识别重复的节点（根据类型和标签）
    type_label_to_nodes = defaultdict(list)
    for node_id, (node_type, label) in node_definitions.items():
        key = (node_type, label)
        type_label_to_nodes[key].append(node_id)

    # 创建节点ID映射，重复的指向代表节点
    node_mapping = {}
    for nodes in type_label_to_nodes.values():
        if len(nodes) > 1:
            representative = nodes[0]
            for dup in nodes[1:]:
                node_mapping[dup] = representative

    # 更新连接，并移除重复的连接线、自循环连接和长度为2的循环
    unique_connections = set()
    updated_connections = []
    edges = defaultdict(set)

    for conn in connections:
        # 替换节点ID
        def replace_node(match):
            from_node = match.group(1)
            condition = match.group(2) if match.group(2) else ''
            to_node = match.group(3)
            # 替换 from_node 和 to_node 如果它们在映射中
            from_node_replaced = node_mapping.get(from_node.rstrip('?'), from_node.rstrip('?'))
            to_node_replaced = node_mapping.get(to_node, to_node)
            # 保留 '?' 后缀
            if from_node.endswith('?'):
                from_node_replaced += '?'
            return f'{from_node_replaced}{condition}->{to_node_replaced}'

        updated_conn = connection_pattern.sub(replace_node, conn).strip()

        # 标准化连接线格式（去除多余空格）
        updated_conn = re.sub(r'\s+', ' ', updated_conn)

        # 解析连接以获取源节点和目标节点
        conn_match = re.match(r'(\w+\??)(\([\w\s]+\))?->(\w+)', updated_conn)
        if conn_match:
            from_node = conn_match.group(1)
            condition = conn_match.group(2) if conn_match.group(2) else ''
            to_node = conn_match.group(3)

            # Remove '?' suffix for node IDs when checking for cycles and self-loops
            from_node_id = from_node.rstrip('?')
            to_node_id = to_node

            # 检查是否为自循环连接
            if from_node_id == to_node_id:
                continue  # 跳过自循环连接

            # 检查是否存在一个反向连接，形成长度为2的循环
            if to_node_id in edges and from_node_id in edges[to_node_id]:
                # 跳过此连接以避免形成长度为2的循环
                continue

            # 添加边到edges
            edges[from_node_id].add(to_node_id)

            # 创建一个标准化的连接键，包括源节点、条件和目标节点
            connection_key = (from_node, condition, to_node)

            # 检查是否为重复连接
            if connection_key not in unique_connections:
                unique_connections.add(connection_key)
                updated_connections.append(updated_conn)
            else:
                # 如果需要调试，可以打印重复的连接
                # print(f"重复连接已移除: {updated_conn}")
                pass

    # 生成新的节点定义，排除重复节点
    unique_nodes = {nid: info for nid, info in node_definitions.items() if nid not in node_mapping}

    # 按照原始顺序重新排列节点定义
    new_flowchart_lines = []
    for line in lines:
        node_match = node_pattern.match(line)
        if node_match:
            node_id = node_match.group(1)
            if node_id in unique_nodes:
                node_type, label = unique_nodes[node_id]
                # 保持原始节点ID和格式
                new_flowchart_lines.append(f'{node_id}=>{node_type}: {label}')

    # 添加更新后的连接线
    new_flowchart_lines.extend(updated_connections)

    return '\n'.join(new_flowchart_lines)

def modify_flowchart(flowchart_code):
    # 将流程图代码拆分为行
    lines = flowchart_code.strip().split('\n')
    # 分离节点定义和边
    node_defs = []
    edges = []
    for line in lines:
        if '=>' in line:
            node_defs.append(line.strip())
        elif '->' in line:
            edges.append(line.strip())
        else:
            continue  # 忽略空行或无效行

    # 构建节点名称到定义的映射
    nodes = {}
    for node_def in node_defs:
        node_name, rest = node_def.split('=>', 1)
        nodes[node_name.strip()] = rest.strip()

    # 构建边的数据结构
    outgoing_edges = {}  # 节点名 -> [(目标节点, 边标签)]
    incoming_edges = {}  # 节点名 -> [(源节点, 边标签)]

    for edge in edges:
        if '->' not in edge:
            continue
        if '(' in edge and ')' in edge:
            from_node_with_label, to_node = edge.split('->')
            from_node, label = from_node_with_label.split('(')
            label = label.rstrip(')')
            from_node = from_node.strip()
            to_node = to_node.strip()
            edge_label = label
        else:
            from_node, to_node = edge.split('->')
            from_node = from_node.strip()
            to_node = to_node.strip()
            edge_label = None

        # 更新边的数据结构
        outgoing_edges.setdefault(from_node, []).append((to_node, edge_label))
        incoming_edges.setdefault(to_node, []).append((from_node, edge_label))

    # 找到所有的'continue'节点
    continue_nodes = [node_name for node_name, definition in nodes.items() if 'continue' in definition]

    for continue_node in continue_nodes:
        # 假设循环的步长节点是'op17002'
        loop_increment_node = None
        for node_name, definition in nodes.items():
            if 'operation' in definition and 'i += 1' in definition:
                loop_increment_node = node_name
                break
        if not loop_increment_node:
            continue  # 如果找不到步长节点，跳过

        # 找到'continue'节点的前驱节点
        predecessors = incoming_edges.get(continue_node, [])

        for from_node, edge_label in predecessors:
            # 更新前驱节点的边，指向步长节点
            edges_list = outgoing_edges.get(from_node, [])
            # 移除指向'continue'节点的边
            edges_list = [ (to_node, label) for (to_node, label) in edges_list if not (to_node == continue_node and label == edge_label)]
            outgoing_edges[from_node] = edges_list
            # 添加指向步长节点的边
            outgoing_edges[from_node].append((loop_increment_node, edge_label))
            incoming_edges.setdefault(loop_increment_node, []).append((from_node, edge_label))

        # 移除'continue'节点和相关的边
        nodes.pop(continue_node, None)
        outgoing_edges.pop(continue_node, None)
        incoming_edges.pop(continue_node, None)

    # 重新构建流程图代码
    new_node_defs = [f"{node_name}=>{definition}" for node_name, definition in nodes.items()]
    new_edges = []
    for from_node, edges_list in outgoing_edges.items():
        for to_node, edge_label in edges_list:
            if edge_label:
                new_edges.append(f"{from_node}({edge_label})->{to_node}")
            else:
                new_edges.append(f"{from_node}->{to_node}")

    return '\n'.join(new_node_defs + new_edges)

from graphviz import Digraph

def generate_and_save_flowchart(flowchart_code, output_filename='flowchart_output'):
    """
    根据输入的流程图描述，生成并保存对应的流程图图片。

    参数:
    flowchart_code (str): 输入的流程图描述代码。
    output_filename (str): 输出文件的基础名称（默认保存为 'flowchart_output.png'）。
    """

    # 定义保存图片的目录
    save_directory = r"."

    # 创建一个Graphviz的Digraph对象
    dot = Digraph()

    # 解析流程图代码
    for line in flowchart_code.splitlines():
        line = line.strip()

        if '=>' in line:  # 处理节点定义
            node_id, description = line.split('=>', 1)
            node_id = node_id.strip()

            # 移除 while 和 if 关键字及括号
            if description.startswith('condition: while (') or description.startswith('condition: if ('):
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

        elif '->' in line:  # 处理边关系
            source, target = line.split('->', 1)
            condition = None

            # 检查是否有条件
            if '(' in source and ')' in source:
                source, condition = source.split('(', 1)
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

def remove_false_edges(flowchart_code):
    """
    解析流程图代码，识别始终为真的条件（如 'while True'），并删除这些条件的假分支边。

    参数:
    flowchart_code (str): 原始的流程图代码。

    返回:
    str: 修改后的流程图代码，已删除不可能发生的假分支边。
    """
    # 将流程图代码按行分割
    lines = flowchart_code.split('\n')
    
    # 存储节点和边
    nodes = {}
    edges = []
    # 存储始终为真的条件节点ID
    always_true_conditions = set()
    
    # 解析节点和边
    for line in lines:
        line = line.strip()
        if '=>' in line:
            # 解析节点
            node_id, rest = line.split('=>', 1)
            node_type, label = rest.split(':', 1)
            node_id = node_id.strip()
            node_type = node_type.strip()
            label = label.strip()
            nodes[node_id] = {'type': node_type, 'label': label}
            # 检查是否是始终为真的条件
            if node_type.lower() == 'condition' and 'while True' in label:
                always_true_conditions.add(node_id)
        elif '->' in line:
            # 解析边
            edges.append(line)
    
    # 过滤掉始终为真的条件的假分支边
    filtered_edges = []
    for edge in edges:
        # 检查边是否有条件标签，如 (yes) 或 (no)
        if '(' in edge and ')' in edge:
            from_part, to_node = edge.split('->', 1)
            from_node = from_part[:from_part.find('(')].strip()
            condition = from_part[from_part.find('(')+1 : from_part.find(')')].strip().lower()
            to_node = to_node.strip()
            # 如果是始终为真的条件且是 'no' 分支，则跳过该边
            if from_node in always_true_conditions and condition == 'no':
                continue
        # 保留其他边
        filtered_edges.append(edge)
    
    # 重新组合节点和过滤后的边
    node_lines = [line for line in lines if '=>' in line]
    edge_lines = filtered_edges
    modified_flowchart = '\n'.join(node_lines + edge_lines)
    
    return modified_flowchart
