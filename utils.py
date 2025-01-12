
import json
import smtplib
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner

from django.contrib.auth.models import User
from app.models import Event, Institute, Profile,TransactionTable
from petri_ca import settings
from rest_framework.response import Response 
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from custom.authorizor import PetrichorJWTAuthentication


Refreshserializer = TokenRefreshSerializer()
PetrichorAuthenticator = PetrichorJWTAuthentication()
PetrichroSigner = TimestampSigner(key=settings.FORGET_KEY,salt=settings.FORGET_SALT_KEY)

AUTH_EXEMPT = ['/admin/','/internal/','/api/register/','/api/login/','/api/forget-password/','/api/change-password']
CLOSED_REGISTRATIONS = ['TP06', 'TP07']
# this is not used now.

# Helper functions
def error_response(message):
    return Response({"error": message}, status=500)

def success_response(message):
    return Response({"message": message}, status=200)

def ResponseWithCode(data:dict,message:str,status=200)-> Response:
    '''
        returns a response after appending status and message to its data
        as specified in readme.md
    '''
    data.update({
        "status":status,
        "message":message
    })
    return Response(data,status)

def has_duplicate(strings): 
  seen = set()
  for string in strings:
      if string in seen:
          return True
      seen.add(string)
  return False

def r500(msg: str) -> Response:
    return Response({
        "success":False,
        'status': 500,
        'message': msg
    },500)

def r200(msg: str) -> Response:
    return Response({
        'status': 200,
        'message': msg
    },200)

def send_error_mail(name, data, e):
    '''
        Sends a mail to website developers
    '''
    if "password" in data.keys():
        data["password"]=""
    try:
      send_mail(f'Website Error in: {name}',
                  message= f'Exception: {e}\nData: {json.dumps(data)}',
                  recipient_list=['112201024@smail.iitpkd.ac.in','112201020@smail.iitpkd.ac.in'],
                  from_email=settings.EMAIL_HOST_USER)
      return ""
    except Exception as e:
        return f"unable to send email {e}"

def get_profile_data(user_profile:Profile):
    '''
        returns the profile data as a dict
        NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
    '''
    user_data = {}
    user_data['username'] = user_profile.username
    user_data['email'] = user_profile.user.get_username()
    user_data['phone'] = user_profile.phone
    user_data['stream'] = user_profile.stream
    user_data['gradYear'] = user_profile.gradYear 
    if user_profile.instituteID:   
      user_data['institute'] = user_profile.instituteID.instiName
    else:
      user_data['institute'] = "No insti"
    return user_data
    
def get_profile_events(user:User):
    '''
        returns the eventIds of events in which this user has registered
        NOTE- Any None handled error raised by this functions is/must be handled by the caller function.
    '''
    events = []
    user_registration = user.userregistrations # type:ignore
    # print(user_registration)
    trIds=TransactionTable.deserialize_emails(user_registration.transactionIds)
    # print(trIds)
    for trId in trIds:
        transaction = TransactionTable.objects.filter(transaction_id = trId, archived = False ).only("event_id", "verified").first()
        if transaction is not None and transaction.event_id:
            events.append({
                "eventId": transaction.event_id.event_id,
                "verified": transaction.verified
            })

    # print(events)
    return events


def method_not_allowed():
    return ResponseWithCode({},"Method Not Allowed.Use Post",405)


def send_forget_password_mail(email , token, name):
    subject = 'Your forget password link'
    message = ForgetPasswordHtml(name, f"{settings.FRONTEND_LINK}/changepassword/{token}/")
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject , "",from_email = email_from , recipient_list=recipient_list,fail_silently=True, html_message=message)
    return True

def send_delete_transaction_mail(email , event_name):
    subject = 'Transaction not verified!'
    message = f'Hi , Your transaction_id is not verified for the event {event_name}. Kindly contact admin of Petrichor.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject , message ,email_from , recipient_list, fail_silently=True)
    return True

def send_event_registration_mail(emails,event,verified):
    subject = 'Petrichor Event: ' + event
    message = (f'''We have received your registration for the event :{event}. Please visit the website for venue and date. You can also contact us here 
      <a href="{settings.FRONTEND_LINK}/contactUs">Contact Us</a>
    ''')
    if not verified:
        message += '<strong>Please note your registration has not been verified by our team till now. We will will verify your payment and mail you a confirmation mail soon.</strong>'
    message +="<br> Thank you for participating in Petrichor'25"
    message = messageUser(" from the Petrichor Team",message)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = emails
    try:
      send_mail(subject , "",from_email = email_from , recipient_list=recipient_list,fail_silently=False, html_message=message)
    except smtplib.SMTPException as e:
        print(e)
        return False
    return True

