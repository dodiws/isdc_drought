from .views import getDrought

from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(getDrought())

urlpatterns = [
    # api
    url(r'', include(geoapi.urls)),
]
