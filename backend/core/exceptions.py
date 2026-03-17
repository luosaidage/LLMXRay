from fastapi import HTTPException, status

class TaskNotFoundError(HTTPException):
    def __init__(self, task_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

class TaskNotReadyError(HTTPException):
    def __init__(self, task_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report for task {task_id} is not ready yet"
        )

class APIConnectionError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error connecting to target API: {message}"
        )
