# White-Box Testing Tool

<img width="904" alt="微信图片_20241203111841" src="https://github.com/user-attachments/assets/b1427906-60a2-44a0-9344-4d5503342a75">


<img width="905" alt="c06fc96add9dfe357c44505f689dd7d" src="https://github.com/user-attachments/assets/bd5e3432-25dd-4d29-ba69-947e6f9dd198">


## Introduction

**PyWhiteBox** is a web-based tool designed for white-box testing of Python code. Users can simply paste or enter the code to be tested into an input field, select different testing modes (Basic Path Testing, Path Coverage Testing, and Large Model Testing), and automatically generate the corresponding test flowchart and detailed test cases. This significantly improves the efficiency of testing.

The software features a clean and user-friendly interface. The input field allows for easy code pasting, and the mode selection section lets users switch between different testing modes effortlessly. The "Submit" button generates the test results with a single click. Additionally, the software supports saving and deleting test records. Users can view, download, and delete saved records from the list, which is useful for future analysis and comparison.

You can access the application by visiting the webpage: http://124.70.51.109:8080/register.

### Usage:
1. Open the web application in a browser.
2. Paste or input the code you want to test.
3. Select the desired test type.
4. Click "Submit" to generate the test results.

### Example Python Code: 
```python 
def fun(a, b, c, d): 
   if a > 0 or b > 0: 
      if c > 0 or d > 0: 
      print(A) 
   return A 
``` 
### Example Output: 
![image](https://github.com/user-attachments/assets/689b27e9-443c-462a-a003-b34e3a1383b2)

### Important Notes:
- For accurate test case generation, users must ensure that the Python code is correctly formatted and select the appropriate test method.

## Features

The tool provides the following primary functionalities:

1. **Basic Path Testing**: Generates a set of basic paths and their corresponding test cases.
2. **Path Coverage Testing**: Provides test cases to cover all possible execution paths in the code.
3. **Large Model Testing**: Uses AI to generate intelligent test cases based on the provided code.

## Installation & Configuration

### Frontend Configuration

1. Navigate to the `Bai_web` directory and open a terminal (Git Bash recommended).
2. Run the following command to start the frontend server:
   ```bash
   yarn serve
   ```
3. Once the server is running, you can access the application by clicking the provided link.

#### Prerequisites:
- Node.js 16.0.4
- Vue.js 2

### Backend Configuration

1. Navigate to the `Bai_serve` directory and open the file:
   ```
   \demo\src\main\java\com\example\demo\DemoApplication.java
   ```
   Run the file to start the backend server.

2. Import the SQL files from the `sql` folder into phpMyAdmin to configure the database.

### Python Environment Configuration

1. Navigate to the `\BaiHeTest\Software_test\app.py` file and run it.
   
#### Python Environment:
Before running the Python code, ensure the following packages are installed in your virtual environment:

| Package                | Version   |
|------------------------|-----------|
| astor                  | 0.8.1     |
| astunparse             | 1.6.3     |
| blinker                | 1.6.2     |
| Brotli                 | 1.0.9     |
| certifi                | 2024.8.30 |
| chardet                | 5.2.0     |
| charset-normalizer     | 3.3.2     |
| click                  | 8.1.7     |
| colorama               | 0.4.6     |
| Flask                  | 3.0.3     |
| Flask-Cors             | 3.0.10    |
| gmpy2                  | 2.1.2     |
| graphviz               | 0.20.1    |
| idna                   | 3.7       |
| importlib-metadata     | 7.0.1     |
| itsdangerous           | 2.2.0     |
| Jinja2                 | 3.1.4     |
| MarkupSafe             | 2.1.3     |
| mkl-fft                | 1.3.8     |
| mkl-random             | 1.2.4     |
| mkl-service            | 2.4.0     |
| mpmath                 | 1.3.0     |
| numpy                  | 1.24.3    |
| pip                    | 24.2      |
| pyflowchart            | 0.3.1     |
| PySocks                | 1.7.1     |
| requests               | 2.32.3    |
| setuptools             | 75.1.0    |
| six                    | 1.16.0    |
| sympy                  | 1.13.2    |
| urllib3                | 2.2.2     |
| Werkzeug               | 3.0.3     |
| wheel                  | 0.44.0    |
| win-inet-pton          | 1.1.0     |
| zipp                   | 3.17.0    |

## Authors

This tool was developed by **Xinjian Ji** and **Bingqian Wang** from the School of Software and Microelectronics, Peking University.
