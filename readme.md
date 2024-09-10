# Petrichor backend

Every response(except for authentication error) from the api will atleast contain following-
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



### @login_required
Every request, which have @login_required, needs to send the access token in Authorization header.
```javascript
    login successful -> These items are appended to the response of the request:
    {
        "loggedIn":true,
        "refreshed":false,
        "token":null
    }
```
```javascript
    login unsuccessful -> In this case response will contains ONLY the following:
    {
        "loggedIn":false,
        "refreshed":false,
        "token":null
    }

```
```javascript
    on error-> If there is an error during authentication-
    {
        "detail":<description about the error>
    }

```

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
    

*   /event/
    ### Expected @login_required
    ```javascript
    request = {
        "id":string:"event id"
    }

    response = {
        "success":boolean:"whether request was successful or not",
        "name":string:"event name",
        "fee":number,
        "minMember":number,
        "maxMember":number,
    }
    ```

*   /event/apply/free/
    ### Expected @login_required
    ```javascript
    request = {
        "user_id":string:"email of the user registering for this"
        "eventId":string:"event Id",
        "participants":Array<string> : "participants including the above userId"
    }

    response = {
        "success":boolean:"whether event registration was successful or not",
    }
    ```

*   /event/apply/paid/
    ### Expected @login_required
    ```javascript
    request = {
        "user_id":string:"email of the user registering for this"
        "eventId":string:"event Id",
        "participants":Array<string> : "participants including the above userId",
        "transactionID":string ,
        "CAcode":string : "if not provided keep it-""   "
    }

    response = {
        "success":boolean:"whether event registration was successful or not",
    }
    ```

Expected on finanace page
```
export type Payment = {
    name: string,
    transId: string,
    amount: number,
    parts: number,
    verified: boolean
    CA: string
}

export type member = {
    name: string,
    email: string,
    phone: string,
}

export type data = {
    data: {
        [name:string]:[
                {
                    user: Payment,
                    members: member[]
                }
            ]
    }
}
```
