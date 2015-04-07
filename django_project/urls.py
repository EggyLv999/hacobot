from django.conf.urls import patterns, url, include
from django_project import views, audit
from django.contrib import admin
admin.autodiscover()
from django.shortcuts import render
from django.http import HttpResponse
import pymongo
import json
import re
urlpatterns = patterns('',
    url(r'^schedule/$', views.index, name='schedule'),
    url(r'^$', audit.index, name='index'),
    url(r'^courses/$', audit.parseaudit, name='parseaudit'),
    url(r'^admin/', include(admin.site.urls)),
)
