from flask import (
    make_response,
    jsonify,
)


class Response:
    @staticmethod
    def create(message: str, status_code: int):
        return make_response(
            jsonify(
                {
                    "message": message,
                }
            ),
            status_code,
        )
