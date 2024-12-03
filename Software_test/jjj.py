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
                next_node = path[i + 1] if i + 1 < len(path) else None

                if next_node:
                    # 构造边的键
                    edge_key_yes = f"{node}(yes)->{next_node}"
                    edge_key_no = f"{node}(no)->{next_node}"
                    condition = conditions.get(node, None)
                    if condition:
                        try:
                            parsed_condition = parse_condition(condition)
                        except ValueError as ve:
                            test_cases.append({
                                "Error": str(ve),
                                "Path": path
                            })
                            break

                        # 根据边的存在情况决定条件
                        if edge_key_yes in edges:
                            # 走 'yes' 分支，条件为真
                            case_conditions.append((*parsed_condition, 'True'))
                        elif edge_key_no in edges:
                            # 走 'no' 分支，条件为假
                            case_conditions.append((*parsed_condition, 'False'))
                        else:
                            test_cases.append({
                                "Error": f"边 {edge_key_yes} 或 {edge_key_no} 未找到。",
                                "Path": path
                            })
                            break

        # 根据汇总的条件生成测试用例
        if not any("Error" in tc for tc in test_cases[-1:]):  # Only check the last-added test case
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
    或者仅有变量时，返回布尔值 ('age', 'bool', None)
    """
    # Remove 'if', parentheses, and extra whitespace
    condition = condition.replace("if", "").replace("(", "").replace(")", "").strip()

    # Define supported operators
    operators = ['<=', '>=', '==', '!=', '<', '>']
    for op in operators:
        if op in condition:
            parts = condition.split(op)
            if len(parts) == 2:
                variable = parts[0].strip()
                value_str = parts[1].strip()
                match = re.match(r'^-?\d+(\.\d+)?$', value_str)
                if match:
                    value = float(value_str) if '.' in value_str else int(value_str)
                else:
                    raise ValueError(f"无法解析的值: {value_str} 在条件: {condition}")
                return variable, op, value

    # If no operator is found, treat as boolean
    return condition, 'bool', None


def create_case_from_conditions(conditions):
    """
    根据条件集合生成测试用例输入。
    条件的格式为 (variable, operator, value, branch)
    branch 为 'True' 表示条件为真，'False' 表示条件为假
    """
    variables_constraints = {}

    for variable, operator, value, branch in conditions:
        if operator == 'bool':
            # Randomly assign True or False for boolean variables
            test_case_value = random.choice([True, False]) if branch == 'True' else random.choice([False, True])
            variables_constraints[variable] = test_case_value
            continue

        if variable not in variables_constraints:
            variables_constraints[variable] = []

        if branch == 'True':
            constraint = (operator, value)
        else:
            inverse_operator = get_inverse_operator(operator)
            constraint = (inverse_operator, value)

        variables_constraints[variable].append(constraint)

    test_case = {}
    for variable, constraints in variables_constraints.items():
        if isinstance(constraints, bool):  # Handle boolean directly
            test_case[variable] = constraints
        else:
            allowed_range = compute_allowed_range(constraints)
            if allowed_range is None:
                raise ValueError(f"无法找到满足所有条件的范围: {constraints}")
            min_val, max_val = allowed_range
            if min_val == float('-inf'):
                min_val = -1000
            if max_val == float('inf'):
                max_val = 1000
            if isinstance(min_val, int) and isinstance(max_val, int):
                if min_val > max_val:
                    raise ValueError(f"对于变量 '{variable}'，最小值 {min_val} 大于最大值 {max_val}。")
                selected_value = random.randint(int(min_val), int(max_val))
            else:
                selected_value = round(random.uniform(float(min_val), float(max_val)), 2)
            test_case[variable] = selected_value

    return test_case


def compute_allowed_range(constraints):
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
            if value >= min_val and value < max_val:
                min_val = value + 1
            else:
                min_val = max(min_val, value - 1)
        else:
            raise ValueError(f"不支持的运算符: {operator}")

    if min_val > max_val:
        return None
    return (min_val, max_val)


def format_conditions(conditions):
    formatted = []
    for variable, operator, value, branch in conditions:
        if operator == 'bool':
            condition_str = f"{variable} 为 {'True' if branch == 'True' else 'False'}"
        elif branch == 'True':
            condition_str = f"{variable} {operator} {value}"
        else:
            inverse_operator = get_inverse_operator(operator)
            condition_str = f"{variable} {inverse_operator} {value}"
        formatted.append(condition_str)
    return formatted


def get_inverse_operator(operator):
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

# 示例条件和边界
def Trans(output_code):
    conditions = {}
    edges = []

    # Split the code lines
    lines = output_code.strip().splitlines()

    # Parse each line
    for line in lines:
        if '=>' in line:
            # Handle node definitions
            node, definition = line.split('=>')
            node_type, content = definition.split(': ', 1)

            # Only extract condition type nodes
            if node_type == 'condition':
                condition_statement = content.strip()
                conditions[node.strip()] = condition_statement

        elif '->' in line:
            # Handle edge definitions
            edges.append(line.strip())

    return conditions, edges

# Example usage (for testing purposes):
# conditions, edges = Trans(output_code)
# random.seed(42)
# test_cases = generate_test_cases_from_paths(paths, edges, conditions)
# for i, case in enumerate(test_cases):
#     print(f"测试用例 {i + 1}:")
#     if "Error" in case:
#         print(f"  错误: {case['Error']}")
#         print(f"  路径: {case['Path']}")
#     else:
#         print(f"  输入: {case['inputs']}")
#         print(f"  条件: {case['conditions']}")
#     print()
