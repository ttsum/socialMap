from rest_framework.response import Response
from rest_framework.views import APIView
from .service import parse_query_with_meta


class ParseIntentView(APIView):
    def post(self, request):
        intent, meta = parse_query_with_meta(request.data.get('query'))
        return Response({'intent': intent, 'meta': meta})
