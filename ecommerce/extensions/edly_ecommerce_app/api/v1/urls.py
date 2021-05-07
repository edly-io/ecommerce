from django.conf.urls import url

from ecommerce.extensions.edly_ecommerce_app.api.v1 import views


app_name = 'v1'
urlpatterns = [
    url(r'site_themes/', views.SiteThemesActions.as_view(), name='site_themes'),
    url(r'session_info/', views.UserSessionInfo.as_view(), name='get_user_session_info'),
    url(r'^edly_sites/', views.EdlySiteViewSet.as_view(), name='edly_sites'),
]
