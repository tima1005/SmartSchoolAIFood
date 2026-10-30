import json
import urllib.request
import urllib.error
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render
from .models import Order, FinanceExpense, FoodWaste
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

    today = timezone.localdate()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    # Аяктаган заказдар
    monthly_orders = Order.objects.filter(
        status="completed",
        created_at__date__gte=month_start,
        created_at__date__lte=today
    )

    yearly_orders = Order.objects.filter(
        status="completed",
        created_at__date__gte=year_start,
        created_at__date__lte=today
    )

    monthly_income = monthly_orders.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    yearly_income = yearly_orders.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    # Чыгашалар
    monthly_expenses = FinanceExpense.objects.filter(
        date__gte=month_start,
        date__lte=today
    )

    yearly_expenses = FinanceExpense.objects.filter(
        date__gte=year_start,
        date__lte=today
    )

    monthly_expense_total = monthly_expenses.aggregate(
        total=Sum("amount")
    )["total"] or 0

    yearly_expense_total = yearly_expenses.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Тамак-аш калдыктары
    monthly_wastes = FoodWaste.objects.filter(
        date__gte=month_start,
        date__lte=today
    )

    yearly_wastes = FoodWaste.objects.filter(
        date__gte=year_start,
        date__lte=today
    )

    monthly_waste_total = sum(
        (w.total_loss for w in monthly_wastes),
        0
    )

    yearly_waste_total = sum(
        (w.total_loss for w in yearly_wastes),
        0
    )

    monthly_waste_count = sum(
        w.quantity for w in monthly_wastes
    )

    yearly_waste_count = sum(
        w.quantity for w in yearly_wastes
    )

    # Калдыктар продуктылар чыгымына киргендиктен,
    # аларды жалпы чыгымга экинчи жолу кошпойбуз.
    monthly_profit = monthly_income - monthly_expense_total
    yearly_profit = yearly_income - yearly_expense_total

    # Категориялар боюнча чыгаша
    expense_by_category = monthly_expenses.values(
        "category"
    ).annotate(total=Sum("amount"))

    category_names = dict(FinanceExpense.CATEGORY_CHOICES)

    expense_chart_labels = [
        category_names.get(item["category"], item["category"])
        for item in expense_by_category
    ]

    expense_chart_data = [
        float(item["total"])
        for item in expense_by_category
    ]

    context = {
        "dishes": dishes,
        "categories": Dish.CATEGORY_CHOICES,
        "menus": menus,

        "income": monthly_income,
        "expenses": monthly_expense_total,
        "waste_total": monthly_waste_total,
        "total_costs": monthly_expense_total,
        "profit": monthly_profit,
        "orders_count": monthly_orders.count(),
        "waste_count": monthly_waste_count,

        "yearly_income": yearly_income,
        "yearly_expenses": yearly_expense_total,
        "yearly_waste_total": yearly_waste_total,
        "yearly_profit": yearly_profit,
        "yearly_waste_count": yearly_waste_count,

        "expense_chart_labels": expense_chart_labels,
        "expense_chart_data": expense_chart_data,
    }

    return render(request, "foodbot/home.html", context)



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
Колдонуучунун тилинде жооп бер: кыргызча же орусча.
Мектеп ашканасы, меню, рецепттер, азыктар жана туура
тамактануу боюнча жардам бер.
Меню суралса, тамактарды тизмектеп көрсөт.
Рецептте ингредиенттер жана даярдоо кадамдары болсун.
Бааларды ойлоп чыгарба.
Кыска, так жана түшүнүктүү жооп бер.
Бир эле сүйлөмдү кайталаба.
Медициналык диагноз койбо.
"""

        payload = json.dumps({
            "model": "qwen2.5:7b",
            "stream": False,
            "keep_alive": "10m",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                },
            ],
            "options": {
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 30,
                "repeat_penalty": 1.2,
                "num_predict": 220,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        import time
        start_time = time.time()

        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        elapsed = time.time() - start_time
        print(f"FoodBot AI жооп убактысы: {elapsed:.2f} секунд")

        reply = result.get("message", {}).get(
            "content", ""
        ).strip()

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

    except urllib.error.URLError as error:
        print("Ollama байланыш катасы:", repr(error))
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
def finance_ai_api(request):
    try:
        today = timezone.localdate()
        month_start = today.replace(day=1)

        orders = Order.objects.filter(
            status="completed",
            created_at__date__gte=month_start,
            created_at__date__lte=today
        )

        income = orders.aggregate(
            total=Sum("total_price")
        )["total"] or 0

        expenses = FinanceExpense.objects.filter(
            date__gte=month_start,
            date__lte=today
        )

        expense_total = expenses.aggregate(
            total=Sum("amount")
        )["total"] or 0

        wastes = FoodWaste.objects.filter(
            date__gte=month_start,
            date__lte=today
        )

        waste_total = sum(
            (w.total_loss for w in wastes),
            0
        )

        total_costs = expense_total + waste_total
        profit = income - total_costs

        categories = expenses.values(
            "category"
        ).annotate(total=Sum("amount"))

        category_names = dict(FinanceExpense.CATEGORY_CHOICES)

        category_text = "\n".join(
            f"- {category_names.get(item['category'], item['category'])}: "
            f"{item['total']} сом"
            for item in categories
        )

        if not category_text:
            category_text = "Категориялар боюнча чыгаша азырынча жок."

        data = json.loads(request.body)
        question = data.get("question", "").strip()

        if not question:
            question = "Финансылык абалды анализдеп, үнөмдөө боюнча сунуш бер."

        system_prompt = f"""
