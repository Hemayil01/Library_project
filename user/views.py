from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import OneTimeCode
from .serializers import (
    RegisterSerializer, UserPublicSerializer, ProfileSerializer, UserSerializer,
    ActivationSendSerializer, ActivationVerifySerializer,
    LoginSerializer, LogoutSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, SendPhoneVerificationSerializer, PhoneVerifySerializer
)
from .utils import generate_numeric_code, expiry

User = get_user_model()


class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['admin', 'librarian']:
            return Response({'detail': 'Only admin or librarian can view users.'},status=status.HTTP_403_FORBIDDEN)

        users = User.objects.all()
        data = UserPublicSerializer(users, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    
class UpdateRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        if request.user.role != 'admin':
            return Response({'detail': 'Only admin can update roles.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        role = request.data.get('role')
        if role not in dict(User.Role.choices):
            return Response({'detail': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        user.role = role
        user.save(update_fields=['role'])

        return Response(UserPublicSerializer(user).data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.ACCOUNT_ACTIVATION,
            code=generate_numeric_code(6),
            expires_at=expiry(10)
        )
        send_mail(
            subject='Library Activation Code',
            message=f'Your activation code: {otp.code}',
            from_email=None,
            recipient_list=[user.email]
        )
        return Response({'detail': 'Registered. Check your email for activation code.'}, status=status.HTTP_201_CREATED)


class ResendActivationOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ActivationSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.ACCOUNT_ACTIVATION,
            code=generate_numeric_code(6),
            expires_at=expiry(10)
        )
        send_mail(
            subject='Library Activation Code',
            message=f'Your activation code: {otp.code}',
            from_email=None,
            recipient_list=[user.email]
        )
        return Response({'detail': 'Activation code resent.'})


class VerifyActivationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ActivationVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        otp = serializer.validated_data['otp']

        user.is_active = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        return Response({'detail': 'Account activated successfully.'})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserPublicSerializer(user).data
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = RefreshToken(serializer.validated_data['refresh'])
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.PASSWORD_RESET,
            code=generate_numeric_code(6),
            expires_at=expiry(10)
        )
        send_mail(
            subject='Library Password Reset Code',
            message=f'Your reset code: {otp.code}',
            from_email=None,
            recipient_list=[user.email]
        )
        return Response({'detail': 'If email exists, password reset code sent.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save(update_fields=['password'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        return Response({'detail': 'Password reset successful.'})


class MeView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPublicSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()
        profile_data = data.pop('profile', {})

        user_serializer = UserSerializer(user, data=data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        profile_serializer = ProfileSerializer(user.profile, data=profile_data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response(UserPublicSerializer(user).data, status=status.HTTP_200_OK)

class SendPhoneVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SendPhoneVerificationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        phone_number = user.profile.phone_number

        OneTimeCode.objects.filter(
            user=user,
            purpose=OneTimeCode.Purpose.PHONE_VERIFICATION,
            is_used=False
        ).delete()

        otp = OneTimeCode.objects.create(
            user=user,
            purpose=OneTimeCode.Purpose.PHONE_VERIFICATION,
            code=generate_numeric_code(6),
            expires_at=expiry(10)
        )
        return Response({'detail': f'Verification code sent to {phone_number}.'}, status=status.HTTP_200_OK)


class VerifyPhoneView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PhoneVerifySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data['otp']
        user = request.user

        user.phone_verified = True
        user.save(update_fields=['phone_verified'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        return Response({'detail': 'Phone number verified successfully.'}, status=status.HTTP_200_OK)
