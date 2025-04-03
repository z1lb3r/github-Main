"""
REST API для доступа к базе данных телеграм-бота.
Позволяет получать и модифицировать данные из внешних систем.
"""

from flask import Flask, request, jsonify
import sqlite3
import json
import os
from functools import wraps
from config import SQLITE_DB_PATH, API_SECRET_KEY

app = Flask(__name__)

# Функция для проверки API-ключа
def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_SECRET_KEY:
            return jsonify({"error": "Unauthorized - Invalid API key"}), 401
        return view_function(*args, **kwargs)
    return decorated_function

# Вспомогательная функция для преобразования результатов запроса в список словарей
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Endpoint для выполнения SELECT-запросов
@app.route('/api/query', methods=['POST'])
@require_api_key
def execute_query():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400
    
    query = data['query']
    params = data.get('params', [])
    
    # Проверка, что запрос только SELECT (для безопасности)
    if not query.strip().upper().startswith('SELECT'):
        return jsonify({"error": "Only SELECT queries are allowed through this endpoint"}), 403
    
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint для выполнения модифицирующих запросов (INSERT, UPDATE, DELETE)
@app.route('/api/execute', methods=['POST'])
@require_api_key
def execute_command():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400
    
    query = data['query']
    params = data.get('params', [])
    
    # Проверка, что запрос не SELECT
    if query.strip().upper().startswith('SELECT'):
        return jsonify({"error": "Use /api/query endpoint for SELECT queries"}), 400
    
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return jsonify({
                "success": True,
                "affected_rows": cursor.rowcount
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint для получения метаданных таблиц
@app.route('/api/schema', methods=['GET'])
@require_api_key
def get_schema():
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            cursor = conn.cursor()
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema[table_name] = columns
            
            return jsonify({"schema": schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Запуск сервера
if __name__ == '__main__':
    # Добавляем в config.py переменную API_SECRET_KEY, если ее нет
    app.run(host='0.0.0.0', port=5001)