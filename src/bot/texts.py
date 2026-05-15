"""All user-facing strings (RU)."""

# Общие
START_GREETING = (
    "Привет! Я бот уведомлений турниров.\n\n"
    "Подпишись на интересующие турниры, и я буду присылать тебе обновления."
)
MAIN_MENU = "Главное меню:"
BACK = "⬅️ Назад"
CANCEL = "❌ Отмена"
CANCELLED = "Отменено."
NO_ACTIVE_TOURNAMENTS = "Сейчас нет активных турниров."
NO_SUBSCRIPTIONS = "У тебя пока нет подписок."
NOT_AUTHORIZED = "Команда недоступна."

# Пользовательские кнопки
BTN_TOURNAMENTS = "📋 Турниры"
BTN_MY_SUBS = "✅ Мои подписки"
BTN_SUBSCRIBE = "➕ Подписаться"
BTN_UNSUBSCRIBE = "➖ Отписаться"

def render_card(name: str, description: str, *, closed: bool = False) -> str:
    import html

    safe_name = html.escape(name)
    label = " [Закрыт]" if closed else ""
    body = description if description else "—"
    return f"<b>{safe_name}</b>{label}\n\n{body}"
SUBSCRIBED = "✅ Подписка оформлена."
UNSUBSCRIBED = "❎ Подписка отменена."

# Админ
ADMIN_MENU = "🛠 Админ-меню:"
BTN_ADMIN_ADD = "➕ Добавить турнир"
BTN_ADMIN_MANAGE = "📝 Управление турнирами"
BTN_ADMIN_BROADCAST = "📢 Рассылка"

# Добавление турнира
ADD_ENTER_NAME = "Введите название турнира:"
ADD_ENTER_DESCRIPTION = (
    "Введите описание турнира (можно использовать markdown-форматирование):"
)
ADD_PREVIEW = "Превью карточки:\n\n{card}\n\nСохранить?"
ADD_SAVED = "Турнир добавлен."
BTN_SAVE = "✅ Сохранить"

# Редактирование
BTN_EDIT_NAME = "✏️ Название"
BTN_EDIT_DESCRIPTION = "✏️ Описание"
BTN_CLOSE = "🔒 Закрыть"
BTN_OPEN = "🔓 Открыть"
EDIT_ENTER_NAME = "Введите новое название:"
EDIT_ENTER_DESCRIPTION = "Введите новое описание:"
EDIT_SAVED = "Изменения сохранены."
TOURNAMENT_OPENED = "Турнир открыт."
TOURNAMENT_CLOSED = "Турнир закрыт."

# Рассылка
BROADCAST_CHOOSE_AUDIENCE = "Выберите аудиторию для рассылки:"
BTN_AUDIENCE_ALL = "👥 Все пользователи"
BROADCAST_SEND_MESSAGE = (
    "Пришлите сообщение для рассылки.\n\n"
    "Можно использовать markdown-форматирование и одну картинку (с подписью). "
    "Сообщение будет скопировано получателям как есть."
)
BROADCAST_PREVIEW = "👆 Превью сообщения выше.\n\nПолучателей: <b>{count}</b>.\n\nОтправить?"
BTN_SEND = "✅ Отправить"
BROADCAST_NO_RECIPIENTS = "Получателей нет. Рассылка не запущена."
BROADCAST_STARTED = "Рассылка запущена. Жди отчёт по завершении."
BROADCAST_REPORT = (
    "📬 Рассылка завершена.\n\n"
    "✅ Отправлено: <b>{sent}</b>\n"
    "🚫 Заблокировали бота: <b>{blocked}</b>\n"
    "⚠️ Ошибки: <b>{errors}</b>"
)
