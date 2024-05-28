import datetime

from flask import jsonify


class ApiResponse:
    """
    Instantiate object with parameters,
    return the jsonified dictionnary as a response as expected by an api request
    """

    _response = {
        "status": "success",
        "data": {
            "paper_id": None,
            "task_status": None,
            "task_elapsed": None,
            "task_started": None,
            "cat_is_processed": None,
            "message": None,
            "alt_message": None,
        },
    }

    def __init__(
        self,
        status: str = None,
        paper_id: int = None,
        task_status: str = None,
        task_elapsed: str = None,
        task_started: datetime = None,
        cat_is_processed: bool = None,
        message: str = None,
        alt_message: str = None,
    ):
        if task_started is not None:
            task_started_str = task_started.strftime("%a, %b %d, %Y - %H:%M:%S")
        else:
            task_started_str = ""
        self._response = {
            "status": status,
            "data": {
                "paper_id": paper_id,
                "task_status": task_status,
                "task_elapsed": task_elapsed,
                "task_started": task_started_str,
                "cat_is_processed": cat_is_processed,
                "message": message,
                "alt_message": alt_message,
            },
        }

    @property
    def response(self):
        import pprint

        return pprint.pformat(self._response)


ar = ApiResponse(status="failed", task_started=datetime.datetime.now())

print(ar.response)
