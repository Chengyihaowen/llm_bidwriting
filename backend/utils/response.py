from flask import jsonify

def success(data=None, message='success'):
    return jsonify({'code': 0, 'message': message, 'data': data})

def error(message, code=400, error_code=None):
    return jsonify({'code': error_code or -1, 'message': message, 'data': None}), code
