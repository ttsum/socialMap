from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, APIException
from .service import search, geocode, AmapError


class AmapView(APIView):
    def handle(self, fn, request):
        value = request.query_params.get('keywords' if fn is search else 'address', '').strip()
        if not value or len(value) > 120:
            raise ValidationError({'detail': '地点关键词不能为空且不能超过120字'})
        try:
            result = fn(value, request.query_params.get('city', '').strip())
        except AmapError as exc:
            error = APIException(str(exc)); error.status_code = 502; raise error
        return Response({'items': result if fn is search else ([result] if result else [])})

    def get(self, request):
        return self.handle(search, request)


class GeocodeView(AmapView):
    def get(self, request):
        return self.handle(geocode, request)
