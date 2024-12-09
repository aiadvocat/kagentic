from flask import Flask, request, jsonify
import re
import math
from shared.db import DatabaseManager
import requests
import time

app = Flask(__name__)

CAPABILITIES = [
    "calculate",
    "math",
    "arithmetic",
    "solve equation",
    "convert units"
]

def extract_numbers(text):
    return [float(num) for num in re.findall(r'-?\d*\.?\d+', text)]

def identify_operation(text):
    text = text.lower()
    if any(word in text for word in ['add', 'sum', 'plus', '+']):
        return 'add'
    if any(word in text for word in ['subtract', 'minus', '-']):
        return 'subtract'
    if any(word in text for word in ['multiply', 'times', '*', 'x']):
        return 'multiply'
    if any(word in text for word in ['divide', '/']):
        return 'divide'
    return None

def perform_calculation(numbers, operation):
    if not numbers:
        return {"error": "No numbers found in the query"}
    
    if operation == 'add':
        return {"result": sum(numbers)}
    elif operation == 'subtract':
        return {"result": numbers[0] - sum(numbers[1:])}
    elif operation == 'multiply':
        result = 1
        for num in numbers:
            result *= num
        return {"result": result}
    elif operation == 'divide':
        try:
            result = numbers[0]
            for num in numbers[1:]:
                result /= num
            return {"result": result}
        except ZeroDivisionError:
            return {"error": "Division by zero"}
    
    return {"error": "Unknown operation"}

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data['query']
    numbers = extract_numbers(query)
    operation = identify_operation(query)
    
    if not operation:
        return jsonify({"error": "Could not identify operation"}), 400
    
    result = perform_calculation(numbers, operation)
    return jsonify(result)

def register_with_agent():
    while True:
        try:
            response = requests.post(
                'http://ai-agent:5000/api/tools/register',
                json={
                    "name": "Calculator Tool",
                    "description": "Performs mathematical calculations including basic arithmetic, unit conversions, and equation solving.",
                    "endpoint_url": "http://calculator-tool:5000/api/calculate",
                    "capabilities": CAPABILITIES
                },
                timeout=5
            )
            if response.status_code == 200:
                print("Successfully registered with AI Agent")
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to register with AI Agent: {e}")
            time.sleep(10)  # Wait before retrying

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Register with the AI Agent on startup
    import threading
    threading.Thread(target=register_with_agent).start()
    
    app.run(host='0.0.0.0', port=5000) 