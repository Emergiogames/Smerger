from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from smerg_app.models import *
from smerg_app.serializers import *
from smerg_chat.models import *
from smerg_chat.serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.hashers import check_password
from rest_framework import status
from smerg_chat.utils.noti_utils import send_notifications
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from rest_framework.permissions import BasePermission
from django.utils.dateparse import parse_date
from django.db.models.functions import ExtractMonth
from django.db.models import Sum
from django.utils.timezone import make_aware



# Define standard status codes
SUCCESS = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

################################# A D M I N  S I D E #################################

# Login
class LoginView(APIView):
    @swagger_auto_schema(
        operation_description="Login authentication using username and password, and return token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username for authentication'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for authentication'),
            },
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request):
        if UserProfile.objects.filter(username=request.data.get('username')).exists():
            user = UserProfile.objects.get(username=request.data.get('username'))
            if check_password(request.data.get('password'), user.password) and user.is_superuser:
                if not Token.objects.filter(user=user).exists():
                    token = Token.objects.create(user=user)
                    token.save()
                token = Token.objects.get(user=user)
                return Response({'status': True, 'token': token.key})
        return Response({'status': False, 'message': 'Invalid credentials'})

# User details
class UserView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch all users",
        responses={
            SUCCESS: openapi.Response(
                description="All users details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                        # Add other relevant user fields here
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = UserSerial(UserProfile.objects.all().exclude(is_superuser=True), many=True)
                return Response(serializer.data)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

# Business
class BusinessView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch Buisness details",
        responses={
            SUCCESS: openapi.Response(
                description="Buisness details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Buisness ID'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Buisness Name'),
                        'entity_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of entity'),
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = SaleProfilesSerial(SaleProfiles.objects.filter(entity_type='business').order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Update business details",
        request_body=SaleProfilesSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Business updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def patch(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                user = UserProfile.objects.get(auth_token=request.headers.get('token'))
                mutable_data = request.data.copy()
                business = SaleProfiles.objects.get(id=id)
                serializer = SaleProfilesSerial(business, data=mutable_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': True, 'message': 'Business updated successfully'})
                return Response(serializer.errors)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Delete business",
        responses={
            SUCCESS: openapi.Response(
                description="Business deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def delete(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                if id == 0:
                    business = SaleProfiles.objects.filter(user__id=UserProfile.objects.get(auth_token=request.headers.get('token')).id, entity_type='business')
                    business.delete()
                    return Response({'status': True, 'message': 'All businesses deleted successfully'})
                business = SaleProfiles.objects.get(id=id)
                business.delete()
                return Response({'status': True, 'message': 'Business deleted successfully'})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Block/Unblock business",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'block'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Business ID'),
                'block': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True to block, False to unblock'),
            },
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Business block/unblock successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                business = SaleProfiles.objects.get(id=request.data.get('id'))
                business.block = request.data.get('block')
                business.save()
                message = "Business blocked successfully" if business.block else "Business unblocked successfully"
                return Response({'status': True, 'message': message})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

# Advisor
class AdvisorView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch advisor details",
        responses={
            SUCCESS: openapi.Response(
                description="Advisor details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the advisor'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the advisor'),
                        'entity_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of entity'),
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request,*args,**kw):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = ProfileSerial(Profile.objects.filter(entity_type='advisor').order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Update advisor details",
        request_body=SaleProfilesSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Advisor updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def patch(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                advisor = Profile.objects.get(id=id)
                mutable_data = request.data.copy()
                serializer = ProfileSerial(advisor, data=mutable_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': True, 'message': 'Advisor updated successfully'})
                return Response(serializer.errors)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Delete advisor",
        responses={
            SUCCESS: openapi.Response(
                description="Advisor deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def delete(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                advisor = Profile.objects.get(id=id)
                advisor.delete()
                return Response({'status': True, 'message': 'Advisor deleted successfully'})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Block/Unblock advisor",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'block'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Advisor ID'),
                'block': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True to block, False to unblock'),
            },
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Advisor block/unblock successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                advisor = SaleProfiles.objects.get(id=request.data.get('id'))
                advisor.block = request.data.get('block')
                advisor.save()
                message = "Advisor blocked successfully" if advisor.block else "Advisor unblocked successfully"
                return Response({'status': True, 'message': message})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

# Investor
class InvestorView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch investor details",
        responses={
            SUCCESS: openapi.Response(
                description="Investor details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Investor ID'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Investor Name'),
                        'entity_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of entity'),
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request,*args,**kw):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = SaleProfilesSerial(SaleProfiles.objects.filter(entity_type='investor').order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Update investor details",
        request_body=SaleProfilesSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Investor updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def patch(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                investor = SaleProfiles.objects.get(id=id)
                mutable_data = request.data.copy()
                serializer = SaleProfilesSerial(investor, data=mutable_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': True, 'message': 'Investor updated successfully'})
                return Response(serializer.errors)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Delete investor",
        responses={
            SUCCESS: openapi.Response(
                description="Investor deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def delete(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                investor = SaleProfiles.objects.get(id=id)
                investor.delete()
                return Response({'status': True, 'message': 'Investor deleted successfully'})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Block/Unblock investor",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'block'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Investor ID'),
                'block': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True to block, False to unblock'),
            },
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Investor block/unblock successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                investor = SaleProfiles.objects.get(id=request.data.get('id'))
                investor.block = request.data.get('block')
                investor.save()
                message = "Investor blocked successfully" if investor.block else "Investor unblocked successfully"
                return Response({'status': True, 'message': message})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

# Franchise
class FranchiseView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch franchise details",
        responses={
            SUCCESS: openapi.Response(
                description="Franchise details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Franchise ID'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Franchise Name'),
                        'entity_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of entity'),
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request,*args,**kw):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = SaleProfilesSerial(SaleProfiles.objects.filter(entity_type='franchise').order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Update franchise details",
        request_body=SaleProfilesSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Franchise updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def patch(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                franchise = SaleProfiles.objects.get(id=id)
                mutable_data = request.data.copy()
                serializer = SaleProfilesSerial(franchise, data=mutable_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': True, 'message': 'Franchise updated successfully'})
                return Response(serializer.errors)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Delete franchise",
        responses={
            SUCCESS: openapi.Response(
                description="Franchise deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def delete(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                franchise = SaleProfiles.objects.get(id=id)
                franchise.delete()
                return Response({'status': True, 'message': 'Franchise deleted successfully'})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Block/Unblock franchise",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id', 'block'],
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Franchise ID'),
                'block': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True to block, False to unblock'),
            },
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Franchise block/unblock successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                franchise = SaleProfiles.objects.get(id=request.data.get('id'))
                franchise.block = request.data.get('block')
                franchise.save()
                message = "Franchise blocked successfully" if franchise.block else "Franchise unblocked successfully"
                return Response({'status': True, 'message': message})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token is not passed'})

# Blocking a user
class Blocked(APIView):
    @swagger_auto_schema(operation_description="Blocking/ Unblocking a user",request_body=ProfileSerial,
    responses={SUCCESS: "{'status':True,'message': 'Blocked/ Unblocked a user successfully'}", BAD_REQUEST:"Passes an error message"})
    def post(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                profile = UserProfile.objects.get(id = request.data.get('userId'))
                if profile.block:
                    profile.block = False
                    message = "Successfully unblocked"
                else:
                    profile.block = True
                    message = "Successfully blocked"
                profile.save()
                return Response({'status':True,'message':message})
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

# Plans
class Plans(APIView):
    @swagger_auto_schema(operation_description="Plans fetching",
    responses={SUCCESS: "Plans Details fetched successfully", BAD_REQUEST:"Passes an error message"})
    def get(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = PlanSerial(Plan.objects.all().order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(operation_description="Plans creation",request_body=PlanSerial,
    responses={SUCCESS: "{'status':True,'message': 'Plans created successfully'}", BAD_REQUEST:"Passes an error message"})
    def post(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = PlanSerial(data = request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status':True})
                return Response(serializer.errors)
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(operation_description="Plan details updation",request_body=SaleProfilesSerial,
    responses={SUCCESS: "{'status':True,'message': 'Plan details updated successfully'}", BAD_REQUEST:"Passes an error message"})
    def put(self,request,id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = PlanSerial(Plan.objects.get(id=id), data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status':True})
                return Response(serializer.errors)
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(operation_description="Plan detail deletion",request_body=SaleProfilesSerial,
    responses={SUCCESS: "{'status':True,'message': 'Plan detail deleted successfully'}", BAD_REQUEST:"Passes an error message"})
    def delete(self,request,id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                banner = Plan.objects.get(id=id)
                banner.delete()
                return Response({'status':True})
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})


# Event banner
class Banners(APIView):
    @swagger_auto_schema(
        operation_description="Banner fetching",
        responses={
            SUCCESS: openapi.Response(
                description="Banner Details fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the banner'),
                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of the banner'),
                        'valid_date': openapi.Schema(type=openapi.TYPE_STRING, description='Validity date of the banner'),
                        'expire': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Banner validity status')
                    })
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Passes an error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                banner_type = request.GET.get('type')
                if 'type' not in request.GET:
                    serializer = BannerSerial(Banner.objects.filter(validity_date__gte=timezone.now()).order_by('-id'), many=True)
                else:
                    banners = Banner.objects.filter(validity_date__gte=timezone.now())
                    if banner_type != 'all':
                        banners = banners.filter(type=banner_type)
                    all_banners = Banner.objects.filter(type='all', validity_date__gte=timezone.now())
                    banners = banners | all_banners 

                    serializer = BannerSerial(banners.order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})
    @swagger_auto_schema(
        operation_description="Banners creation",
        request_body=BannerSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Banners created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Passes an error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def post(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = BannerSerial(data = request.data)
                if serializer.is_valid():
                    if 'type' not in request.data or 'valid_date' not in request.data:
                        return Response({'status': False,'message': 'Type and valid_date are required'}, status=status.HTTP_400_BAD_REQUEST)
                    serializer.save()
                    return Response({'status':True})
                return Response(serializer.errors)
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Banners updation",
        request_body=BannerSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Banners updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Passes an error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def put(self,request,id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = BannerSerial(Banner.objects.get(id=id), data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status':True})
                return Response(serializer.errors)
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(
        operation_description="Banner deletion",
        request_body=BannerSerial,
        responses={
            SUCCESS: openapi.Response(
                description="Banner deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request')
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Passes an error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def delete(self,request,id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                banner = Banner.objects.get(id=id)
                banner.delete()
                return Response({'status':True})
            return Response({'status':False,'message': 'User does not exist'})
        return Response({'status':False,'message': 'Token is not passed'})

# Notification creation, delete
class Notifications(APIView):
    @swagger_auto_schema(operation_description="Notifications fetching",
    responses={200: "Notifications Details fetched succesfully",400:"Passes an error message"})
    def get(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                serializer = NotiSerial(Notification.objects.all().order_by('-id'), many=True)
                return Response(serializer.data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(operation_description="Notification creation",request_body=NotiSerial,
    responses={200: "{'status':True,'message': 'Notification created successfully'}",400:"Passes an error message"})
    def post(self,request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                mutable_data = request.data.copy()
                if mutable_data.get('userId') != "all":
                    user = UserProfile.objects.get(id=mutable_data.get('userId'))
                    mutable_data['user'] = user.id
                serializer = NotiSerial(data = mutable_data)
                if serializer.is_valid():
                    noti = serializer.save()
                    if mutable_data.get('userId') == "all":
                        all_user_ids = [user.id for user in UserProfile.objects.all()]
                        users = UserProfile.objects.filter(id__in=all_user_ids)
                        noti.user.set(users)
                        noti.save()
                    return Response({'status':True})
                return Response(serializer.errors)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})

    @swagger_auto_schema(operation_description="Notification deletion",request_body=NotiSerial,
    responses={200: "{'status':True,'message': 'Notification deleted successfully'}",400:"Passes an error message"})
    def delete(self,request,id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                noti = Notification.objects.get(id=id)
                noti.delete()
                return Response({'status':True})
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token is not passed'})

# Admin Report Management
class AdminReportView(APIView):
    @swagger_auto_schema(operation_description="Fetch all reports",
    responses={200: "Reports fetched successfully", 404: "No reports found"})
    def get(self, request):
        token = request.headers.get('token')
        if token:
            if UserProfile.objects.filter(auth_token=token).exists():
                user = UserProfile.objects.get(auth_token=token)
                if not user.is_superuser:
                    return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status': False, 'message': 'Token not provided'}, status=status.HTTP_403_FORBIDDEN)

        reports = Report.objects.all()
        if not reports.exists():
            return Response({'status': False, 'message': 'No reports found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReportSerial(reports, many=True)
        return Response({'status': True, 'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Update report status and type",
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['report_id', 'report_type', 'status'],
    properties={'report_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the report'),
                'report_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of report'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the report (e.g., resolved, pending)')}), 
    responses={200: "{'status':True,'message': 'Report updated successfully'}", 400: "{'status':False,'message': 'Invalid report ID or data'}"})
    def patch(self, request):
        token = request.headers.get('token')
        if token:
            if UserProfile.objects.filter(auth_token=token).exists():
                user = UserProfile.objects.get(auth_token=token)
                if not user.is_superuser:
                    return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status': False, 'message': 'Token not provided'}, status=status.HTTP_403_FORBIDDEN)

        report_id = request.data.get('report_id')
        report_type = request.data.get('report_type')
        r_status = request.data.get('status')

        if not report_id or not report_type or not status:
            return Response({'status': False, 'message': 'Invalid report ID or data'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({'status': False, 'message': 'Report does not exist'}, status=status.HTTP_404_NOT_FOUND)

        report.report_type = report_type
        report.status = r_status
        report.save()

        return Response({'status': True, 'message': 'Report updated successfully'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Block post or user based on report",
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['post_id', 'user_id', 'block'],
    properties={'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the post to block/unblock'),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user to block/unblock'),
                'block': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True to block, False to unblock')}), 
    responses={200: "{'status':True,'message': 'Post/User block/unblock successful'}", 400: "{'status':False,'message': 'Invalid post/user ID or block status'}"})
    def post(self, request):
        token = request.headers.get('token')
        if token:
            if UserProfile.objects.filter(auth_token=token).exists():
                user = UserProfile.objects.get(auth_token=token)
                if not user.is_superuser:
                    return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status': False, 'message': 'Token not provided'}, status=status.HTTP_403_FORBIDDEN)

        report_type = request.data.get('report_type')
        block = request.data.get('block')

        if report_type not in ['post', 'user'] or block is None:
            return Response({'status': False, 'message': 'Invalid report type or block status'}, status=status.HTTP_400_BAD_REQUEST)

        if report_type == 'post':
            post_id = request.data.get('post_id')
            if post_id is None:
                return Response({'status': False, 'message': 'Post ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                post = SaleProfiles.objects.get(id=post_id)
                post.block = block
                post.save()
                message = "Post blocked successfully" if block else "Post unblocked successfully"
            except SaleProfiles.DoesNotExist:
                return Response({'status': False, 'message': 'Post does not exist'}, status=status.HTTP_404_NOT_FOUND)
        elif report_type == 'user':
            user_id = request.data.get('user_id')
            if user_id is None:
                return Response({'status': False, 'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = UserProfile.objects.get(id=user_id)
                user.block = block
                user.save()
                message = "User blocked successfully" if block else "User unblocked successfully"                
            except UserProfile.DoesNotExist:
                return Response({'status': False, 'message': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': True, 'message': message}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    @swagger_auto_schema(
        operation_description="Fetch number of posts, users, and reports within a date range or show full numbers if dates are not provided",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Start date in YYYY-MM-DD format'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='End date in YYYY-MM-DD format'),
            }
        ),
        responses={
            SUCCESS: openapi.Response(
                description="Dashboard statistics fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'posts_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of posts'),
                        'users_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of users'),
                        'reports_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of reports'),
                        'subscribe_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of subscrptions'),
                    }
                )
            ),
            BAD_REQUEST: openapi.Response(
                description="Error message",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Status of the request'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        }
    )
    def get(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists():
                user = UserProfile.objects.get(auth_token=request.headers.get('token'))
                if not user.is_superuser:
                    return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'status': False, 'message': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status': False, 'message': 'Token not provided'}, status=status.HTTP_403_FORBIDDEN)

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            posts_count = SaleProfiles.objects.count()  
            users_count = UserProfile.objects.count()    
            reports_count = Report.objects.count()        
            subscribe_count=Subscription.objects.count()       
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return Response({'status': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

            posts_count = SaleProfiles.objects.filter(created_at__range=[start_date, end_date]).count()
            users_count = UserProfile.objects.filter(date_joined__range=[start_date, end_date]).count()
            reports_count = Report.objects.filter(created_at__range=[start_date, end_date]).count()
            subscribe_count = Subscription.objects.filter(expiry_date__range=[start_date, end_date]).count()

        return Response({
            'posts_count': posts_count,
            'users_count': users_count,
            'reports_count': reports_count,
            'subscribe_count':subscribe_count
        }, status=status.HTTP_200_OK)

class Userconnections(APIView):
    @swagger_auto_schema(operation_description="Fetch recent enquiries",
    responses={200: "{'status':True,'message': 'Fetched successfully'}"})
    def get(self, request):
        token = request.headers.get('token')
        if not token:
            return Response({'status': False, 'message': 'Token is not passed'})

        try:
    
            user = UserProfile.objects.get(auth_token=token)
            if user.block:
                return Response({'status': False, 'message': 'User is blocked'})

            user_id = request.GET.get('user_id')
            
            if user_id:
                try:
                    target_user = UserProfile.objects.get(id=user_id)
                    users_to_fetch = [target_user]
                except UserProfile.DoesNotExist:
                    return Response({'status': False, 'message': 'Specified user does not exist'})
            else:
                users_to_fetch = UserProfile.objects.all()

            enquiries_data = []
            
            for target_user in users_to_fetch:
                recent_rooms = Room.objects.filter(
                    Q(first_person=target_user) | Q(second_person=target_user)
                ).order_by('-created_date')

                for room in recent_rooms:
                    if ChatMessage.objects.filter(room=room).exists():
                        other_person = room.second_person if room.first_person == target_user else room.first_person
                        enquiry_info = {
                            'user': target_user.username,       
                            'other_person': other_person.username,
                            'created_date': room.created_date
                        }
                        enquiries_data.append(enquiry_info)

            return Response({'status': True, 'recent_enquiries': enquiries_data})

        except UserProfile.DoesNotExist:
            return Response({'status': False, 'message': 'User does not exist'})

class UserConnectionCount(APIView):
    @swagger_auto_schema(operation_description="Get the total number of connections for a user",
                         responses={200: "{'status': True, 'message': 'Fetched successfully', 'connections_count': <count>}"},
                         manual_parameters=[{'name': 'user_id', 'in': 'query', 'description': 'ID of the user to fetch connections for', 'required': False, 'type': 'integer'}])
    def get(self, request):
        token = request.headers.get('token')
        if not token:
            return Response({'status': False, 'message': 'Token is not passed'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            requesting_user = UserProfile.objects.get(auth_token=token)
            if requesting_user.block:
                return Response({'status': False, 'message': 'User is blocked'}, status=status.HTTP_403_FORBIDDEN)
            user_id = request.GET.get('user_id')
            if user_id:
                try:
                    target_user = UserProfile.objects.get(id=user_id)
                except UserProfile.DoesNotExist:
                    return Response({'status': False, 'message': 'Specified user does not exist'}, status=status.HTTP_404_NOT_FOUND)
            else:
                target_user = requesting_user
            connections_count = Room.objects.filter(
                Q(first_person=target_user) | Q(second_person=target_user)
            ).distinct().count()

            return Response({'status': True, 'connections_count': connections_count}, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({'status': False, 'message': 'Requesting user does not exist'}, status=status.HTTP_404_NOT_FOUND)

        
class ChangePwd(APIView):
    @swagger_auto_schema(operation_description="Forgot password api, where an otp is sended to user's whatsapp",request_body=openapi.Schema(type=openapi.TYPE_OBJECT,required=['username'],
    properties={'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username for authentication'),'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for authentication'),},),
    responses={200: "{'status':True,'message': 'User password changed successfully'}",400:"Passes an error message"})
    def post(self,request):
        password = request.data.get('password')
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                user = UserProfile.objects.get(auth_token=request.headers.get('token'))
            else:
                return Response({'status':False,'message': 'User doesnot exist'})
        else:
            if  UserProfile.objects.get(username=request.data.get('username')).is_superuser:
                user = UserProfile.objects.get(username=request.data.get('username'))
        if check_password(password, user.password):
            return Response({'status':False})
        user.set_password(password)
        user.save()
        return Response({'status':True})


    

class AdminPostVerification(APIView):

    @swagger_auto_schema(
        operation_description="Fetch all posts pending verification",
        responses={200: "Pending posts fetched successfully"}
    )
    def get(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
                pending_posts = SaleProfiles.objects.filter(verified=False, block=False)
        serializer = SaleProfilesSerial(pending_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Approve or block a post",
        request_body=None,
        responses={200: "{'status': True, 'message': 'Post status updated successfully'}"}
    )
    def patch(self, request, id):
        action = request.data.get('action')

        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser:
        
                try:
                    post = SaleProfiles.objects.get(id=id)
                except SaleProfiles.DoesNotExist:
                    return Response({'status': False, 'message': 'Post does not exist'}, status=status.HTTP_404_NOT_FOUND)

                if action == 'approve':
                    post.verified = True
                    post.block = False
                    message = 'Post approved successfully'
                elif action == 'block':
                    post.verified = False
                    post.block = True
                    message = 'Post blocked successfully'
                else:
                    return Response({'status': False, 'message': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

                post.save()
                return Response({'status': True, 'message': message}, status=status.HTTP_200_OK)
            else:
                return Response({'status':False,'message': 'User doesnot exist'})



class Adminview(APIView):
     @swagger_auto_schema(
        operation_description="Fetch all admins",
        responses={200: "All Admin fetched successfully"}
    )
     def get(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser and UserProfile.objects.get(auth_token=request.headers.get('token')).is_staff:
                serializer = UserSerial(UserProfile.objects.filter(is_superuser=True).exclude(is_staff=True), many=True)
                return Response(serializer.data)
            return Response({'status':False,'message': 'User doesnot exist'})
        return Response({'status':False,'message': 'Token doesnot exist'})
     

     @swagger_auto_schema(operation_description="creation of new admins",
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['email','password'],
    properties={'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the new admin'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password of the new admin')}), 
    responses={200: "{'status':True,'message': 'Admins are'}", 400: "{'status':False,'message': 'Invalid post/user ID or block status'}"})
     def post(self, request):
         if request.headers.get('token'):
             if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser and UserProfile.objects.get(auth_token=request.headers.get('token')).is_staff:
                 serializer = UserSerial(data=request.data)
                 
                 if UserProfile.objects.filter(username=request.data.get('email')).exists():
                     return Response({'status': False, 'message': 'Email already exists'})
                 else:
                     if serializer.is_valid():
                         admin = serializer.save()
                         admin.is_superuser = True
                         admin.set_password(request.data.get('password'))
                         admin.save()
                         return Response({'status': True, 'message': 'Admin created successfully'})
                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             return Response({'status': False, 'message': 'User does not exist'})
         return Response({'status': False, 'message': 'Token does not exist'})
# ... existing code ...
     @swagger_auto_schema(operation_description="Update existing admin",
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['email','password'],
    properties={'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the admin to update'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password of the admin')}), 
    responses={200: "{'status':True,'message': 'Admin updated successfully'}", 400: "{'status':False,'message': 'Invalid post/user ID or block status'}"})
     def patch(self, request, id):
         if request.headers.get('token'):
             if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser and UserProfile.objects.get(auth_token=request.headers.get('token')).is_staff:
                 admin = UserProfile.objects.get(id=id)
                 serializer = UserSerial(admin, data=request.data, partial=True)
                 if serializer.is_valid():
                    password = request.data.get('password')
                    serializer.save()
                    if password:
                        admin.set_password(password)
                        admin.save()
                    return Response({'status': True, 'message': 'Admin updated successfully'})
                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             return Response({'status': False, 'message': 'User does not exist'})
         return Response({'status': False, 'message': 'Token does not exist'})
# ... existing code ...

     @swagger_auto_schema(operation_description="Delete existing admin",
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['id'],
    properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the admin to delete')}), 
    responses={200: "{'status':True,'message': 'Admin deleted successfully'}", 400: "{'status':False,'message': 'Invalid admin ID'}"})
     def delete(self, request, id):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser and UserProfile.objects.get(auth_token=request.headers.get('token')).is_staff:         
                try:
                    admin = UserProfile.objects.get(id=id)
                    admin.delete()
                    return Response({'status': True, 'message': 'Admin deleted successfully'})
                except UserProfile.DoesNotExist:
                    return Response({'status': False, 'message': 'Admin does not exist'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token does not exist'})
    


class TotalTimeSpentView(APIView):
    def get(self, request):
        if request.headers.get('token'):
            if UserProfile.objects.filter(auth_token=request.headers.get('token')).exists() and UserProfile.objects.get(auth_token=request.headers.get('token')).is_superuser and UserProfile.objects.get(auth_token=request.headers.get('token')).is_staff:         
                try:
                    user = UserProfile.objects.get(auth_token=request.headers.get('token'))
                    if user.block:
                        return Response({'status': False, 'message': 'User is blocked'})
                    user_id = request.query_params.get('user_id')
                    start_date = request.query_params.get('start_date')
                    end_date = request.query_params.get('end_date')

                    if not user_id or not start_date or not end_date:
                        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

                    try:
                       
                        start_date = make_aware(datetime.combine(parse_date(start_date), datetime.min.time()))
                        end_date = make_aware(datetime.combine(parse_date(end_date), datetime.max.time()))


                      
                        if not start_date or not end_date:
                            raise ValueError("Invalid date format")

                        sessions = UserSession.objects.filter(
                            user_id=user_id,
                            login_time__gte=start_date,
                            logout_time__lte=end_date
                        )

                        
                        total_seconds = sessions.aggregate(total=Sum('session_duration'))['total'] or 0
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60

                        return Response({
                            "user_id": user_id,
                            "total_time_spent": f"{hours} hours, {minutes} minutes"
                        })

                    except ValueError:
                        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
                except UserProfile.DoesNotExist:
                    return Response({'status': False, 'message': 'User does not exist'})
            return Response({'status': False, 'message': 'User does not exist'})
        return Response({'status': False, 'message': 'Token does not exist'})
