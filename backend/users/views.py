from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .wechat import code2session, WeChatLoginError

def tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}

class WeChatAuthView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        code = request.data.get('code')
        if not isinstance(code, str) or not code.strip():
            return Response({'detail': 'code 必填'}, status=400)
        try:
            identity = code2session(code.strip())
        except WeChatLoginError as exc:
            return Response({'detail': str(exc)}, status=502)
        with transaction.atomic():
            user, created = User.objects.get_or_create(username='wx:' + identity['openid'], defaults={'first_name': '团友'})
        payload = tokens(user)
        payload['user'] = {'id': user.id, 'nickname': user.first_name or '团友'}
        payload['created'] = created
        return Response(payload)

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'id': request.user.id, 'nickname': request.user.first_name or '团友'})

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('refresh')
        if token:
            RefreshToken(token).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
