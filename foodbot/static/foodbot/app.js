
document.addEventListener("DOMContentLoaded", () => {
    const particles = document.getElementById("particles");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const sendButton = chatForm.querySelector(".send-button");
    const clearChat = document.getElementById("clearChat");

    // 1. Animated background particles
    if (particles) {
        const fragment = document.createDocumentFragment();

        for (let i = 0; i < 48; i++) {
            const particle = document.createElement("span");
            particle.className = "particle";
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animationDuration = `${8 + Math.random() * 15}s`;
            particle.style.animationDelay = `${-Math.random() * 20}s`;

            if (Math.random() > 0.65) {
                particle.style.width = "2px";
                particle.style.height = "2px";
            }

            fragment.appendChild(particle);
        }

        particles.appendChild(fragment);
    }

    // 2. Scroll reveal animations
    const revealElements = document.querySelectorAll(
        ".stat-card, .feature-card, .chat-section .section-heading"
    );

    revealElements.forEach((element) => {
        element.classList.add("reveal");
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealElements.forEach((element) => observer.observe(element));
    } else {
        revealElements.forEach((element) => element.classList.add("visible"));
    }

    // 3. Smooth navigation
    function scrollToSection(id) {
        const section = document.getElementById(id);
        if (section) {
            section.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    document.getElementById("startChat").addEventListener("click", () => {
        scrollToSection("chat");
        setTimeout(() => chatInput.focus(), 500);
    });

    document.getElementById("chatNav").addEventListener("click", () => {
        scrollToSection("chat");
    });

    document.getElementById("homeNav").addEventListener("click", () => {
        scrollToSection("home");
    });

    document.getElementById("menuNav").addEventListener("click", () => {
        scrollToSection("menu");
    });

    document.getElementById("exploreMenu").addEventListener("click", () => {
        scrollToSection("menu");
    });

    // 4. Highlight navigation while scrolling
    const navButtons = {
        home: document.getElementById("homeNav"),
        menu: document.getElementById("menuNav"),
        chat: document.getElementById("chatNav")
    };

    if ("IntersectionObserver" in window) {
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    Object.values(navButtons).forEach((button) => {
                        button.classList.remove("active");
                    });

                    if (navButtons[entry.target.id]) {
                        navButtons[entry.target.id].classList.add("active");
                    }
                }
            });
        }, { rootMargin: "-20% 0px -65% 0px" });

        ["home", "menu", "chat"].forEach((id) => {
            const section = document.getElementById(id);
            if (section) sectionObserver.observe(section);
        });
    }

    // 5. Chat message helpers
    function addMessage(text, sender) {
        const wrapper = document.createElement("div");
        wrapper.className = sender === "user"
            ? "message user-message"
            : "message assistant-message";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = sender === "user" ? "YOU" : "✳";

        const body = document.createElement("div");
        body.className = "message-body";

        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = sender === "user" ? "YOU" : "SMART AI";

        const time = document.createElement("span");
        time.textContent = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });
        name.appendChild(time);

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = text;

        body.append(name, bubble);
        wrapper.append(avatar, body);
        chatMessages.appendChild(wrapper);

        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });

        return wrapper;
    }

    function showTyping() {
        const wrapper = document.createElement("div");
        wrapper.className = "message assistant-message typing-message";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "✳";

        const body = document.createElement("div");
        body.className = "message-body";

        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = "SMART AI";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        const dots = document.createElement("div");
        dots.className = "typing-dots";

        for (let i = 0; i < 3; i++) {
            dots.appendChild(document.createElement("span"));
        }

        bubble.appendChild(dots);
        body.append(name, bubble);
        wrapper.append(avatar, body);
        chatMessages.appendChild(wrapper);

        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });

        return wrapper;
    }

    // 6. Send messages to Django backend
    let isSending = false;

    async function sendMessage(text) {
        text = text.trim();

        if (!text || isSending) return;

        isSending = true;
        chatInput.value = "";
        chatInput.disabled = true;
        sendButton.disabled = true;

        addMessage(text, "user");
        const typing = showTyping();

        try {
            const csrfToken = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;

            const response = await fetch("/api/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {})
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            typing.remove();

            if (!response.ok) {
                throw new Error(data.error || data.detail || "Серверде ката кетти.");
            }

            addMessage(
                data.reply || data.response || "AI жооп берген жок.",
                "assistant"
            );
        } catch (error) {
            typing.remove();

            addMessage(
                "Азыр жооп алуу мүмкүн болгон жок. Django API жана AI серверинин иштеп жатканын текшер. (" +
                error.message + ")",
                "assistant"
            );

            console.error("Chat error:", error);
        } finally {
            isSending = false;
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        }
    }

    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage(chatInput.value);
    });

    // 7. Quick prompt cards
    document.querySelectorAll("[data-prompt]").forEach((button) => {
        button.addEventListener("click", () => {
            const prompt = button.dataset.prompt;
            scrollToSection("chat");
            chatInput.value = prompt;
            chatInput.focus();
        });
    });

    // 8. Clear chat and restore welcome message
    clearChat.addEventListener("click", () => {
        chatMessages.replaceChildren();

        addMessage(
            "Салам! Мен Smart School FoodBot жардамчысымын. Мектеп менюсу, тамак-аш жана туура тамактануу боюнча кандай сурооң бар?",
            "assistant"
        );

        chatInput.focus();
    });

    console.log("Smart School AI FoodBot interface initialized.");
});

