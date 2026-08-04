from rest_framework.exceptions import APIException

class DashboardException(APIException):
    status_code = 400
    default_detail = "A dashboard operation failed."
    default_code = "dashboard_error"

class DashboardDataFetchException(DashboardException):
    status_code = 500
    default_detail = "Failed to fetch dashboard data."
    default_code = "dashboard_fetch_error"
