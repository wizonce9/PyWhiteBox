from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import numpy as np
from topImage import *
from Control_flow import parse_edges_from_output_code, generate_adjacency_matrix, parse_edges
from jjj import Trans, generate_test_cases_from_paths
from nsz import find_linearly_independent_paths
from zzz import get_basic_paths

# 创建 Flask 应用
app = Flask(__name__)

# 设置 CORS 策略
CORS(app, origins=["http://124.70.51.109:8080"], supports_credentials=True)  # 允许该地址的访问，并支持凭证

# 设置限速器
limiter = Limiter(app) # 使用用户的 IP 地址来进行请求限制

# 定义输出目录的绝对路径
OUTPUT_DIR = os.path.abspath(r".\pic_create\output")  # 使用绝对路径
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 设置路由限制，限制每个 IP 地址每分钟最多请求 15 次
@app.route('/api/process_code', methods=['POST'])
@limiter.limit("1 per minute")  # 每分钟最多允许 15 次请求
def process_code():
    data = request.json
    code = data.get('code', '')
    option = data.get('option', 'option1')  # 获取前端传递的选项，默认为 'option1'
    print(f"Received code: {code}")
    print(f"Selected option: {option}")

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    try:
        flowchart_code_step2 = generate_flowchart_from_code(transform_code(code))
        processed_code_step3 = process_flowchart(flowchart_code_step2)
        processed_code_step4 = modify_flowchart(processed_code_step3)
        output_code_step5 = modify_flowchart_code(processed_code_step4)
        output_code_step6 = unify_end_node(output_code_step5)
        final_output_code_step7 = merge_duplicate_nodes_and_remove_duplicate_connections(output_code_step6)
        final_output_code_step7 = remove_false_edges(final_output_code_step7)
        # 生成并保存流程图
        flowchart_filename = 'flowchart_output.png'
        saved_flowchart_path = generate_and_save_flowchart(final_output_code_step7,
                                                           os.path.join(OUTPUT_DIR, flowchart_filename))

        # 获取文件名（用于在Flask中生成相对路径） 
        flowchart_filename = os.path.basename(saved_flowchart_path)

        if option in ['option1', 'option2']:
            edges = parse_edges_from_output_code(final_output_code_step7)
            nodes_cc = parse_edges(edges)
            adjacency_matrix_cc = generate_adjacency_matrix(edges, nodes_cc)
            adjacency_matrix = np.array(adjacency_matrix_cc)
            basic_paths = get_basic_paths(adjacency_matrix, nodes_cc)

            if option == 'option1':
                independent_paths = find_linearly_independent_paths(basic_paths)
                conditions, edges = Trans(final_output_code_step7)
                test_cases = generate_test_cases_from_paths(independent_paths, edges, conditions)
            elif option == 'option2':
                conditions, edges = Trans(final_output_code_step7)
                test_cases = generate_test_cases_from_paths(basic_paths, edges, conditions)

            # 检查是否有“无法解析的值”错误
            error_found = any('无法解析的值' in str(error.get('Error', '')) for error in test_cases)

            if error_found:
                # 如果有错误，返回仅包含图片路径的响应
                return jsonify({
                    'flowchartPath': f'/output/{flowchart_filename}'  # 只返回图片路径
                })
            else:
                # 如果没有错误，返回测试用例和图片路径
                return jsonify({
                    'testCases': test_cases,
                    'flowchartPath': f'/output/{flowchart_filename}'  # 返回测试用例和图片路径
                })
        elif option == 'option3':
            # 仅生成流程图，不生成测试用例
            # 生成文本内容
            answer_str = get_response(
                code + "。请对上代码进行基本路径分析，给每条路径生成测试用例，包括输入数据、预期输出和可能的边界条件，确保每个路径都被覆盖。此外，请分析这些路径中可能存在的异常处理逻辑，并提供相应的测试建议。最终输出的格式一定要美观标准，每一部分间都要换行。")

            return jsonify({
                'flowchartPath': f'/output/{flowchart_filename}',  # 返回相对路径
                'responseText': answer_str
            })

        else:
            return jsonify({'error': 'Invalid option provided'}), 400

    except Exception as e:
        print(f"Error processing code: {e}")
        return jsonify({'error': str(e)}), 500

# 设置用于提供静态文件的路由
@app.route('/output/<filename>')
def serve_flowchart(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # 绑定到所有网络接口