def send_event_verification_mail(emails, trIds,event):
    subject = 'Petrichor Event: ' + event
    message = (f'''We have <strong>verified</strong> your registration for the event :{event} with given transactionId: {trIds}. Please visit the website for venue and date. You can also contact us here 
      <a href="{settings.FRONTEND_LINK}/contactUs">Contact Us</a>
    ''')
    message +="<br> Thank you for participating in Petrichor'25."
    message = messageUser(" from the Petrichor Team",message)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = emails
    try:
      send_mail(subject , "",from_email = email_from , recipient_list=recipient_list,fail_silently=False, html_message=message)
    except smtplib.SMTPException:
        print(e)
        return False
    return True

def send_event_unverification_mail(emails, trIds,event):
    subject = 'Petrichor Event: ' + event
    message = (f'''We have <strong>unverified and deleted</strong> your registration for the event :{event} with given transactionId: {trIds}. Now, you can re-register for the event. You can also contact us here 
      <a href="{settings.FRONTEND_LINK}/contactUs">Contact Us</a>
    ''')
    message +="<br> Thank you for participating in Petrichor'25."
    message = messageUser(" from the Petrichor Team",message)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = emails
    try:
      send_mail(subject , "",from_email = email_from , recipient_list=recipient_list,fail_silently=False, html_message=message)
    except smtplib.SMTPException:
        print(e)
        return False
    return True

def send_user_verification_mail(email:str,token):
    subject = 'Petrichor \'25 Registration' 
    verification_link = f"{settings.BACKEND_LINK}api/login/verify/{token}/"
    message = (f'''<div>
                <p>We have received a registration request for this email at <a href="{settings.FRONTEND_LINK}">Petrichor25</a>\
                  Please click here to verify your registration <br>
               </p>
               <center><a class="button-green button" style="color:white;" href="{verification_link}">Verify</a></center>
               <p>
                  If above button does not works, you can click on the following link:
                  <a href="{verification_link}">{verification_link}</a>
                  Ignore this message if you don't recognize this request.  
                  You can also contact us here <a href="{settings.FRONTEND_LINK}/contactUs">Contact Us</a>
               </p>
               </div>
    ''')
    message +="<p><br> Thank you for participating in Petrichor'25.</p>"
    message = messageUser(" from the Petrichor Team",message)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    try:
      send_mail(subject , "",from_email = email_from , recipient_list=recipient_list, fail_silently=False, html_message=message)
    except smtplib.SMTPException:
        print(e)
        return False
    return True

def get_forget_token(email):
    return PetrichroSigner.sign(email)

def get_email_from_token(token:str):
    token = PetrichroSigner.unsign(token,max_age=settings.FORGET_TOKEN_MAX_AGE)
    return token

