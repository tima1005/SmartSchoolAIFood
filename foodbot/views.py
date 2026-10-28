
import json
import urllib.request
import urllib.error
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from .forms import DishForm
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Dish, DailyMenu, Order, OrderItem


@ensure_csrf_cookie
def home(request):
    dishes = Dish.objects.filter(is_available=True)
    menus = DailyMenu.objects.filter(
        is_published=True
    ).prefetch_related("dishes")

    return render(request, "foodbot/home.html", {
        "dishes": dishes,
        "categories": Dish.CATEGORY_CHOICES,
        "menus": menus,
    })


@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"reply": "Сураныч, сурооңузду жазыңыз."},
                status=400,
            )

        system_prompt = """
Сен Smart School Cafeteria AI FoodBot жардамчысысың.
Кыргызча суроого кыргызча, орусча суроого орусча жооп бер.
Мектеп ашканасы, рецепттер, меню, азыктар жана пайдалуу
тамактануу боюнча так, түшүнүктүү жооп бер.
Меню суралса тамактарды тизмектеп көрсөт.
Күнүмдүк менюда эртең мененки, түшкү жана жеңил тамак болсун.
Жумалык менюда дүйшөмбүдөн жумага чейинки күндөр болсун.
Рецептте ингредиенттер жана даярдоо кадамдары көрсөтүлсүн.
Бааларды билбесең, ойлоп чыгарба.
Бир эле сүйлөмдү кайталаба.
Медициналык диагноз койбо; аллергия же өзгөчө диета боюнча
адистин кеңеши керек болушу мүмкүн экенин эскерт.
"""

        payload = json.dumps({
            "model": "qwen2.5:7b",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "options": {
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 30,
                "repeat_penalty": 1.25,
                "num_predict": 500,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        reply = result.get("message", {}).get("content", "").strip()

        if not reply:
            return JsonResponse(
                {"reply": "AI жооп түзгөн жок. Кайра аракет кылыңыз."},
                status=502,
            )

        return JsonResponse({"reply": reply})

    except (json.JSONDecodeError, AttributeError):
        return JsonResponse(
            {"reply": "Суроонун форматы туура эмес."},
            status=400,
        )
    except urllib.error.URLError:
        return JsonResponse(
            {"reply": "Ollama иштеп жатканын текшериңиз."},
            status=503,
        )
    except Exception as error:
        print("FoodBot катасы:", repr(error))
        return JsonResponse(
            {"reply": "Ката чыкты. Терминалдагы маалыматты текшериңиз."},
            status=500,
        )


@require_POST
def create_order(request):
    try:
        data = json.loads(request.body)
        customer_name = str(data.get("customer_name", "")).strip()
        class_name = str(data.get("class_name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        note = str(data.get("note", "")).strip()
        items = data.get("items", [])

        if not customer_name:
            return JsonResponse(
                {"error": "Окуучунун аты-жөнүн киргизиңиз."},
                status=400,
            )

        if not isinstance(items, list) or not items or len(items) > 50:
            return JsonResponse(
                {"error": "Корзинага тамак кошуңуз."},
                status=400,
            )

        with transaction.atomic():
            order = Order.objects.create(
                customer_name=customer_name[:150],
                class_name=class_name[:30],
                phone=phone[:30],
                note=note,
            )

            total = Decimal("0.00")

            for item in items:
                dish_id = int(item.get("dish_id", 0))
                quantity = int(item.get("quantity", 0))

                if quantity < 1 or quantity > 100:
                    raise ValueError("Тамактын саны 1–100 аралыгында болушу керек.")

                dish = Dish.objects.get(
                    pk=dish_id,
                    is_available=True,
                )

                price = dish.price
                OrderItem.objects.create(
                    order=order,
                    dish=dish,
                    quantity=quantity,
                    price=price,
                )
                total += price * quantity

            order.total_price = total
            order.save(update_fields=["total_price"])

        return JsonResponse({
            "success": True,
            "order_id": order.pk,
            "total_price": str(order.total_price),
            "message": f"Заказ №{order.pk} кабыл алынды!",
        })

    except (json.JSONDecodeError, TypeError, AttributeError):
        return JsonResponse(
            {"error": "Берилген маалыматтын форматы туура эмес."},
            status=400,
        )
    except (ValueError, InvalidOperation) as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Dish.DoesNotExist:
        return JsonResponse(
            {"error": "Тандалган тамак сатууда жок."},
            status=400,
        )
    except Exception as error:
        print("Заказ катасы:", repr(error))
        return JsonResponse(
            {"error": "Заказды сактоо мүмкүн болгон жок."},
            status=500,
        )


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/",
)
def add_dish(request):
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Жаңы тамак менюга ийгиликтүү кошулду!")
            return redirect("foodbot:home")
    else:
        form = DishForm()

    return render(request, "foodbot/add_dish.html", {
        "form": form,
    })
