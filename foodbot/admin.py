
from django.contrib import admin
from .models import Dish, DailyMenu, MenuEntry, Order, OrderItem


class MenuEntryInline(admin.TabularInline):
    model = MenuEntry
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "calories", "is_available")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description", "ingredients")
    list_editable = ("price", "is_available")


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "meal_type", "is_published")
    list_filter = ("date", "meal_type", "is_published")
    search_fields = ("title", "description")
    inlines = [MenuEntryInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer_name", "class_name",
        "total_price", "status", "created_at"
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "class_name", "phone")
    list_editable = ("status",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "dish", "quantity", "price")
    list_filter = ("dish",)
