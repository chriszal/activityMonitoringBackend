import falcon
import json

import jwt
import datetime
from model.user import User
from model.registration_token import RegistrationToken
from services.user_service import UserService
from common.constants import REGISTRATION_SECRET
from common.constants import GMAIL_PASS
from common.constants import GMAIL_USER
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

class UserResource(object):

    def __init__(self):
        """
        Constructor method to initialize the UserResource class with an instance of UserService.
        """
        self.user_service = UserService()
        self.secret_key = REGISTRATION_SECRET
        self.gmail = GMAIL_USER
        self.gmail_pass = GMAIL_PASS
        # self.creds = Credentials.from_authorized_user_file('/usr/api/credentials.json')


    def on_get(self, req, resp):
        """
        HTTP GET request method to retrieve a list of all users.
        """
        try:
            resp.status = falcon.HTTP_200
            users = self.user_service.list_users()
            # Convert the list of User objects to a list of dictionary objects
            users_dict = [user.to_dict() for user in users]
            resp.body = json.dumps(users_dict)
        except Exception as e:
            raise falcon.HTTPConflict("User creation conflict", str(e))

    def on_post(self, req, resp):
        """
        HTTP POST request method to create a new user with the given user data.
        """
        try:
            user_data = req.media
            # Create a new user object using the user_service and the provided user data
            user_obj = self.user_service.create_user(**user_data)
            resp.status = falcon.HTTP_201
            resp.body = json.dumps({
                'message': 'User successfully created!',
                'status': 201,
                'data': user_obj.to_dict()
            })
        except Exception as e:
            # If an error occurs while creating the user, return a 409 status code with an error message
            resp.status = falcon.HTTP_409
            resp.body = json.dumps({
                'message': str(e),
                'status': 409,
                'data': {}
            })
            return

    def on_get_email(self, req, resp, email):
        """
        HTTP GET request method to retrieve the user object with the given email address.
        """
        try:
            user_obj = self.user_service.get_user_by_email(email)
            resp.body = json.dumps(user_obj.to_dict())
            resp.status = falcon.HTTP_200
        except User.DoesNotExist:
            # If the user does not exist, return a 404 status code with an error message
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'User does not exist.',
                'status': 404,
                'data': {}
            })

    def on_put_email(self, req, resp, email):
        """
        HTTP PUT request method to update the user object with the given email address using the provided user data.
        """
        
        try:
            user_data = req.media
            # Update the user object using the user_service and the provided user data
            user_obj = self.user_service.update_user_by_email(
                email, **user_data)
            resp.status = falcon.HTTP_200
            resp.body = json.dumps({
                'message': 'User successfully updated!',
                'status': 200,
                'data': user_obj.to_dict()
            })
        except User.DoesNotExist:
            # If the user does not exist, return a 404 status code with an error message
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'User does not exist.',
                'status': 404,
                'data': {}
            })

    def on_delete_email(self, req, resp, email):
        """
        HTTP DELETE request method to delete the user object with the given email address.
        """
        try:
            # Delete the user object using the user_service and the provided email address
            self.user_service.delete_user_by_email(email)
            resp.status = falcon.HTTP_204
            resp.body = json.dumps({
                'message': 'User successfully deleted!',
                'status': 204,
                'data': {}
            })
        except User.DoesNotExist:
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'User does not exist.',
                'status': 404,
                'data': {}
            })

    def on_get_id(self, req, resp, id):
        try:
            user_obj = self.user_service.get_user_by_id(id)
            resp.body = json.dumps({
                'email': user_obj.email
            })
            resp.status = falcon.HTTP_200
        except User.DoesNotExist:
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'User does not exist.',
                'status': 404,
                'data': {}
            })

    def on_get_id_by_email(self, req, resp, email):
        try:
            user_obj = self.user_service.get_user_id_by_email(email)
            resp.body = json.dumps({
                'id': str(user_obj.id)
            })
            resp.status = falcon.HTTP_200
        except User.DoesNotExist:
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'User does not exist.',
                'status': 404,
                'data': {}
            })

    def on_post_token(self, req, resp):
        """
        HTTP POST request method to create a new JWT token with the given user email, role, expiration date,
        and used or not bool field, and save it in the tokens collection.
        """
        try:
            token_data = req.media
            recipient = token_data['email']
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
            
            # Generate the token using the user email, role, and expiration date
            token = jwt.encode({
                'email': token_data['email'],
                'role': token_data['role'],
                'exp': expires_at
            }, self.secret_key, algorithm='HS256')
            
            # Save the token in the database
            token_obj = self.user_service.create_token(token=token)
            
            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.starttls()
            smtp.login(self.gmail, self.gmail_pass)
            
            body_html = f"""
                    <html>
                        <head>
                            <style>
                                .email-content {{
                                    font-family: Arial, sans-serif;
                                    max-width: 600px;
                                    margin: 20px auto;
                                    border: 1px solid #e0e0e0;
                                    padding: 20px;
                                    border-radius: 8px;
                                }}
                                .button {{
                                    display: inline-block;
                                    padding: 10px 20px;
                                    margin: 20px 0;
                                    color: #ffffff;
                                    background-color: #007BFF;
                                    border: none;
                                    border-radius: 4px;
                                    text-decoration: none;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="email-content">
                                <p>Hello!</p>
                                <p>We would like to invite you to register for our system. Click the button below to continue:</p>
                                <a href="http://0.0.0.0:3000/auth/register/{token}" class="button">Register Now</a>
                            </div>
                        </body>
                    </html>
                    """

            
            msg = MIMEMultipart()
            msg['From'] = GMAIL_USER
            msg['To'] = recipient
            msg['Subject'] = 'Activity Monitoring Registration'
            
            msg.attach(MIMEText(body_html, 'html'))
            smtp.sendmail(GMAIL_USER, recipient, msg.as_string())
            smtp.quit()

            resp.status = falcon.HTTP_201
            resp.body = json.dumps({
                'message': 'Token successfully created and Registration Email successfully Sent!',
                'status': 201,
                'data': {'token': token}
            })
        
        except Exception as e:
            resp.status = falcon.HTTP_409
            resp.body = json.dumps({
                'message': str(e),
                'status': 409,
                'data': {}
            })
            return

    def on_get_token(self, req, resp,token):
        """
        This function checks if a JWT token exists and is valid, and returns an appropriate response.
        
        :param req: The HTTP request object
        :param resp: resp is a response object that is used to send the HTTP response back to the
        client. It contains information such as the status code, headers, and body of the response. In
        this code snippet, it is used to set the status code and response body based on the outcome of
        the token validation process
        :param token: The JWT token that needs to be checked for validity
        :return: a response object with an HTTP status code and a JSON body containing a message,
        status, and data. The message and status indicate the result of the token validation, while the
        data contains the decoded payload of the token if it is valid. If the token is invalid or has
        already been used, an appropriate error message is returned. If the token does not exist, a 404
        error
        """
        try:
            is_used = self.user_service.is_token_used(token=token)
            if is_used:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps({
                    'message': 'Token has already been used.',
                    'status': 400,
                    'data': {}
                })
                return

            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            if payload['exp'] < datetime.datetime.utcnow().timestamp():
                resp.status = falcon.HTTP_400
                resp.body = json.dumps({
                    'message': 'The registration token has expired.',
                    'status': 400,
                    'data': {}
                })
                return

            resp.status = falcon.HTTP_200
            resp.body = json.dumps({
                'message': 'Token is valid.',
                'status': 200,
                'data': payload
            })
        except RegistrationToken.DoesNotExist:
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'This token does not exist.',
                'status': 404,
                'data': {}
            })
            return

    def on_post_user_by_token(self, req, resp,token):
        try:
            is_used = self.user_service.is_token_used(token=token)
            if is_used:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps({
                    'message': 'This token has already been registered.',
                    'status': 400,
                    'data': {}
                })
                return

            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            email = payload['email']
            role = payload['role']

            user_data = req.media
            first_name = user_data.get('first_name')
            last_name = user_data.get('last_name')
            password = user_data.get('password')
            user_obj = self.user_service.create_user(first_name=first_name, last_name=last_name, email=email, password=password, roles=[role])
            self.user_service.update_token(token)
            resp.status = falcon.HTTP_201
            resp.body = json.dumps({
                'message': 'User successfully registered!',
                'status': 201,
                'data': user_obj.to_dict()
            })
        except RegistrationToken.DoesNotExist:
            resp.status = falcon.HTTP_404
            resp.body = json.dumps({
                'message': 'Token does not exist.',
                'status': 404,
                'data': {}
            })
        except Exception as e:
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({
                'message': str(e),
                'status': 400,
                'data': {}
            })