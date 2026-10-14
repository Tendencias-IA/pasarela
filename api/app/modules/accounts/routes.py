"""Public account routes."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.common.errors import InvalidJsonError
from app.common.errors import ValidationError as RequestValidationError
from app.modules.accounts.schemas import RegisterAccountIn, RegisterAccountOut
from app.modules.accounts.service import register_account

blueprint = Blueprint("accounts", __name__, url_prefix="/api/v1/accounts")


@blueprint.post("")
def create_account():  # type: ignore[no-untyped-def]
    try:
        payload = request.get_json(force=False, silent=False)
        data = RegisterAccountIn.model_validate(payload)
    except ValidationError as error:
        errors = [
            {
                "field": str(item["loc"][0]),
                "message": str(item["msg"]).removeprefix("Value error, "),
            }
            for item in error.errors()
        ]
        raise RequestValidationError(errors=errors) from error
    except Exception as error:
        raise InvalidJsonError() from error
    result = register_account(data)
    response = RegisterAccountOut(account_id=result.account_id, balance=result.balance)
    return jsonify(response.response_body()), 201
