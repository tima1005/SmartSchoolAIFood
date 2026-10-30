
from django.db import models


class Dish(models.Model):
    CATEGORY_CHOICES = [
        ("breakfast", "Завтрак"),
        ("lunch", "Обед"),
        ("snack", "Перекус"),
        ("drink", "Напитки"),
        ("dessert", "Десерты"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(
        upload_to="dishes/",
        blank=True,
        null=True
    )
    ingredients = models.TextField(blank=True)
    calories = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DailyMenu(models.Model):
    MEAL_CHOICES = [
        ("breakfast", "Завтрак"),
        ("lunch", "Обед"),
        ("snack", "Перекус"),
    ]

    title = models.CharField(max_length=200)
    date = models.DateField()
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_CHOICES
    )
    description = models.TextField(blank=True)
    dishes = models.ManyToManyField(
        Dish,
        through="MenuEntry",
        related_name="daily_menus"
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MenuEntry(models.Model):
    menu = models.ForeignKey(
        DailyMenu,
        on_delete=models.CASCADE
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["menu", "dish"],
                name="unique_dish_in_menu"
            )
        ]

    def __str__(self):
        return f"{self.menu} — {self.dish}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("confirmed", "Подтверждён"),
        ("preparing", "Готовится"),
        ("ready", "Готов"),
        ("completed", "Завершён"),
        ("cancelled", "Отменён"),
    ]

    customer_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=30)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заказ #{self.id} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.dish.name} × {self.quantity}"


class FinanceExpense(models.Model):
    CATEGORY_CHOICES = [
        ("products", "Продукты"),
        ("salary", "Зарплата"),
        ("utilities", "Коммунальные услуги"),
        ("equipment", "Оборудование"),
        ("other", "Другие расходы"),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Название расхода"
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other",
        verbose_name="Категория"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма (сом)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата"
    )

    def __str__(self):
        return f"{self.title} — {self.amount} сом"

    class Meta:
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"
        ordering = ["-date"]


class FoodWaste(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Блюдо"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество порций"
    )
    cost_per_portion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Себестоимость одной порции (сом)"
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Причина отходов"
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата"
    )

    @property
    def total_loss(self):
        return self.quantity * self.cost_per_portion

    def __str__(self):
        return f"{self.quantity} порций — {self.total_loss} сом"

    class Meta:
        verbose_name = "Пищевой отход"
        verbose_name_plural = "Пищевые отходы"
        ordering = ["-date"]
