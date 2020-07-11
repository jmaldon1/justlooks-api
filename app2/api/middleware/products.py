import toolz
import traceback

from flask import request
from functools import wraps
from typing import Union, Callable
from jsonschema import validate, Draft7Validator
from jsonschema.exceptions import ValidationError, ErrorTree

from api.constants import BAD_REQUEST
from api import utils
from api.logger import logger

# ====================
# Middleware
# ====================
def validate_query_params__all_products(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        """
        Validate the query params of all_products route
        """
        validation_errors = []
        try:
            last_id_gt = validate_query_param__last_id_gt(request.args.get("last_id_gt", None))
        except ValueError as e:
            validation_errors.append(e.args[0])

        try:
            per_page = validate_query_param__per_page(request.args.get("per_page", None))
        except ValueError as e:
            validation_errors.append(e.args[0])

        try:
            sort_by = validate_query_param__sort_by(request.args.get("sort_by", None))
        except ValueError as e:
            validation_errors.append(e.args[0])
        
        try:
            color_filter = request.args.get("color", None)
            price_filter = request.args.getlist("price", None)
            filters = validate_query_param__filters(color_filter, price_filter)
        except ValueError as e:
            validation_errors.extend(e.args[0])
        
        if validation_errors:
            validation_failed_error = utils.create_error__typical(1,
                                                                 "Validation Failed",
                                                                 validation_errors,
                                                                 details_name="errors")
            return validation_failed_error, BAD_REQUEST

        return f(last_id_gt, per_page, sort_by, filters, *args, **kwargs)

    return wrap


# ====================
# Logic
# ====================
def validate_query_param__last_id_gt(_last_id_gt: Union[str, None]) -> int:
    try:
        if _last_id_gt is None:
            last_id_gt = -1
        else:
            last_id_gt = utils.__try_number(_last_id_gt)

        schema = {"type": "number"}
        validate(last_id_gt, schema)

        return last_id_gt

    except ValidationError as e:
        err = utils.create_error__validation(2, "last_id_gt", e.message)
        raise ValueError(err)
    except Exception as e:
        logger.error(traceback.format_exc())
        err = utils.create_error__validation(2, "last_id_gt", str(e))
        raise ValueError(err)


def validate_query_param__per_page(_per_page: Union[str, None]) -> int:
    try:
        if _per_page is None:
            per_page = 10
        else:
            per_page = utils.__try_number(_per_page)

        schema = {
            "type": "number",
            "exclusiveMinimum": 0,  # x > 0
            "maximum": 500,  # x <= 500
        }
        validate(per_page, schema)

        return per_page

    except ValidationError as e:
        err = utils.create_error__validation(3, "per_page", e.message)
        raise ValueError(err)
    except Exception as e:
        logger.error(traceback.format_exc())
        err = utils.create_error__validation(3, "per_page", str(e))
        raise ValueError(err)


def validate_query_param__sort_by(_sort_by: Union[str, None]) -> str:
    try:
        if _sort_by is None:
            sort_by = "int_id"
        else:
            sort_by = _sort_by

        schema = {"type": "string"}
        validate(sort_by, schema)

        return sort_by

    except ValidationError as e:
        err = utils.create_error__validation(4, "sort_by", e.message)
        raise ValueError(err)
    except Exception as e:
        logger.error(traceback.format_exc())
        err = utils.create_error__validation(4, "sort_by", str(e))
        raise ValueError(err)


class AllValidationErrors(ValidationError):
    def __init__(self, message, errors):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


def validate_query_param__filters(color: Union[str, None], price: list) -> str:
    try:
        # print(color)
        filters = {
            "color": color,
            "price": price
        }

        price_pattern = r"^(gte|lte|gt|lt)\:(\d+)$|^(\d+)$"
        schema = {
            "type": "object",
            "properties": {
                "color": {"type": ["string", "null"]},
                "price": {
                    "type": "array",
                    "maxItems": 2,
                    "items":{
                        "type": "string",
                        "pattern": price_pattern
                    }
                }
            }
        }

        # validate(filters, schema)
        validator = Draft7Validator(schema)
        errors = validator.iter_errors(filters)
        if errors:
            error_messages = [error for error in errors]
            raise AllValidationErrors("Validation errors", error_messages)

        return filters
    except AllValidationErrors as e:
        all_validation_errors = []
        for error in e.errors:
            full_error = utils.create_error__validation(5,
                                                        next(iter(error.path), None),
                                                        error.message)
            all_validation_errors.append(full_error)
        raise ValueError(all_validation_errors)
    # except ValidationError as e:
    #     # print(type(e))
    #     print(e)
    #     err = utils.create_error__validation(5, "filters", e.message)
    #     raise ValueError(err)
    except Exception as e:
        logger.error(traceback.format_exc())
        err = utils.create_error__validation(5, "filters", str(e))
        raise ValueError(err)
