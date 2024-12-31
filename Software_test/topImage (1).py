import ast
import os

import astor


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
                if isinstance(step, ast.Constant) and step.value > 0:
                    op = ast.Add()
                    compare_op = ast.Lt()
                else:
                    op = ast.Sub()
                    compare_op = ast.Gt()

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
                            value=ast.Constant(value=1)
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
    node_id_counter = max([int(re.findall(r'\d+', nid)[0]) for nid in nodes if re.findall(r'\d+', nid)]) + 1

    for node_id, node in nodes.items():
        if node['type'] == 'operation' and 'if' in node['content']:
            # Extract operation and condition
            op_content = node['content']
            match = re.match(r'(.*)\s+if\s+(.*)', op_content)
            if match:
                operation, condition = match.groups()
                operation = operation.strip()
                condition = condition.strip()

                # Create new condition node
                new_cond_id = f"cond{node_id_counter}"
                node_id_counter += 1
                new_nodes[new_cond_id] = {'type': 'condition', 'content': f'if {condition}'}

                # Update the original node to only contain the operation
                new_nodes[node_id]['content'] = operation

                # Redirect incoming edges to the new condition node
                for edge in new_edges:
                    if edge['to'] == node_id:
                        edge['to'] = new_cond_id

                # Redirect outgoing edges from the original operation node to the new condition node
                original_outgoing_edges = [edge for edge in new_edges if edge['from'] == node_id]
                new_edges = [edge for edge in new_edges if edge not in original_outgoing_edges]

                # Add 'yes' edge from the condition node to the operation node
                new_edges.append({'from': new_cond_id, 'to': node_id, 'label': 'yes'})

                # Reconnect the original outgoing edges from the operation node
                for edge in original_outgoing_edges:
                    new_edges.append({'from': node_id, 'to': edge['to'], 'label': edge.get('label')})

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
    合并流程图中具有相同类型和标签的重复节点（包括条件节点），并移除重复的连接线和自循环连接。

    参数:
        flowchart_str (str): 原始的流程图定义字符串。

    返回:
        str: 处理后的流程图定义字符串。
    """
    # 分离节点定义和连接
    lines = flowchart_str.strip().split('\n')
    node_definitions = {}
    connections = []
    node_pattern = re.compile(r'^(\w+)=>(\w+):\s*(.+)$')
    connection_pattern = re.compile(r'^(\w+)(\([\w\s]+\))?->(\w+)$')

    for line in lines:
        node_match = node_pattern.match(line)
        if node_match:
            node_id, node_type, label = node_match.groups()
            node_definitions[node_id] = (node_type.strip().lower(), label.strip())
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

    # 更新连接，并移除重复的连接线和自循环连接
    updated_connections = []
    unique_connections = set()

    for conn in connections:
        conn_match = connection_pattern.match(conn)
        if not conn_match:
            continue  # 跳过不符合格式的连接

        from_node = conn_match.group(1)
        condition = conn_match.group(2) if conn_match.group(2) else ''
        to_node = conn_match.group(3)

        # 替换节点ID
        from_node_replaced = node_mapping.get(from_node, from_node)
        to_node_replaced = node_mapping.get(to_node, to_node)

        # 重新构建连接
        updated_conn = f"{from_node_replaced}{condition}->{to_node_replaced}"

        # 标准化连接线格式（去除多余空格）
        updated_conn = re.sub(r'\s+', ' ', updated_conn)

        # 跳过自循环连接
        if from_node_replaced == to_node_replaced:
            continue

        # 使用元组跟踪唯一连接
        connection_key = (from_node_replaced, condition, to_node_replaced)
        if connection_key not in unique_connections:
            unique_connections.add(connection_key)
            updated_connections.append(updated_conn)

    # 构建条件节点的分支映射
    condition_targets = defaultdict(dict)  # {condition_node: {'yes': target, 'no': target}}

    connection_label_pattern = re.compile(r'^(\w+)\((yes|no)\)->(\w+)$')
    for conn in updated_connections:
        conn_match = connection_label_pattern.match(conn)
        if conn_match:
            from_node, label, to_node = conn_match.groups()
            if label in ['yes', 'no']:
                condition_targets[from_node][label] = to_node

    # 递归解析目标节点，确保条件节点不指向其他条件节点
    def resolve_target(node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited:
            return node_id  # 防止无限循环
        visited.add(node_id)

        node_type, label = node_definitions.get(node_id, (None, None))
        if node_type != 'condition':
            return node_id
        targets = condition_targets.get(node_id, {})
        resolved_targets = {}
        for branch, target in targets.items():
            final_target = resolve_target(target, visited)
            resolved_targets[branch] = final_target
        # 更新条件节点的目标
        condition_targets[node_id] = resolved_targets
        return node_id

    # 解析所有条件节点的最终目标
    for condition_node in condition_targets:
        resolve_target(condition_node)

    # 重新构建最终的连接关系
    final_connections = []
    unique_final_connections = set()

    for condition_node, branches in condition_targets.items():
        for branch, target in branches.items():
            final_conn = f"{condition_node}({branch})->{target}"
            if (condition_node, branch, target) not in unique_final_connections:
                unique_final_connections.add((condition_node, branch, target))
                final_connections.append(final_conn)

    # 包含非条件的连接（如开始到输入，操作到下一个节点）
    non_condition_connections = []
    for conn in updated_connections:
        if not connection_label_pattern.match(conn):
            non_condition_connections.append(conn)

    # 合并非条件连接和条件连接
    final_connections = non_condition_connections + final_connections

    # 移除重复的连接
    final_connections = list(dict.fromkeys(final_connections))

    # 生成新的节点定义，排除重复节点
    unique_nodes = {nid: info for nid, info in node_definitions.items() if nid not in node_mapping}

    # 按照原始顺序重新排列节点定义
    node_order = []
    for line in lines:
        node_match = node_pattern.match(line)
        if node_match:
            node_id = node_match.group(1)
            if node_id in unique_nodes and node_id not in node_order:
                node_order.append(node_id)

    # 生成新的流程图行
    new_flowchart_lines = []
    for node_id in node_order:
        node_type, label = unique_nodes[node_id]
        new_flowchart_lines.append(f"{node_id}=>{node_type}: {label}")

    # 添加最终的连接线
    new_flowchart_lines.extend(final_connections)

    return '\n'.join(new_flowchart_lines)


def parse_flowchart_continue(flowchart_code):
    """
    解析流程图代码，找到所有的 continue 节点，并将它们连接到对应的循环条件节点。
    同时保留原始边上的条件标签（如 yes、no）。

    参数:
    flowchart_code (str): 流程图的代码字符串。

    返回:
    str: 修改后的流程图代码，节点先定义，边后定义，并保留边上的条件标签。
    """
    from collections import deque, defaultdict
    import re

    nodes = {}
    edges = []
    edge_set = set()  # 用于避免重复的边

    # 正则表达式匹配带条件的边，例如 cond12741(yes)->op12769
    edge_pattern = re.compile(r'(\w+)(\(([^)]+)\))?->(\w+)')

    # 分析每一行，区分节点和边
    for line in flowchart_code.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue  # 忽略空行和注释
        if '=>' in line:
            # 节点定义
            parts = line.split('=>', 1)
            node_id = parts[0].strip()
            rest = parts[1].strip()
            if ':' in rest:
                node_type, label = rest.split(':', 1)
                nodes[node_id] = {'type': node_type.strip(), 'label': label.strip()}
        elif '->' in line:
            # 边定义
            match = edge_pattern.match(line)
            if match:
                from_node = match.group(1).strip()
                label = match.group(3).strip() if match.group(3) else None
                to_node = match.group(4).strip()
                edges.append({'from': from_node, 'to': to_node, 'label': label})
                edge_set.add((from_node, to_node, label))

    # 构建反向邻接表，用于从子节点追溯到父节点
    reverse_adj = defaultdict(list)
    for edge in edges:
        reverse_adj[edge['to']].append(edge['from'])

    # 识别循环条件节点（以 for 或 while 开头的条件节点）
    loop_conditions = [
        node_id for node_id, node in nodes.items()
        if node['type'] == 'condition' and (node['label'].startswith('for') or node['label'].startswith('while'))
    ]

    # 识别所有的 continue 节点
    continue_nodes = [
        node_id for node_id, node in nodes.items()
        if node['label'] == 'continue'
    ]

    # 为每个 continue 节点找到最近的循环条件节点，并添加边连接
    for cont_node in continue_nodes:
        visited = set()
        queue = deque()
        queue.append(cont_node)
        found = None
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if current in loop_conditions:
                found = current
                break
            # 通过反向邻接表遍历父节点
            for parent in reverse_adj.get(current, []):
                if parent not in visited:
                    queue.append(parent)
        if found:
            # 添加新边，且不重复
            new_edge = {'from': cont_node, 'to': found, 'label': None}
            if (new_edge['from'], new_edge['to'], new_edge['label']) not in edge_set:
                edges.append(new_edge)
                edge_set.add((new_edge['from'], new_edge['to'], new_edge['label']))

    # 将节点和边转换回流程图代码的格式
    nodes_output = []
    edges_output = []

    # 首先输出节点，保持输入顺序
    for line in flowchart_code.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=>' in line:
            node_id = line.split('=>', 1)[0].strip()
            if node_id in nodes:
                node = nodes[node_id]
                nodes_output.append(f"{node_id}=>{node['type']}: {node['label']}")

    # 然后输出边，保持输入顺序，并保留条件标签
    for line in flowchart_code.splitlines():
        line = line.strip()
        if '->' in line:
            match = edge_pattern.match(line)
            if match:
                from_node = match.group(1).strip()
                label = match.group(3).strip() if match.group(3) else None
                to_node = match.group(4).strip()
                # 查找对应的边并保留标签
                for edge in edges:
                    if edge['from'] == from_node and edge['to'] == to_node and edge['label'] == label:
                        if label:
                            edges_output.append(f"{from_node}({label})->{to_node}")
                        else:
                            edges_output.append(f"{from_node}->{to_node}")
                        break

    # 添加新添加的边（从 continue 到循环条件），不保留标签
    for edge in edges:
        if edge['from'] in continue_nodes and edge['to'] in loop_conditions:
            # 检查是否已经在输出中定义
            exists = False
            for existing_edge in edges_output:
                # 解析 existing_edge 来比较
                existing_match = edge_pattern.match(existing_edge)
                if existing_match:
                    existing_from = existing_match.group(1).strip()
                    existing_to = existing_match.group(4).strip()
                    existing_label = existing_match.group(3).strip() if existing_match.group(3) else None
                    if existing_from == edge['from'] and existing_to == edge['to'] and existing_label == edge['label']:
                        exists = True
                        break
            if not exists:
                # 添加无标签的边
                edges_output.append(f"{edge['from']}->{edge['to']}")

    # 移除可能的重复边
    edges_output = list(dict.fromkeys(edges_output))

    # 合并节点和边输出
    final_output = '\n'.join(nodes_output + edges_output)

    return final_output

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


import requests
import json




def get_access_token():
    API_KEY = "J0EyTqLEd1mQEYGlwzbdodsX"
    SECRET_KEY = "5NYhOTuvNhjktqXFgDsCnYOImxRK8stg"

    """
    使用 API Key，Secret Key 获取 access_token。
    """
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + API_KEY + "&client_secret=" + SECRET_KEY

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.post(url, headers=headers)
    return response.json().get("access_token")


def get_response(content):
    """
    输入内容 content，构造 payload，发送请求，并返回响应中的 result 字段。
    """
    access_token = get_access_token()
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token=" + access_token

    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    })

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)

    # 将返回的文本转为 JSON 并提取 result 字段
    response_json = response.json()  # 将返回结果转为 JSON 格式
    result = response_json.get("result")  # 获取 result 字段

    return result

code = """
def check_age():
    i=1
    while(i<10 and j>0):
        i+=1
    return i
"""

# 转换代码
transformed_code_step1 = transform_code(code)

# 生成初始的流程图代码
flowchart_code_step2 = generate_flowchart_from_code(transformed_code_step1)

# 处理包含 elif 的部分
processed_code_step3 = process_flowchart(flowchart_code_step2)

# 处理 continue 语句
processed_code_step4 = parse_flowchart_continue(processed_code_step3)

# 处理 break 语句
output_code_step5 = modify_flowchart_code(processed_code_step4)

# 统一并连接到 end 节点
output_code_step6 = unify_end_node(output_code_step5)

# 合并重复的节点和删除重复的连接，处理嵌套的 or 条件
final_output_code_step7 = merge_duplicate_nodes_and_remove_duplicate_connections(output_code_step6)

print(transformed_code_step1)
print()
print(flowchart_code_step2)

# generate_and_save_flowchart(flowchart_code_step2)