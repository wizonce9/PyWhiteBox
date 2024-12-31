import re
import random
def generate_test_cases_from_paths(paths, edges, conditions):
    random.seed(42)
    test_cases = []

    for path in paths:
        case_conditions = []
        case_inputs = {}
        for i, node in enumerate(path):
            if node.startswith('cond'):
                # 查找条件节点的下一个节点
                if i + 1 < len(path):
                    next_node = path[i + 1]
                else:
                    next_node = None

                if next_node:
                    # 构造边的键
                    edge_key_yes = f"{node}(yes)->{next_node}"
                    edge_key_no = f"{node}(no)->{next_node}"
                    condition = conditions.get(node, None)
                    if condition:
                        try:
                            variable, operator, value = parse_condition(condition)
                        except ValueError as ve:
                            test_cases.append({
                                "Error": str(ve),
                                "Path": path
                            })
                            break

                        # 根据边的存在情况决定条件
                        if edge_key_yes in edges:
                            # 走 'yes' 分支，条件为真
                            case_conditions.append((variable, operator, value, 'True'))
                        elif edge_key_no in edges:
                            # 走 'no' 分支，条件为假
                            case_conditions.append((variable, operator, value, 'False'))
                        else:
                            test_cases.append({
                                "Error": f"边 {edge_key_yes} 或 {edge_key_no} 未找到。",
                                "Path": path
                            })
                            break

        # 根据汇总的条件生成测试用例
        # 只在没有错误的情况下生成测试用例
        if not any("Error" in tc for tc in test_cases[-1:]):  # 只检查最新添加的测试用例
            try:
                case_inputs = create_case_from_conditions(case_conditions)
                test_cases.append({
                    "inputs": case_inputs,
                    "conditions": format_conditions(case_conditions)
                })
            except Exception as e:
                test_cases.append({
                    "Error": str(e),
                    "Path": path
                })

    return test_cases


def parse_condition(condition):
    """
    解析条件表达式，提取变量、运算符和值。
    例如：'if (age < 0)' -> ('age', '<', 0)
    """
    # 去除条件中的 'if' 和括号
    condition = condition.replace("if", "").replace("(", "").replace(")", "").strip()

    # 定义支持的运算符，按照长度降序避免 '<=' 被 '<' 先匹配
    operators = ['<=', '>=', '==', '!=', '<', '>']
    for op in operators:
        if op in condition:
            parts = condition.split(op)
            if len(parts) == 2:
                variable = parts[0].strip()
                value_str = parts[1].strip()
                # 处理可能的负数和小数
                match = re.match(r'^-?\d+(\.\d+)?$', value_str)
                if match:
                    value = float(value_str) if '.' in value_str else int(value_str)
                else:
                    raise ValueError(f"无法解析的值: {value_str} 在条件: {condition}")
                return variable, op, value
    raise ValueError(f"不支持的条件运算符在条件: {condition}")


def create_case_from_conditions(conditions):
    """
    根据条件集合生成测试用例输入。
    条件的格式为 (variable, operator, value, branch)
    branch 为 'True' 表示条件为真，'False' 表示条件为假
    """
    # 假设所有条件作用于同一个变量
    # 如果有多个变量，需要调整此部分逻辑
    variables_constraints = {}

    for variable, operator, value, branch in conditions:
        if variable not in variables_constraints:
            variables_constraints[variable] = []

        # 根据分支状态，转换条件
        if branch == 'True':
            constraint = (operator, value)
        else:
            # 获取反向运算符
            inverse_operator = get_inverse_operator(operator)
            constraint = (inverse_operator, value)

        variables_constraints[variable].append(constraint)

    # 现在为每个变量计算允许的范围
    test_case = {}
    for variable, constraints in variables_constraints.items():
        allowed_range = compute_allowed_range(constraints)
        if allowed_range is None:
            raise ValueError(f"无法找到满足所有条件的范围: {constraints}")
        min_val, max_val = allowed_range
        # 随机选择一个值在 min_val 和 max_val 之间
        # 如果 min_val 是 -inf，设定一个实际的下限
        if min_val == float('-inf'):
            min_val = -1000
        # 如果 max_val 是 +inf，设定一个实际的上限
        if max_val == float('inf'):
            max_val = 1000
        # 随机选择一个整数或浮点数
        if isinstance(min_val, int) and isinstance(max_val, int):
            if min_val > max_val:
                raise ValueError(f"对于变量 '{variable}'，最小值 {min_val} 大于最大值 {max_val}。")
            selected_value = random.randint(int(min_val), int(max_val))
        else:
            selected_value = round(random.uniform(float(min_val), float(max_val)), 2)
        test_case[variable] = selected_value

    return test_case


