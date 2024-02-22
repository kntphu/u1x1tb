from flask import jsonify, abort, Response


class ModelValidationError(Exception):

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
        # todo: return JSON
        abort(Response(message, status=400, mimetype='application/json'))
