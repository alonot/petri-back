from rest_framework.response import Response

def r500(msg: str) -> Response:
    return Response({
        'status': 500,
        'message': msg
    })

def r200(msg: str) -> Response:
    return Response({
        'status': 200,
        'message': msg
    })