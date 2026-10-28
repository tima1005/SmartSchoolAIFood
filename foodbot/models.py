
from django.db import models


class Dish(models.Model):
    CATEGORY_CHOICES = [
        ("breakfast", "Эртең мененки тамак"),
        ("lunch", "Түшкү тамак"),
        ("snack", "Жеңил тамак"),
        ("drink", "Суусундук"),
        ("dessert", "Десерт"),
    ]

    name = models.CharField("Тамактын аталышы", max_length=150)
    description = models.TextField("Сүрөттөмө", blank=True)
    category = models.CharField(
        "Категория",
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="lunch",
    )
    price = models.DecimalField(
        "Баасы (сом)",
        max_digits=8,
        decimal_places=2,
    )
    image = models.ImageField(
        "Сүрөт",
        upload_to="dishes/",
        blank=True,
        null=True,
    )
    ingredients = models.TextField("Курамы", blank=True)
    calories = models.PositiveIntegerField(
        "Калория (ккал)",
        blank=True,
        null=True,
    )
    is_available = models.BooleanField(
        "Сатууда бар",
        default=True,
    )
    created_at = models.DateTimeField(
        "Түзүлгөн убакыт",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Тамак"
        verbose_name_plural = "Тамактар"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DailyMenu(models.Model):
    MEAL_CHOICES = [
        ("breakfast", "Эртең мененки тамак"),
        ("lunch", "Түшкү тамак"),
        ("snack", "Жеңил тамак"),
    ]

    title = models.CharField("Менюнун аталышы", max_length=150)
    date = models.DateField("Күнү")
    meal_type = models.CharField(
        "Тамактануу түрү",
        max_length=20,
        choices=MEAL_CHOICES,
        default="lunch",
    )
    description = models.TextField("Сүрөттөмө", blank=True)
    dishes = models.ManyToManyField(
        Dish,
        through="MenuEntry",
        related_name="menus",
        verbose_name="Тамактар",
        blank=True,
    )
    is_published = models.BooleanField(
        "Жарыяланган",
        default=False,
    )
    created_at = models.DateTimeField(
        "Түзүлгөн убакыт",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Менюлар"
        ordering = ["date", "meal_type"]

    def __str__(self):
        return f"{self.title} — {self.date}"


class MenuEntry(models.Model):
    menu = models.ForeignKey(
        DailyMenu,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="Меню",
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="menu_entries",
        verbose_name="Тамак",
    )
    quantity = models.PositiveIntegerField(
        "Порция саны",
        default=1,
    )

    class Meta:
        verbose_name = "Менюдагы тамак"
        verbose_name_plural = "Менюдагы тамактар"
        constraints = [
            models.UniqueConstraint(
                fields=["menu", "dish"],
                name="unique_dish_in_menu",
            )
        ]

    def __str__(self):
        return f"{self.dish.name} — {self.menu.title}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Күтүүдө"),
        ("confirmed", "Ырасталды"),
        ("preparing", "Даярдалууда"),
        ("ready", "Даяр"),
        ("completed", "Аяктады"),
        ("cancelled", "Жокко чыгарылды"),
    ]

    customer_name = models.CharField(
        "Окуучунун аты-жөнү",
        max_length=150,
        default="Белгисиз",
    )
    class_name = models.CharField(
        "Классы",
        max_length=30,
        blank=True,
    )
    phone = models.CharField(
        "Телефон",
        max_length=30,
        blank=True,
    )
    status = models.CharField(
        "Заказдын статусу",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    total_price = models.DecimalField(
        "Жалпы сумма (сом)",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    note = models.TextField("Кошумча маалымат", blank=True)
    created_at = models.DateTimeField(
        "Заказ берилген убакыт",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказдар"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.pk} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        verbose_name="Тамак",
    )
    quantity = models.PositiveIntegerField("Саны", default=1)
    price = models.DecimalField(
        "Бир порциянын баасы",
        max_digits=8,
        decimal_places=2,
    )

    class Meta:
        verbose_name = "Заказдагы тамак"
        verbose_name_plural = "Заказдагы тамактар"

    def __str__(self):
        return f"{self.dish.name} × {self.quantity}"