def compute_allowed_range(constraints):
    """
    根据一组约束条件，计算变量允许的最小值和最大值。
    约束的格式为 (operator, value)
    返回一个元组 (min_val, max_val)
    """
    min_val = float('-inf')
    max_val = float('inf')

    for operator, value in constraints:
        if operator == '<':
            if value - 1 < max_val:
                max_val = value - 1
        elif operator == '<=':
            if value < max_val:
                max_val = value
        elif operator == '>':
            if value + 1 > min_val:
                min_val = value + 1
        elif operator == '>=':
            if value > min_val:
                min_val = value
        elif operator == '==':
            min_val = value
            max_val = value
        elif operator == '!=':
            # 对于 '!=', 需要特殊处理，这里简单地选择 value + 1 或 value - 1
            # 更复杂的处理需要考虑范围和其他条件
            if value >= min_val and value < max_val:
                # Preferably, choose value + 1 within the range
                min_val = value + 1
            else:
                min_val = max(min_val, value - 1)
        else:
            raise ValueError(f"不支持的运算符: {operator}")

    # 检查是否有冲突
    if min_val > max_val:
        return None

    return (min_val, max_val)


def format_conditions(conditions):
    """
    将条件集合格式化为易读的字符串形式，不包含 True/False。
    """
    formatted = []
    for variable, operator, value, branch in conditions:
        if branch == 'True':
            condition_str = f"{variable} {operator} {value}"
        else:
            # 生成条件的反向
            inverse_operator = get_inverse_operator(operator)
            condition_str = f"{variable} {inverse_operator} {value}"
        formatted.append(condition_str)
    return formatted


def get_inverse_operator(operator):
    """
    获取运算符的反向操作符。
    """
    inverse_map = {
        '<': '>=',
        '<=': '>',
        '>': '<=',
        '>=': '<',
        '==': '!=',
        '!=': '=='
    }
    return inverse_map.get(operator, '!=')


# 示例路径
paths = [
    ['io5', 'cond9', 'op13', 'io43'],
    ['io5', 'cond9', 'cond18', 'op22', 'io43'],
    ['io5', 'cond9', 'cond18', 'cond27', 'op31', 'io43'],
    ['io5', 'cond9', 'cond18', 'cond27', 'op35', 'io43']
]
def Trans(output_code):
    conditions = {}
    edges = []

    # 分割代码行
    lines = output_code.strip().splitlines()

    # 解析每一行
    for line in lines:
        if '=>' in line:
            # 处理节点定义
            node, definition = line.split('=>')
            node_type, content = definition.split(': ', 1)

            # 仅提取condition类型的节点
            if node_type == 'condition':
                condition_statement = content.strip()
                # 将条件加入conditions字典
                conditions[node.strip()] = condition_statement

        elif '->' in line:
            # 处理边的表示
            edges.append(line.strip())

    return conditions, edges

# # 调用函数
# conditions, edges = Trans(output_code)
#
# # 设置随机种子以保证可重复性（可选）
# random.seed(42)
#
# # 生成测试用例
# test_cases = generate_test_cases_from_paths(paths, edges, conditions)
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
