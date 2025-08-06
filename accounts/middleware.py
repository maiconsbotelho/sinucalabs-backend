from django.utils.deprecation import MiddlewareMixin


class CookieTokenMiddleware(MiddlewareMixin):
    """
    Middleware para extrair tokens JWT dos cookies httpOnly
    e adicioná-los ao header Authorization
    """
    
    def process_request(self, request):
        # Extrair access_token do cookie
        access_token = request.COOKIES.get('access_token')
        
        if access_token:
            # Adicionar token ao header Authorization
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        
        return None