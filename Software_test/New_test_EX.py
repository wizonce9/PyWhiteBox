import itertools

def generate_test_cases(basic_paths, conditions):
    test_cases = []
    for path in basic_paths:
        test_case = {}
        for node in path:
            if node in conditions:
                # 这里我们处理条件
                condition = conditions[node]
                variable, operator, value = parse_condition(condition)
                if variable not in test_case:
                    test_case[variable] = []
                if operator == '<':
                    test_case[variable].append(float(value) - 1)
                elif operator == '<=':
                    test_case[variable].append(float(value))
                elif operator == '>':
                    test_case[variable].append(float(value) + 1)
                elif operator == '>=':
                    test_case[variable].append(float(value))
                elif operator == '==':
                    test_case[variable].append(float(value))
                elif operator == '!=':
                    test_case[variable].append(float(value) + 1)
        # 每个变量可能有多个可行的值，我们选择组合所有的值
        all_combinations = itertools.product(*test_case.values())
        for combination in all_combinations:
            test_case_values = dict(zip(test_case.keys(), combination))
            test_cases.append(test_case_values)
    return test_cases

def parse_condition(condition):
    for operator in ['<=', '>=', '<', '>', '==', '!=']:
        if operator in condition:
            variable, value = condition.split(operator)
            return variable.strip(), operator.strip(), value.strip()
    raise ValueError(f"无法解析的条件: {condition}")

# 示例条件
conditions = {
    1: "age < 0",
    3: "age <= 18",
    6: "age <= 50"
}

# 示例基本路径
basic_paths = [
    [0, 1, 2, 4],
    [0, 1, 3, 5, 4],
    [0, 1, 3, 6, 7, 4],
    [0, 1, 3, 6, 8, 4]
]


test_cases = generate_test_cases(basic_paths, conditions)

print("生成的测试用例:")
for i, test_case in enumerate(test_cases, 1):
    print(f"Test Case {i}: {test_case}")
