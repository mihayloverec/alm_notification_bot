"""All user-facing strings (RU)."""

# Общие
START_GREETING = (
    "Привет! Я бот уведомлений турниров.\n\n"
    "Подпишись на интересующие турниры, и я буду присылать тебе обновления."
)
MAIN_MENU = "Главное меню:"
BACK = "⬅️ Назад"
CANCEL = "❌ Отмена"
BTN_TO_MAIN_MENU = "🏠 Главное меню"
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
ORGANIZER_MENU = "📢 Меню организатора:"
BTN_ADMIN_ADD = "➕ Добавить турнир"
BTN_ADMIN_MANAGE = "📝 Управление турнирами"
BTN_ADMIN_BROADCAST = "📢 Рассылка"
BTN_ADMIN_PLAYERS = "👥 Игроки"
BTN_ADMIN_ORGANIZERS = "👨‍💼 Организаторы"

# Игроки (админ)
PLAYERS_LIST_HEADER = "Игроки: всего <b>{total}</b>, страница <b>{page}/{pages}</b>"
PLAYERS_LIST_EMPTY = "Пока никто не запускал бота."
BTN_PREV_PAGE = "◀️"
BTN_NEXT_PAGE = "▶️"
BTN_SEARCH = "🔍 Поиск"
SEARCH_ENTER_QUERY = (
    "Введите запрос для поиска по @username, имени или Telegram ID:"
)
SEARCH_RESULTS_HEADER = "Найдено: <b>{n}</b>"
SEARCH_NO_RESULTS = "По запросу «{q}» ничего не найдено."

PLAYER_CARD = (
    "👤 <b>{display_name}</b>\n"
    "ID: <code>{user_id}</code>\n"
    "{username_line}"
    "Регистрация: {created_at}\n"
    "Статус: {status}\n"
    "Подписок: <b>{subs}</b>"
)
PLAYER_STATUS_OK = "🟢 активен"
PLAYER_STATUS_BLOCKED = "⚪ заблокировал бота"
PLAYER_STATUS_BANNED = "🚫 забанен"
BTN_BAN = "🚫 Забанить"
BTN_UNBAN = "♻️ Разбанить"
BTN_PLAYER_ADD_SUB = "➕ Подписать на турнир"
BTN_PLAYER_SUBS = "📋 Подписки игрока"
PLAYER_BANNED = "Игрок забанен."
PLAYER_UNBANNED = "Игрок разбанен."
PLAYER_SELF_BAN_FORBIDDEN = "Нельзя забанить самого себя."
PLAYER_CHOOSE_TOURNAMENT = "Выберите турнир для подписки:"
PLAYER_SUBSCRIBED = "Игрок подписан на «{name}»."
PLAYER_NO_SUBS = "У игрока нет подписок."
PLAYER_SUBS_LIST = "Подписки игрока:"
PLAYER_UNSUBSCRIBED = "Подписка на «{name}» снята."
NO_ACTIVE_TOURNAMENTS_ADMIN = "Сейчас нет активных турниров. Сначала создай или открой турнир."

# Бан игрока — что видит сам игрок
BANNED_NOTICE = "Вы заблокированы администратором."

# Обращения (пользователь)
BTN_INQUIRY_SK = "📨 Обратиться в СК"
BTN_INQUIRY_DK = "📨 Обратиться в ДК"
INQUIRY_LABEL = {"sk": "СК", "dk": "ДК"}
INQUIRY_UNAVAILABLE = "Обращение в {label} временно недоступно — получатели не настроены."
INQUIRY_ENTER_MESSAGE = (
    "Опишите ваше обращение в {label}.\n\n"
    "Можно прислать текст, фото или документ с подписью. "
    "Сообщение будет переслано получателям как есть."
)
INQUIRY_PREVIEW = "👆 Превью обращения выше.\n\nОтправить?"
INQUIRY_SENT = "✅ Обращение в {label} отправлено."
INQUIRY_SEND_FAILED = "⚠️ Не удалось доставить ни одному получателю. Попробуйте позже."
INQUIRY_HEADER = (
    "📨 Новое обращение [<b>{label}</b>]\n"
    "От: {username_line}"
    "ID: <code>{user_id}</code>\n"
    "Имя: {first_name}"
)

# Действия получателя над обращением
INQUIRY_RECIPIENT_BTN_REPLY = "📩 Ответить"
INQUIRY_RECIPIENT_BTN_BAN = "🚫 Забанить"
INQUIRY_ACTION_NOT_AUTHORIZED = (
    "Только получатель обращения или админ может это сделать."
)

INQUIRY_REPLY_PROMPT = (
    "Напишите ответ игроку. Можно прислать текст, фото или документ "
    "с подписью и форматированием. Игрок получит ответ через бота."
)
INQUIRY_REPLY_SENT = "✅ Ответ доставлен."
INQUIRY_REPLY_FAILED = (
    "⚠️ Не удалось доставить ответ (возможно, игрок заблокировал бота)."
)
INQUIRY_REPLY_HEADER = "✉️ Ответ на ваше обращение в <b>{label}</b>:"

INQUIRY_BAN_CONFIRM = (
    "Забанить отправителя?\n\n"
    "Игрок будет полностью заблокирован — не сможет писать боту, "
    "не получит никаких рассылок. Разбанить сможет только админ."
)
INQUIRY_BAN_DONE = "🚫 Игрок забанен."
INQUIRY_BAN_CANCELLED = "Бан отменён."
INQUIRY_BAN_SELF_FORBIDDEN = "Нельзя забанить самого себя."
INQUIRY_BAN_ADMIN_FORBIDDEN = "Нельзя забанить администратора."

