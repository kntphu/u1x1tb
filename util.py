from marshmallow import Schema, ValidationError

from domain.error import ModelValidationError


def validate_schema(schema: Schema, request):
    js = request.get_json(silent=True)
    data = js['input']
    print(f'event : {data}')
    try:
        return schema.load(data, many=True)
    except ValidationError as err:
        print(err)
        raise ModelValidationError("schema invalid")
