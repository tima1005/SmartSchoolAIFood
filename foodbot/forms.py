
from django import forms
from .models import Dish


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = [
            "name",
            "description",
            "category",
            "price",
            "image",
            "ingredients",
            "calories",
            "is_available",
        ]

        labels = {
            "name": "Тамактын аталышы",
            "description": "Тамак жөнүндө маалымат",
            "category": "Категориясы",
            "price": "Баасы (сом)",
            "image": "Тамактын сүрөтү",
            "ingredients": "Ингредиенттери",
            "calories": "Калориясы",
            "is_available": "Сатууда бар",
        }

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Мисалы: Тоок шорпо",
            }),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Тамак жөнүндө кыскача маалымат",
            }),
            "price": forms.NumberInput(attrs={
                "min": "0",
                "step": "0.01",
            }),
            "ingredients": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Тоок эти, картошка, сабиз...",
            }),
            "calories": forms.NumberInput(attrs={
                "min": "0",
            }),
        }