# Обращения (админ)
BTN_ADMIN_INQUIRY = "📨 Получатели обращений"
INQUIRY_ADMIN_MENU = "Получатели обращений — выберите тип:"
BTN_INQUIRY_ADMIN_SK = "📋 СК"
BTN_INQUIRY_ADMIN_DK = "📋 ДК"
INQUIRY_ADMIN_LIST_HEADER = "Получатели <b>{label}</b>: <b>{n}</b>"
INQUIRY_ADMIN_LIST_EMPTY = "Получатели <b>{label}</b> не настроены."
BTN_INQUIRY_ADD = "➕ Добавить"
INQUIRY_PICK_HEADER = "Выберите игрока для добавления в <b>{label}</b> (стр. {page}/{pages}):"
INQUIRY_PICK_EMPTY = "Нет ни одного игрока — список пуст."
INQUIRY_RECIPIENT_ADDED = "Добавлен в получатели {label}."
INQUIRY_RECIPIENT_ALREADY = "Этот игрок уже в получателях {label}."
INQUIRY_RECIPIENT_REMOVE_CONFIRM = "Удалить {who} из получателей {label}?"
INQUIRY_RECIPIENT_REMOVED = "Удалён из получателей {label}."
BTN_YES = "Да"
BTN_NO = "Нет"

# Организаторы (только админ)
ORGANIZERS_LIST_HEADER = "Организаторы: <b>{n}</b>"
ORGANIZERS_LIST_EMPTY = "Организаторов нет."
BTN_ORGANIZER_ADD = "➕ Добавить организатора"
BTN_ORGANIZER_SEARCH = "🔍 По @username / ID"
ORGANIZER_PICK_HEADER = "Выберите игрока (стр. {page}/{pages}) или введите вручную:"
ORGANIZER_PICK_EMPTY = "Игроков нет — попросите кандидата сначала запустить бота (/start)."
ORGANIZER_SEARCH_PROMPT = (
    "Введите @username (можно без @), имя или Telegram ID. "
    "Кандидат должен быть зарегистрирован в боте (хоть раз сделал /start)."
)
ORGANIZER_SEARCH_NOT_FOUND = "По запросу «{q}» ничего не найдено."
ORGANIZER_SEARCH_RESULTS = "Найдено: <b>{n}</b>. Выберите кандидата:"
ORGANIZER_ADDED = "Добавлен в организаторы."
ORGANIZER_ALREADY = "Этот игрок уже организатор."
ORGANIZER_REMOVE_CONFIRM = "Снять {who} с роли организатора?"
ORGANIZER_REMOVED = "Снят с роли организатора."

# Кастомные кнопки меню (только админ)
BTN_ADMIN_MENU_BUTTONS = "📌 Кнопки меню"
MENU_BUTTONS_LIST_HEADER = "Кастомные кнопки в главном меню: <b>{n}</b>"
MENU_BUTTONS_LIST_EMPTY = "Кастомные кнопки не настроены."
BTN_MENU_BUTTON_ADD = "➕ Добавить кнопку"
MENU_BUTTON_CARD = (
    "Кнопка #{id}\n"
    "Текст: {text}\n"
    "URL: <code>{url}</code>"
)
MENU_BUTTON_ENTER_TEXT = (
    "Введите текст кнопки (можно с эмодзи в начале, например «📺 Стрим»):"
)
MENU_BUTTON_ENTER_URL = (
    "Введите URL — должен начинаться с http:// или https://:"
)
MENU_BUTTON_INVALID_URL = "URL должен начинаться с http:// или https://. Введите ещё раз:"
MENU_BUTTON_TEXT_EMPTY = "Текст не может быть пустым. Введите ещё раз:"
MENU_BUTTON_ADDED = "Кнопка добавлена."
MENU_BUTTON_UPDATED = "Кнопка обновлена."
MENU_BUTTON_DELETED = "Кнопка удалена."
BTN_MENU_BUTTON_EDIT_TEXT = "✏️ Текст"
BTN_MENU_BUTTON_EDIT_URL = "✏️ URL"
BTN_MENU_BUTTON_UP = "⬆️"
BTN_MENU_BUTTON_DOWN = "⬇️"
BTN_MENU_BUTTON_DELETE = "🗑 Удалить"
MENU_BUTTON_DELETE_CONFIRM = "Удалить кнопку «{text}»?"

# Кнопки в рассылке (per-broadcast)
BTN_BROADCAST_ADD_BUTTON = "➕ Добавить кнопку"
BTN_BROADCAST_RESET_BUTTONS = "🗑 Сбросить кнопки"
BROADCAST_PREVIEW_WITH_BUTTONS = (
    "👆 Превью сообщения выше.\n\n"
    "Получателей: <b>{count}</b>\n"
    "Кнопок: <b>{buttons}</b>\n\n"
    "Отправить?"
)
BROADCAST_BUTTON_ENTER_TEXT = (
    "Введите текст кнопки (можно с эмодзи):"
)
BROADCAST_BUTTON_ENTER_URL = (
    "Введите URL — должен начинаться с http:// или https://:"
)
BROADCAST_BUTTONS_RESET = "Кнопки сброшены."

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
