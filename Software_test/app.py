from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import numpy as np
from Image import *
from Control_flow import parse_edges_from_output_code, generate_adjacency_matrix, parse_edges
from jjj import Trans, generate_test_cases_from_paths
from nsz import find_linearly_independent_paths
from zzz import get_basic_paths

app = Flask(__name__)
CORS(app)  # 启用 CORS

# 定义输出目录的绝对路径
OUTPUT_DIR = r"D:/2024_Study/2024_9_project_computer/SoftWare_test_1/pic_create/output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


@app.route('/api/process_code', methods=['POST'])
def process_code():
    data = request.json
    code = data.get('code', '')
    option = data.get('option', 'option1')  # 获取前端传递的选项，默认为 'option1'

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    try:
        # 调用已编写的处理代码逻辑
        transformed_code = transform_code(code)
        flowchart_code = generate_flowchart_from_code(transformed_code)
        processed_code = process_flowchart(flowchart_code)
        output_code = modify_flowchart_code(processed_code)
        output_code = unify_end_node(output_code)

        # 生成并保存流程图
        flowchart_filename = os.path.join(OUTPUT_DIR, 'flowchart_output')
        saved_flowchart_path = generate_and_save_flowchart(output_code, flowchart_filename)

        # 获取文件名（用于在Flask中生成相对路径）
        flowchart_filename = os.path.basename(saved_flowchart_path)

        edges = parse_edges_from_output_code(output_code)
        nodes_cc = parse_edges(edges)
        adjacency_matrix_cc = generate_adjacency_matrix(edges, nodes_cc)
        adjacency_matrix = np.array(adjacency_matrix_cc)
        basic_paths = get_basic_paths(adjacency_matrix, nodes_cc)

        # 根据选项执行不同的逻辑
        if option == 'option1':
            independent_paths = find_linearly_independent_paths(basic_paths)
            conditions, edges = Trans(output_code)
            test_cases = generate_test_cases_from_paths(independent_paths, edges, conditions)
            print(test_cases)
        elif option == 'option2':
            conditions, edges = Trans(output_code)
            test_cases = generate_test_cases_from_paths(basic_paths, edges, conditions)
            print(test_cases)
        else:
            return jsonify({'error': 'Invalid option provided'}), 400

        return jsonify({
            'testCases': test_cases,
            'flowchartPath': f'/output/{flowchart_filename}'  # 返回相对路径
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/output/<filename>')
def serve_flowchart(filename):
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/api/latest_image', methods=['GET'])
def get_latest_image():
    # 获取目录下所有png文件
    images = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')]
    print(images)

    if not images:
        return jsonify({'error': 'No images found'}), 404  # 返回404错误并带有错误消息

    # 通过对文件名进行排序来找到序号最大的文件
    images.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]) if x.split('_')[-1].split('.')[0].isdigit() else 0)
    latest_image = images[-1]

    # 构建相对路径以便前端访问
    latest_image_url = f"/{latest_image}"
    print('latestImagePath: ', latest_image_url)
    return jsonify({'latestImagePath': latest_image_url})


if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 修改端口为5001
