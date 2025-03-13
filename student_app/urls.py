from django.urls import path,include
from . import views
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static
from .views import notice_list
from .views import contact_view
from .views import register_view, login_view
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('',views.home,name='home'),
     path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('about/',views.about, name='about'),
    path('year/',views.year, name='year'),
    # path('contact/',views.contact, name='contact'),
    path('subjects/<str:year>/', views.subjects, name='subjects'),
    path('notices/', notice_list, name='notice_list'),
     path('contact/', views.contact_view, name='contact'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

