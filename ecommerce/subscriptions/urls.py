from django.conf.urls import url

from ecommerce.subscriptions import views

urlpatterns = [
    url(r'^(.*)$', views.SubscriptionAppView.as_view(), name='app'),
]
