from django.conf.urls import url

from ecommerce.extensions.edly_ecommerce_app.api.v1 import views


app_name = 'v1'
urlpatterns = [
    url(r'site_themes/', views.SiteThemesActions.as_view(), name='site_themes'),
    url(r'csrf_token/', views.CSRFTokenInfo.as_view(), name='get_csrf_token'),
    url(r'edly_sites/', views.EdlySiteViewSet.as_view(), name='edly_sites'),
    url(r'edly_site_config/', views.EdlySiteConfigViewset.as_view(), name='edly_site_config'),
]