Сен Smart School Cafeteria долбоорунун AI финансылык кеңешчисиң.

Колдонуучунун тилинде жооп бер: кыргызча же орусча.

Мектеп ашканасынын ушул айдагы чыныгы маалыматтары:

Киреше: {income} сом
Чыгашалар: {expense_total} сом
Тамак-аш калдыктарынан жоготуу: {waste_total} сом
Жалпы чыгым: {total_costs} сом
Таза пайда: {profit} сом

Чыгашалар категориялар боюнча:
{category_text}

Маалыматтарды так анализде.
Ойлоп чыгарылган сандарды колдонбо.
Кайсы чыгашаны азайтууга болорун түшүндүр.
Тамак-аш калдыктарын азайтуу боюнча сунуш бер.
Жоопту кыска, түшүнүктүү жана пайдалуу кыл.
"""

        payload = json.dumps({
            "model": "qwen2.5:7b",
            "stream": False,
            "keep_alive": "10m",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            "options": {
                "temperature": 0.3,
                "num_predict": 250,
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
                {"reply": "AI жооп түзгөн жок."},
                status=502
            )

        return JsonResponse({"reply": reply})

    except (json.JSONDecodeError, AttributeError):
        return JsonResponse(
            {"reply": "Суроонун форматы туура эмес."},
            status=400
        )

    except urllib.error.URLError:
        return JsonResponse(
            {"reply": "Ollama иштеп жатканын текшериңиз."},
            status=503
        )

    except Exception as error:
        print("Finance AI катасы:", repr(error))
        return JsonResponse(
            {"reply": "Финансылык анализ учурунда ката чыкты."},
            status=500
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


def finance_dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    # Ушул айдагы аяктаган заказдардан түшкөн киреше
    orders = Order.objects.filter(
        status="completed",
        created_at__date__gte=month_start,
        created_at__date__lte=today
    )

    income = orders.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    # Ушул айдагы чыгашалар
    expenses = FinanceExpense.objects.filter(
        date__gte=month_start,
        date__lte=today
    )

    expense_total = expenses.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Ушул айдагы тамак-аш калдыктары
    wastes = FoodWaste.objects.filter(
        date__gte=month_start,
        date__lte=today
    )

    waste_total = sum(
        (waste.total_loss for waste in wastes),
        0
    )

    # Жалпы чыгаша жана таза финансылык жыйынтык
    total_costs = expense_total + waste_total
    profit = income - total_costs

    context = {
        "income": income,
        "expenses": expense_total,
        "waste_total": waste_total,
        "total_costs": total_costs,
        "profit": profit,
        "orders_count": orders.count(),
        "waste_count": sum(w.quantity for w in wastes),
        "expense_records": expenses,
        "waste_records": wastes,
    }

    return render(
        request,
        "foodbot/finance.html",
        context
    )


