
from django.contrib.auth.models import AnonymousUser
import json
from collections import OrderedDict
from rest_framework_simplejwt.exceptions import TokenError
from django.http import HttpRequest, HttpResponse
from app.models import Profile
import cProfile
import pstats
import io

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
        # path = (request.get_full_path())
        # print(path)
        to_profile = request.GET.get('prof', False) == ""
        if to_profile:
            # print("profiling")
            profiler = cProfile.Profile()
            profiler.enable()

        exempt = True
        # for url in AUTH_EXEMPT:
        if request.path.startswith('/api/auth'):
            exempt = False
                # break

        resp_data = {
            "refreshed": False,
            "loggedIn":False
        }
        if not exempt:
            token = None
            user = None
            try:
                user = PetrichorAuthenticator.authenticate(request)  # type: ignore
                resp_data:dict = {
                    "loggedIn":False
                }
                if user is not None:  # If we got some data here, then user is already authorized
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
                    "status":403
                }
                # if user is not logged then returning the response from here only. 
                # The request does goes further to any middleware or the target view
                return HttpResponse(json.dumps(resp_data),content_type='application/json',status=403)
            resp_data['access'] = token 
            if not resp_data['loggedIn'] or user is None:
                resp_data.update({
                    "success":False,
                    "message":"Not Logged in",
                    "status":403
                })
                # if user is not logged then returning the response from here only. 
                # The request does goes further to any middleware or the target view
                return HttpResponse(json.dumps(resp_data),content_type='application/json',status=403)

            '''
            No need to check for verified or not If user is able to login then he must have already been verified
            Otherwise the login request would have failed and user would have not got the access token
            But since user got one, so he is surely verified
            
            '''
            

        response:HttpResponse = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.


        if to_profile:
            # print("profiling")
            profiler.disable()
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats(10)  # Adjust the number of lines to print if needed

            profiling_data = stream.getvalue().replace("\n", "<br>").replace(" ", "&nbsp;")
            print("profile data",profiling_data)
            html_template = f"""
                <html>
                <head>
                    <title>Profiling Data</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.5; }}
                        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
                        h1 {{ color: #333; }}
                    </style>
                </head>
                <body>
                    <h1>Profiling Data</h1>
                    <pre>{profiling_data}</pre>
                </body>
                </html>
                """
            response.content = html_template.encode('utf-8')
            response['Content-Type'] = 'text/html'
            response.status_code = 200

            return response

        # if everything went correctly then we will append the log in details with the response
        if not exempt and hasattr(response,'data'):
            resp_data.update((response.data)) # type: ignore
            response.data = resp_data # type: ignore
            response.content = json.dumps(response.data) # type: ignore
        # print(response.content)
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