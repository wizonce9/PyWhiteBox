from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from graphviz import Digraph
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

LATEST_IMAGE_FILE = 'test_cases.json'

@app.route('/api/process_code', methods=['POST'])
def process_code():
    data = request.get_json()
    code = data.get('code', '')
    option = data.get('option', 'option1')

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    # Mock processing based on the option
    test_cases = generate_test_cases(code, option)

    # Generate a flowchart image
    flowchart_path = generate_flowchart(code)

    # Save the latest image path
    save_latest_image(flowchart_path)

    return jsonify({'testCases': test_cases}), 200

def generate_test_cases(code, option):
    # This is a mock function. Replace with actual test case generation logic.
    if option == 'option1':
        return [
            {'inputs': {'a': 1, 'b': 2}, 'conditions': 'a > 0'},
            {'inputs': {'a': -1, 'b': 3}, 'conditions': 'a <= 0'}
        ]
    elif option == 'option2':
        return [
            {'inputs': {'x': 10}, 'conditions': 'x > 5'},
            {'inputs': {'x': 5}, 'conditions': 'x == 5'},
            {'inputs': {'x': 0}, 'conditions': 'x < 5'}
        ]
    elif option == 'option3':
        # Example GPT-based test cases
        return [
            {'inputs': {'input1': 'test'}, 'conditions': 'input1 contains "test"'},
            {'inputs': {'input1': ''}, 'conditions': 'input1 is empty'}
        ]
    else:
        return []

def generate_flowchart(code):
    # Create a unique filename
    filename = f"flowchart_{uuid.uuid4().hex}.png"
    filepath = os.path.join('generated_images', filename)

    # Ensure the directory exists
    os.makedirs('generated_images', exist_ok=True)

    # Create a simple flowchart
    dot = Digraph(comment='Flowchart')

    # Mock parsing: In reality, you'd parse the code to create nodes and edges
    dot.node('A', 'Start')
    dot.node('B', 'Process')
    dot.node('C', 'End')

    dot.edges(['AB', 'BC'])

    # Render the flowchart to a PNG file
    dot.render(filename=filename, directory='generated_images', format='png', cleanup=True)

    return filepath

def save_latest_image(image_path):
    data = {'latestImagePath': image_path}
    with open(LATEST_IMAGE_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/api/latest_image', methods=['GET'])
def get_latest_image():
    if not os.path.exists(LATEST_IMAGE_FILE):
        return jsonify({'error': 'No image available'}), 404

    with open(LATEST_IMAGE_FILE, 'r') as f:
        data = json.load(f)

    return jsonify({'latestImagePath': data.get('latestImagePath', '')}), 200

# Serve images from the generated_images directory
@app.route('/generated_images/<path:filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory('generated_images', filename)

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('generated_images', exist_ok=True)
    app.run(debug=True)