/* SMART SCHOOL: корзина жана заказ функциялары */
(() => {
    const foodGrid = document.getElementById("foodGrid");
    const cartList = document.getElementById("cartList");
    const cartEmpty = document.getElementById("cartEmpty");
    const cartTotal = document.getElementById("cartTotal");
    const clearCartButton = document.getElementById("clearCart");
    const orderForm = document.getElementById("orderForm");
    const orderMessage = document.getElementById("orderMessage");
    const foodSearch = document.getElementById("foodSearch");
    const foodCategory = document.getElementById("foodCategory");

    if (!foodGrid || !cartList || !orderForm) return;

    const cart = new Map();

    function renderCart() {
        cartList.replaceChildren();
        let total = 0;

        cart.forEach((item, id) => {
            total += item.price * item.quantity;

            const row = document.createElement("li");
            row.className = "cart-row";

            const info = document.createElement("div");
            const name = document.createElement("strong");
            name.textContent = item.name;

            const details = document.createElement("div");
            details.textContent =
                `${item.price.toFixed(2)} сом × ${item.quantity}`;

            info.append(name, details);

            const controls = document.createElement("div");

            const minus = document.createElement("button");
            minus.type = "button";
            minus.textContent = "−";
            minus.setAttribute("aria-label", `${item.name} санын азайтуу`);
            minus.addEventListener("click", () => {
                if (item.quantity <= 1) {
                    cart.delete(id);
                } else {
                    item.quantity--;
                }
                renderCart();
            });

            const plus = document.createElement("button");
            plus.type = "button";
            plus.textContent = "+";
            plus.setAttribute("aria-label", `${item.name} санын көбөйтүү`);
            plus.addEventListener("click", () => {
                if (item.quantity < 100) item.quantity++;
                renderCart();
            });

            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "×";
            remove.setAttribute("aria-label", `${item.name} алып салуу`);
            remove.addEventListener("click", () => {
                cart.delete(id);
                renderCart();
            });

            controls.append(minus, plus, remove);
            row.append(info, controls);
            cartList.appendChild(row);
        });

        cartTotal.textContent = total.toFixed(2);
        cartEmpty.hidden = cart.size > 0;
    }

    foodGrid.addEventListener("click", (event) => {
        const button = event.target.closest("[data-add-dish]");
        if (!button) return;

        const card = button.closest(".food-card");
        if (!card) return;

        const id = card.dataset.id;
        const name = card.dataset.name;
        const price = Number(card.dataset.price);

        if (!id || !name || !Number.isFinite(price) || price < 0) {
            alert("Тамак тууралуу маалымат туура эмес.");
            return;
        }

        if (cart.has(id)) {
            const item = cart.get(id);
            if (item.quantity >= 100) {
                alert("Бир тамактан эң көп 100 даана тандай аласыз.");
                return;
            }
            item.quantity++;
        } else {
            cart.set(id, { name, price, quantity: 1 });
        }

        renderCart();

        button.textContent = "✓ Кошулду";
        setTimeout(() => {
            button.textContent = "＋ Корзинага кошуу";
        }, 900);
    });

    clearCartButton?.addEventListener("click", () => {
        cart.clear();
        renderCart();
        orderMessage.textContent = "";
    });

    function filterFoods() {
        const query = (foodSearch?.value || "").trim().toLowerCase();
        const category = foodCategory?.value || "";

        foodGrid.querySelectorAll(".food-card").forEach((card) => {
            const name = (card.dataset.name || "").toLowerCase();
            const description =
                (card.querySelector("p")?.textContent || "").toLowerCase();

            const matchesText =
                name.includes(query) || description.includes(query);
            const matchesCategory =
                !category || card.dataset.category === category;

            card.hidden = !(matchesText && matchesCategory);
        });
    }

    foodSearch?.addEventListener("input", filterFoods);
    foodCategory?.addEventListener("change", filterFoods);

    orderForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (cart.size === 0) {
            orderMessage.textContent = "Алгач корзинага тамак кошуңуз.";
            return;
        }

        const submitButton = orderForm.querySelector(
            'button[type="submit"]'
        );
        const formData = new FormData(orderForm);

        const payload = {
            customer_name: formData.get("customer_name"),
            class_name: formData.get("class_name"),
            phone: formData.get("phone"),
            note: formData.get("note"),
            items: Array.from(cart.entries()).map(([id, item]) => ({
                dish_id: Number(id),
                quantity: item.quantity
            }))
        };

        const csrfToken = orderForm.querySelector(
            "[name=csrfmiddlewaretoken]"
        )?.value;

        submitButton.disabled = true;
        orderMessage.textContent = "Заказ жөнөтүлүүдө...";

        try {
            const response = await fetch("/api/order/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {})
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.reply || "Заказ кабыл алынган жок.");
            }

            orderMessage.textContent =
                `${data.message} Жалпы сумма: ${data.total_price} сом.`;

            cart.clear();
            renderCart();
            orderForm.reset();
        } catch (error) {
            orderMessage.textContent = error.message;
            console.error("Order error:", error);
        } finally {
            submitButton.disabled = false;
        }
    });

    renderCart();
    console.log("Smart School cart initialized.");
})();

