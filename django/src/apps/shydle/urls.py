from django.urls import path
from .views import ShydleView

app_name = 'shydle'

urlpatterns = [
    path('', ShydleView.as_view(), name='index'),
]
