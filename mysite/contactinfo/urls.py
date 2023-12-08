from django.urls import path
from . import views 

urlpatterns = [
    path('contact-info/', views.upload_url, name='upload_url'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('delete/<int:id>/', views.delete, name='delete'),
    path('show-all-contacts/', views.show_all_contacts, name='show_all_contacts'),
    path('deleteurlcontents/', views.delete_urlcontents, name='delete_urlcontents'),
]
