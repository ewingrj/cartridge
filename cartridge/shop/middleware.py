from __future__ import unicode_literals

from django.core import urlresolvers

from mezzanine.conf import settings
from mezzanine.pages.middleware import PageMiddleware
from mezzanine.pages.views import page as page_view

from cartridge.shop.models import Cart


class SSLRedirect(object):

    def __init__(self):
        old = ("SHOP_SSL_ENABLED", "SHOP_FORCE_HOST", "SHOP_FORCE_SSL_VIEWS")
        for name in old:
            try:
                getattr(settings, name)
            except AttributeError:
                pass
            else:
                import warnings
                warnings.warn("The settings %s are deprecated; "
                    "use SSL_ENABLED, SSL_FORCE_HOST and "
                    "SSL_FORCE_URL_PREFIXES, and add "
                    "mezzanine.core.middleware.SSLRedirectMiddleware to "
                    "MIDDLEWARE_CLASSES." % ", ".join(old))
                break


class ShopMiddleware(SSLRedirect):
    """
    Adds cart and wishlist attributes to the current request.
    """
    def process_request(self, request):
        request.cart = Cart.objects.from_request(request)
        wishlist = request.COOKIES.get("wishlist", "").split(",")
        if not wishlist[0]:
            wishlist = []
        request.wishlist = wishlist

class MultiurlPageMiddleware(PageMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Wraps mezzanine PageMiddleware, providing support for multiurl
        PageMiddleware will detect if the view_func != page_view and attempt to 
        call the view_func (in order to allow calling other apps pages). It then
        catches 404s and renders the page template. When using multiurl for the page
        url, the view_func is a multiurl function.
        """
        if hasattr(view_func, 'multi_resolver_match'):
            for match in view_func.multi_resolver_match.matches:
                try:
                    # should we pass view_args & view_kwargs???
                    return super(MultiurlPageMiddleware, self).process_view(request, match.func, match.args,
                                                                            match.kwargs)
                except view_func.multi_resolver_match.exceptions:
                    continue

            raise urlresolvers.Resolver404(
                {'tried': view_func.multi_resolver_match.patterns_matched, 'path': view_func.multi_resolver_match.path})

        return super(MultiurlPageMiddleware, self).process_view(request, view_func, view_args, view_kwargs)
