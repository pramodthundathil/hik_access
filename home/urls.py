from django.urls import path 
from .import views 


urlpatterns = [
    path("call_connection/<str:deviceip>/<str:username>/<str:password>/", views.call_connection,name = "call_connection"),
    path('api/get-all-persons/', views.GetAllPersonsView.as_view(), name='get_all_persons'),
    path("add_person_record/", views.add_person_record,name="add_person_record"),
    path("delete_user_from_device/", views.delete_user_record,name="delete_user_from_device"),
    path("disable_enable_user_setup/", views.disable_enable_user_setup,name="disable_enable_user_setup"),
    path("get_person_by_employee_no/",views.get_person_by_employee_no,name="get_person_by_employee_no")
    
]