# reference - https://github.com/ActiveCampaign/postmark-templates/blob/main/templates/basic-full/password-reset/content.html
def ForgetPasswordHtml(name,action_url):
    return f'''
    <html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="x-apple-disable-message-reformatting" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title></title>
    <style type="text/css" rel="stylesheet" media="all">
    /* Base ------------------------------ */
    
    @import url("https://fonts.googleapis.com/css?family=Nunito+Sans:400,700&display=swap");
    body {{
      width: 100% !important;
      height: 100%;
      margin: 0;
      -webkit-text-size-adjust: none;
    }}
    
    a {{
      color: #3869D4;
    }}
    
    a img {{
      border: none;
    }}
    
    td {{
      word-break: break-word;
    }}
    
    .preheader {{
      display: none !important;
      visibility: hidden;
      mso-hide: all;
      font-size: 1px;
      line-height: 1px;
      max-height: 0;
      max-width: 0;
      opacity: 0;
      overflow: hidden;
    }}
    /* Type ------------------------------ */
    
    body,
    td,
    th {{
      font-family: "Nunito Sans", Helvetica, Arial, sans-serif;
    }}
    
    h1 {{
      margin-top: 0;
      color: #333333;
      font-size: 22px;
      font-weight: bold;
      text-align: left;
    }}
    
    h2 {{
      margin-top: 0;
      color: #333333;
      font-size: 16px;
      font-weight: bold;
      text-align: left;
    }}
    
    h3 {{
      margin-top: 0;
      color: #333333;
      font-size: 14px;
      font-weight: bold;
      text-align: left;
    }}
    
    td,
    th {{
      font-size: 16px;
    }}
    
    p,
    ul,
    ol,
    blockquote {{
      margin: .4em 0 1.1875em;
      font-size: 16px;
      line-height: 1.625;
    }}
    
    p.sub {{
      font-size: 13px;
    }}
    /* Utilities ------------------------------ */
    
    .align-right {{
      text-align: right;
    }}
    
    .align-left {{
      text-align: left;
    }}
    
    .align-center {{
      text-align: center;
    }}
    
    .u-margin-bottom-none {{
      margin-bottom: 0;
    }}
    /* Buttons ------------------------------ */
    
    .button {{
      background-color: #3869D4;
      border-top: 10px solid #3869D4;
      border-right: 18px solid #3869D4;
      border-bottom: 10px solid #3869D4;
      border-left: 18px solid #3869D4;
      display: inline-block;
      color: #FFF;
      text-decoration: none;
      border-radius: 3px;
      box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16);
      -webkit-text-size-adjust: none;
      box-sizing: border-box;
    }}
    
    .button--green {{
      background-color: #22BC66;
      border-top: 10px solid #22BC66;
      border-right: 18px solid #22BC66;
      border-bottom: 10px solid #22BC66;
      border-left: 18px solid #22BC66;
    }}
    
    .button--red {{
      background-color: #FF6136;
      border-top: 10px solid #FF6136;
      border-right: 18px solid #FF6136;
      border-bottom: 10px solid #FF6136;
      border-left: 18px solid #FF6136;
    }}
    
    @media only screen and (max-width: 500px) {{
      .button {{
        width: 100% !important;
        text-align: center !important;
      }}
    }}
    /* Attribute list ------------------------------ */
    
    .attributes {{
      margin: 0 0 21px;
    }}
    
    .attributes_content {{
      background-color: #F4F4F7;
      padding: 16px;
    }}
    
    .attributes_item {{
      padding: 0;
    }}
    /* Related Items ------------------------------ */
    
    .related {{
      width: 100%;
      margin: 0;
      padding: 25px 0 0 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .related_item {{
      padding: 10px 0;
      color: #CBCCCF;
      font-size: 15px;
      line-height: 18px;
    }}
    
    .related_item-title {{
      display: block;
      margin: .5em 0 0;
    }}
    
    .related_item-thumb {{
      display: block;
      padding-bottom: 10px;
    }}
    
    .related_heading {{
      border-top: 1px solid #CBCCCF;
      text-align: center;
      padding: 25px 0 10px;
    }}
    /* Discount Code ------------------------------ */
    
    .discount {{
      width: 100%;
      margin: 0;
      padding: 24px;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #F4F4F7;
      border: 2px dashed #CBCCCF;
    }}
    
    .discount_heading {{
      text-align: center;
    }}
    
    .discount_body {{
      text-align: center;
      font-size: 15px;
    }}
    /* Social Icons ------------------------------ */
    
    .social {{
      width: auto;
    }}
    
    .social td {{
      padding: 0;
      width: auto;
    }}
    
    .social_icon {{
      height: 20px;
      margin: 0 8px 10px 8px;
      padding: 0;
    }}
    /* Data table ------------------------------ */
    
    .purchase {{
      width: 100%;
      margin: 0;
      padding: 35px 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .purchase_content {{
      width: 100%;
      margin: 0;
      padding: 25px 0 0 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .purchase_item {{
      padding: 10px 0;
      color: #51545E;
      font-size: 15px;
      line-height: 18px;
    }}
    
    .purchase_heading {{
      padding-bottom: 8px;
      border-bottom: 1px solid #EAEAEC;
    }}
    
    .purchase_heading p {{
      margin: 0;
      color: #85878E;
      font-size: 12px;
    }}
    
    .purchase_footer {{
      padding-top: 15px;
      border-top: 1px solid #EAEAEC;
    }}
    
    .purchase_total {{
      margin: 0;
      text-align: right;
      font-weight: bold;
      color: #333333;
    }}
    
    .purchase_total--label {{
      padding: 0 15px 0 0;
    }}
    
    body {{
      background-color: #F2F4F6;
      color: #51545E;
    }}
    
    p {{
      color: #51545E;
    }}
    
    .email-wrapper {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #F2F4F6;
    }}
    
    .email-content {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    /* Masthead ----------------------- */
    
    .email-masthead {{
      padding: 25px 0;
      text-align: center;
    }}
    
    .email-masthead_logo {{
      width: 94px;
    }}
    
    .email-masthead_name {{
      font-size: 16px;
      font-weight: bold;
      color: #A8AAAF;
      text-decoration: none;
      text-shadow: 0 1px 0 white;
    }}
    /* Body ------------------------------ */
    
    .email-body {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .email-body_inner {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
      -premailer-width: 570px;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #FFFFFF;
    }}
    
    .email-footer {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
      -premailer-width: 570px;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      text-align: center;
    }}
    
    .email-footer p {{
      color: #A8AAAF;
    }}
    
    .body-action {{
      width: 100%;
      margin: 30px auto;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      text-align: center;
    }}
    
    .body-sub {{
      margin-top: 25px;
      padding-top: 25px;
      border-top: 1px solid #EAEAEC;
    }}
    
    .content-cell {{
      padding: 45px;
    }}
    /*Media Queries ------------------------------ */
    
    @media only screen and (max-width: 600px) {{
      .email-body_inner,
      .email-footer {{
        width: 100% !important;
      }}
    }}
    
    @media (prefers-color-scheme: dark) {{
      body,
      .email-body,
      .email-body_inner,
      .email-content,
      .email-wrapper,
      .email-masthead,
      .email-footer {{
        background-color: #333333 !important;
        color: #FFF !important;
      }}
      p,
      ul,
      ol,
      blockquote,
      h1,
      h2,
      h3,
      span,
      .purchase_item {{
        color: #FFF !important;
      }}
      .attributes_content,
      .discount {{
        background-color: #222 !important;
      }}
      .email-masthead_name {{
        text-shadow: none !important;
      }}
    }}
    
    :root {{
      color-scheme: dark;
      supported-color-schemes: dark;
    }}
    </style>
  </head>
  <body>
    <span class="preheader">Use this link to reset your password. The link is only valid for 24 hours.</span>
    <table class="email-wrapper" width="100%" cellpadding="0" cellspacing="0" role="presentation">
      <tr>
        <td align="center">
          <table class="email-content" width="100%" cellpadding="0" cellspacing="0" role="presentation">
            <tr>
              <td class="email-masthead">
                <a href="{settings.FRONTEND_LINK}" class="f-fallback email-masthead_name">
                Petrichor 25
              </a>
              </td>
            </tr>
            <!-- Email Body -->
            <tr>
              <td class="email-body" width="570" cellpadding="0" cellspacing="0">
                <table class="email-body_inner" align="center" width="570" cellpadding="0" cellspacing="0" role="presentation">
                  <!-- Body content -->
                  <tr>
                    <td class="content-cell">
                      <div class="f-fallback">
                        <h1>Hi {name},</h1>
                        <p>You recently requested to reset your password for your Petrichor 25 account. Use the button below to reset it. <strong>This password reset is only valid for the next 24 hours.</strong></p>
                        <!-- Action -->
                        <table class="body-action" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation">
                          <tr>
                            <td align="center">
                              <!-- Border based button
           https://litmus.com/blog/a-guide-to-bulletproof-buttons-in-email-design -->
                              <table width="100%" border="0" cellspacing="0" cellpadding="0" role="presentation">
                                <tr>
                                  <td align="center">
                                    <a href="{action_url}" class="f-fallback button button--green" target="_blank">Reset your password</a>
                                  </td>
                                </tr>
                              </table>
                            </td>
                          </tr>
                        </table>
                        
                        <p>Thanks,
                          <br>The Petrichor 25 team</p>
                        <!-- Sub copy -->
                        <table class="body-sub" role="presentation">
                          <tr>
                            <td>
                              <p class="f-fallback sub">If you’re having trouble with the button above, copy and paste the URL below into your web browser.</p>
                              <p class="f-fallback sub">{action_url}</p>
                            </td>
                          </tr>
                        </table>
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
'''

