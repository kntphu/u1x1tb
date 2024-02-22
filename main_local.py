#!flask/bin/python
from flask import Flask, make_response, jsonify, request

from main import run_script_general

app = Flask("App")


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({
        'status': "NOT_FOUND",
    }))


@app.route("/run", methods=['POST'])
def run_local():
    result = run_script_general(request)
    return make_response(result)


if __name__ == '__main__':
    app.run(debug=True)
