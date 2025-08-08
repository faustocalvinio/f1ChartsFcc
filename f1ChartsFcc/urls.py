"""
URL configuration for f1ChartsFcc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import tyre_strategy_chart, laptimes_view, comparison_view, home, qualy_delta_view

urlpatterns = [
    path('', home, name='home'),
    path('tyre-chart/', tyre_strategy_chart, name='tyre_strategy_chart'),
    path('laptimes/', laptimes_view, name='laptimes_view'),
    path('comparison/', comparison_view, name='comparison_view'),
    path('qualy-delta/', qualy_delta_view, name='qualy_delta_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
