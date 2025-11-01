from fastapi import HTTPException

from tools.logger_config import logger


class Exceptions:
    @staticmethod
    def general_exception(
        code: int,
        description,
        canRetry: bool = False,
    ):
        logger.error(f"exception: {description}")
        return HTTPException(
            status_code=code,
            detail={
                "message": "An unexpected error has occurred. We are working on it.",
                "description": description,
                "canRetry": canRetry,
            },
        )

    @staticmethod
    def api_key_exception(provider):
        logger.error(f"Invalid API key for {provider}")
        return HTTPException(
            status_code=401,
            detail={
                "message": "We're currently experiencing some downtime. Don't worry, the Niti.ai team is already on it and working to resolve the issue as quickly as possible. Thank you for your patience!",
                "description": f"Invalid API key for {provider}",
                "canRetry": False,
            },
        )

    @staticmethod
    def required_and_type_exception(field, type=None):
        message = f"{field} is required"
        if type is not None:
            message += f" and must be of type {type}"
        logger.error(message)
        return HTTPException(
            status_code=400,
            detail={
                "message": f"We had an error getting the resource: {message}",
                "description": message,
                "canRetry": False,
            },
        )

    @staticmethod
    def json_exception(
        status_code: int = 500, e: Exception = None, canRetry: bool = False
    ):
        logger.error(f"Error parsing JSON: {str(e)}")
        return HTTPException(
            status_code=status_code,
            detail={
                "message": f"Looks like we ran into an unexpected error. {'Please try again.' if canRetry else 'Reach out to the Niti.ai team for assistance.'}",
                "description": f"Couldn't parse JSON: {str(e)}",
                "canRetry": canRetry,
            },
        )

    @staticmethod
    def not_found_exception(resource):
        logger.error(f"{resource} not found")
        return HTTPException(
            status_code=404,
            detail={
                "message": "We had an error getting the resource. We are working on your problem.",
                "description": f"{resource} not found",
                "canRetry": False,
            },
        )