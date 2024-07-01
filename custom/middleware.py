
from django.contrib.auth.models import AnonymousUser
import json
from collections import OrderedDict
from rest_framework_simplejwt.exceptions import TokenError
from django.http import HttpRequest, HttpResponse

from utils import AUTH_EXEMPT, PetrichorAuthenticator, Refreshserializer
class PetrichorAuthMiddleware(object):
    '''
        This is a custom middleware.
        courtesy:https://stackoverflow.com/questions/18322262/how-to-set-up-custom-middleware-in-django
    '''
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request:HttpRequest):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """
        '''
            This function is called by every request other than /register/ and /login/
            returns a response object as follows:
            {
                loggedIn: True / False  - If False, frontend must direct user to login first
                refreshed: (if the access token is refreshed) True- "In this case frontend must update the access cookie." 
                                                            : False-"No action needed from frontend"
                access: (if refreshed) ? The refreshed token : None;
            }
            NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
        '''
        exempt = False
        for url in AUTH_EXEMPT:
            if request.path.startswith(url):
                exempt = True
                break
        
        if not exempt:
            resp_data = {
                "refreshed": False,
                "loggedIn":False
            }
            token = None
            try:
                user = PetrichorAuthenticator.authenticate(request)
                if user:  # If we got some data here, then user is already authorized
                    resp_data['loggedIn'] = True
                    token = None
                else: 
                    '''
                        removing the concept of refresh token for now
                        To enable this- uncomment below and the above "authenticate" lines, then 
                        put this middleware in the settings 'before' the authorization middleware
                    
                    '''
                    '''
                    # get the refresh token from the cookies
                    refreshToken = request.COOKIES['refresh']
                    # recording the refresh token and sending it to validate
                    req_data = {'refresh' :refreshToken}
                    # validate returns access token or if refresh token is expired/wrong then 
                    # raises Token Error
                    token = Refreshserializer.validate((OrderedDict)(req_data))['access']
                    # adding this token to META from where it is used by Auth middleware later
                    request.META['petrichor_auth'] = bytes('Bearer ' + token,'utf-8')
                    resp_data['loggedIn'] = True
                    resp_data['refreshed'] = True
                    '''
                    pass
            except TokenError:
                token = None
            except KeyError:
                resp_data = {
                    "success":False,
                    "message":"Refresh token not present",
                    "status":400
                }
                # if user is not logged then returning the response from here only. 
                # The request does goes further to any middleware or the target view
                return HttpResponse(json.dumps(resp_data),content_type='application/json',status=400)
            resp_data['access'] = token
            if not resp_data['loggedIn']:
                resp_data.update({
                    "success":False,
                    "message":"Not Logged in",
                    "status":400
                })
                # if user is not logged then returning the response from here only. 
                # The request does goes further to any middleware or the target view
                return HttpResponse(json.dumps(resp_data),content_type='application/json',status=400)
            



        response:HttpResponse = self.get_response(request)
        
        # Code to be executed for each request/response after
        # the view is called.

        # if everything went correctly then we will append the log in details with the response
        if not exempt and hasattr(response,'data'):
            resp_data.update((response.data))
            response.data = resp_data
            response.content = json.dumps(response.data)

        return response

    def process_view(self, request:HttpRequest, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        """
        return None

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        return None

    def process_template_response(self, request, response):
        """
        Called just after the view has finished executing.
        """
        return response