# Petrichor backend

Every response from the api will atleast contain following-
```javascript
    {
        "status":number:"status_code",
        "message":"some message regarding the request"
    }
```


#### NOTE: <br> 
*   #### All the below given responses are unique to the given url. Those will be appended to these above mentioned responses.

*    #### All below case are for status: 200, If status id other than 200, please consider the request to be failed. Any response which have status other than 200, does not gaurentee to contain below additional values.

*    #### @login_required depicts that login is required to resolve this request

## /api/

Main website will call using this url:

*   /register/
    ### Expected
    ```javascript
    request = {
        "username":string,
        "email":string,
        "password":string,
        "phone":string,
        "college":string,
        "gradyear":number,
        "institype":string,
        "stream":string
    }

    response = {
        "success":boolean:"whether register was successfull or not",
        "username":string:"username",
        "token":string:"contains value when login is successful"
    }
    ```

*   /login/
    ### Expected @login_required
    ```javascript
    request = {
        "username":"the email provided by user must be in this",
        "password":string
    }

    response = {
        "success":boolean:"whether login was successful or not",
        "token":string:"save this token in cookie/local storage",
        "username":string?:"username, null if not loggedIn"
    }
    ```

*   /auth/
    ### Expected @login_required
    ```javascript
    request = {
        "getEvents":boolean:"if True, returns all eventIds for which this user have been registered"
        "getUser":boolean:"if True, returns all information about the user."
    }

    response = {
        "success":boolean:"whether login was successful or not",
        "token":string:"save this token in cookie/local storage",
        "username":string?:"username, null if not loggedIn"
    }
    ```
    


