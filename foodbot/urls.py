
from django.urls import path
from . import views

app_name = "foodbot"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/order/", views.create_order, name="create_order"),

path("menu/add/", views.add_dish, name="add_dish"),

]
