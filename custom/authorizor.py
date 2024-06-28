from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request

class PetrichorJWTAuthentication(JWTAuthentication):
    '''
        This acts as a custom Authentication Class which authenticates the user.
        This class overrides the authenticate function to call super.authenticate 
        and catch ONLY "rest_framework_simplejwt.exceptions.InvalidToken" error 
        which is raised if refresh token has expired. This prevent django from 
        automatically sending the response. 
        Our request then reaches the respective function(view) which calls auth 
        and returns customized message accordingly 
    '''
    def authenticate(self, request: Request):
        try:
            return super().authenticate(request)
        except InvalidToken:
            pass 

    def get_header(self, request: Request) -> bytes:
        auth_token = super().get_header(request)
        if "petrichor_auth" in request.META:
            auth_token = request.META['petrichor_auth']
        # print(auth_token)
        return auth_token