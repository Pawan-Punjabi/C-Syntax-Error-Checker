from flask import Flask, render_template, request, jsonify
from checker import find_syntax_errors

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('compiler.html')


@app.route('/docs')
def docs():
    return render_template('docs.html')


@app.route('/api/check', methods=['POST'])
def check_syntax():
    code = request.json.get('code', '')
    if not code:
        return jsonify({'success': False, 'errors': [], 'message': 'No code provided'})

    errors = find_syntax_errors(code)
    return jsonify({
        'success': True,
        'errors': errors,
        'count': len(errors)
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)