def messageUser(name,message:str):
    return f'''
    <html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="x-apple-disable-message-reformatting" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title></title>
    <style type="text/css" rel="stylesheet" media="all">
    /* Base ------------------------------ */
    
    @import url("https://fonts.googleapis.com/css?family=Nunito+Sans:400,700&display=swap");
    body {{
      width: 100% !important;
      height: 100%;
      margin: 0;
      -webkit-text-size-adjust: none;
    }}
    
    a {{
      color: #3869D4;
    }}
    
    a img {{
      border: none;
    }}
    
    td {{
      word-break: break-word;
    }}
    
    .preheader {{
      display: none !important;
      visibility: hidden;
      mso-hide: all;
      font-size: 1px;
      line-height: 1px;
      max-height: 0;
      max-width: 0;
      opacity: 0;
      overflow: hidden;
    }}
    /* Type ------------------------------ */
    
    body,
    td,
    th {{
      font-family: "Nunito Sans", Helvetica, Arial, sans-serif;
    }}
    
    h1 {{
      margin-top: 0;
      color: #333333;
      font-size: 22px;
      font-weight: bold;
      text-align: left;
    }}
    
    h2 {{
      margin-top: 0;
      color: #333333;
      font-size: 16px;
      font-weight: bold;
      text-align: left;
    }}
    
    h3 {{
      margin-top: 0;
      color: #333333;
      font-size: 14px;
      font-weight: bold;
      text-align: left;
    }}
    
    td,
    th {{
      font-size: 16px;
    }}
    
    p,
    ul,
    ol,
    blockquote {{
      margin: .4em 0 1.1875em;
      font-size: 16px;
      line-height: 1.625;
    }}
    
    p.sub {{
      font-size: 13px;
    }}
    /* Utilities ------------------------------ */
    
    .align-right {{
      text-align: right;
    }}
    
    .align-left {{
      text-align: left;
    }}
    
    .align-center {{
      text-align: center;
    }}
    
    .u-margin-bottom-none {{
      margin-bottom: 0;
    }}
    /* Buttons ------------------------------ */
    
    .button {{
      background-color: #3869D4;
      border-top: 10px solid #3869D4;
      border-right: 18px solid #3869D4;
      border-bottom: 10px solid #3869D4;
      border-left: 18px solid #3869D4;
      display: inline-block;
      color: #FFF;
      text-decoration: none;
      border-radius: 3px;
      box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16);
      -webkit-text-size-adjust: none;
      box-sizing: border-box;
    }}
    
    .button--green {{
      background-color: #22BC66;
      border-top: 10px solid #22BC66;
      border-right: 18px solid #22BC66;
      border-bottom: 10px solid #22BC66;
      border-left: 18px solid #22BC66;
    }}
    
    .button--red {{
      background-color: #FF6136;
      border-top: 10px solid #FF6136;
      border-right: 18px solid #FF6136;
      border-bottom: 10px solid #FF6136;
      border-left: 18px solid #FF6136;
    }}
    
    @media only screen and (max-width: 500px) {{
      .button {{
        width: 100% !important;
        text-align: center !important;
      }}
    }}
    /* Attribute list ------------------------------ */
    
    .attributes {{
      margin: 0 0 21px;
    }}
    
    .attributes_content {{
      background-color: #F4F4F7;
      padding: 16px;
    }}
    
    .attributes_item {{
      padding: 0;
    }}
    /* Related Items ------------------------------ */
    
    .related {{
      width: 100%;
      margin: 0;
      padding: 25px 0 0 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .related_item {{
      padding: 10px 0;
      color: #CBCCCF;
      font-size: 15px;
      line-height: 18px;
    }}
    
    .related_item-title {{
      display: block;
      margin: .5em 0 0;
    }}
    
    .related_item-thumb {{
      display: block;
      padding-bottom: 10px;
    }}
    
    .related_heading {{
      border-top: 1px solid #CBCCCF;
      text-align: center;
      padding: 25px 0 10px;
    }}
    /* Discount Code ------------------------------ */
    
    .discount {{
      width: 100%;
      margin: 0;
      padding: 24px;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #F4F4F7;
      border: 2px dashed #CBCCCF;
    }}
    
    .discount_heading {{
      text-align: center;
    }}
    
    .discount_body {{
      text-align: center;
      font-size: 15px;
    }}
    /* Social Icons ------------------------------ */
    
    .social {{
      width: auto;
    }}
    
    .social td {{
      padding: 0;
      width: auto;
    }}
    
    .social_icon {{
      height: 20px;
      margin: 0 8px 10px 8px;
      padding: 0;
    }}
    /* Data table ------------------------------ */
    
    .purchase {{
      width: 100%;
      margin: 0;
      padding: 35px 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .purchase_content {{
      width: 100%;
      margin: 0;
      padding: 25px 0 0 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .purchase_item {{
      padding: 10px 0;
      color: #51545E;
      font-size: 15px;
      line-height: 18px;
    }}
    
    .purchase_heading {{
      padding-bottom: 8px;
      border-bottom: 1px solid #EAEAEC;
    }}
    
    .purchase_heading p {{
      margin: 0;
      color: #85878E;
      font-size: 12px;
    }}
    
    .purchase_footer {{
      padding-top: 15px;
      border-top: 1px solid #EAEAEC;
    }}
    
    .purchase_total {{
      margin: 0;
      text-align: right;
      font-weight: bold;
      color: #333333;
    }}
    
    .purchase_total--label {{
      padding: 0 15px 0 0;
    }}
    
    body {{
      background-color: #F2F4F6;
      color: #51545E;
    }}
    
    p {{
      color: #51545E;
    }}
    
    .email-wrapper {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #F2F4F6;
    }}
    
    .email-content {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    /* Masthead ----------------------- */
    
    .email-masthead {{
      padding: 25px 0;
      text-align: center;
    }}
    
    .email-masthead_logo {{
      width: 94px;
    }}
    
    .email-masthead_name {{
      font-size: 16px;
      font-weight: bold;
      color: #A8AAAF;
      text-decoration: none;
      text-shadow: 0 1px 0 white;
    }}
    /* Body ------------------------------ */
    
    .email-body {{
      width: 100%;
      margin: 0;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
    }}
    
    .email-body_inner {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
      -premailer-width: 570px;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      background-color: #FFFFFF;
    }}
    
    .email-footer {{
      width: 570px;
      margin: 0 auto;
      padding: 0;
      -premailer-width: 570px;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      text-align: center;
    }}
    
    .email-footer p {{
      color: #A8AAAF;
    }}
    
    .body-action {{
      width: 100%;
      margin: 30px auto;
      padding: 0;
      -premailer-width: 100%;
      -premailer-cellpadding: 0;
      -premailer-cellspacing: 0;
      text-align: center;
    }}
    
    .body-sub {{
      margin-top: 25px;
      padding-top: 25px;
      border-top: 1px solid #EAEAEC;
    }}
    
    .content-cell {{
      padding: 45px;
    }}
    /*Media Queries ------------------------------ */
    
    @media only screen and (max-width: 600px) {{
      .email-body_inner,
      .email-footer {{
        width: 100% !important;
      }}
    }}
    
    @media (prefers-color-scheme: dark) {{
      body,
      .email-body,
      .email-body_inner,
      .email-content,
      .email-wrapper,
      .email-masthead,
      .email-footer {{
        background-color: #333333 !important;
        color: #FFF !important;
      }}
      p,
      ul,
      ol,
      blockquote,
      h1,
      h2,
      h3,
      span,
      .purchase_item {{
        color: #FFF !important;
      }}
      .attributes_content,
      .discount {{
        background-color: #222 !important;
      }}
      .email-masthead_name {{
        text-shadow: none !important;
      }}
    }}
    
    :root {{
      color-scheme: dark;
      supported-color-schemes: dark;
    }}
    </style>
  </head>
  <body>
    <span class="preheader">{message}</span>
    <table class="email-wrapper" width="100%" cellpadding="0" cellspacing="0" role="presentation">
      <tr>
        <td align="center">
          <table class="email-content" width="100%" cellpadding="0" cellspacing="0" role="presentation">
            <tr>
              <td class="email-masthead">
                <a href="{settings.FRONTEND_LINK}" class="f-fallback email-masthead_name">
                Petrichor 25
              </a>
              </td>
            </tr>
            <!-- Email Body -->
            <tr>
              <td class="email-body" width="570" cellpadding="0" cellspacing="0">
                <table class="email-body_inner" align="center" width="570" cellpadding="0" cellspacing="0" role="presentation">
                  <!-- Body content -->
                  <tr>
                    <td class="content-cell">
                      <div class="f-fallback">
                        <h1>Hi {name},</h1>
                        {message}                        
                        <p>Thanks,
                          <br>The Petrichor 25 team</p>
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
'''

# <p>For security, this request was received from a {{operating_system}} device using {{browser_name}}. If you did not request a password reset, please ignore this email or <a href="{{support_url}}">contact support</a> if you have questions.</p>