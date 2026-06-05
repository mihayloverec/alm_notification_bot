from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    action: str  # "tournaments" | "my_subs" | "admin" | "main"


class TournamentCB(CallbackData, prefix="t"):
    action: str  # "view" | "sub" | "unsub" (user); "manage" | "toggle" | "edit_name" | "edit_desc" (admin)
    tournament_id: int


class AdminCB(CallbackData, prefix="adm"):
    action: str  # "add" | "manage" | "broadcast"


class AddTournamentCB(CallbackData, prefix="addt"):
    action: str  # "save" | "cancel"


class BroadcastCB(CallbackData, prefix="bc"):
    action: str  # "all" | "tournament" | "send" | "cancel"
    tournament_id: int = 0  # 0 = "all" / неприменимо


class PlayersCB(CallbackData, prefix="pl"):
    action: str  # "list" | "page" | "search"
    page: int = 0


class PlayerCB(CallbackData, prefix="p"):
    action: str  # "view" | "ban" | "unban" | "sub_list" | "sub" | "subs" | "unsub"
    user_id: int
    tournament_id: int = 0  # для sub / unsub


class InquiryUserCB(CallbackData, prefix="iu"):
    action: str  # "start" | "send" | "cancel"
    type: str = ""  # "sk" | "dk"


class InquiryAdminCB(CallbackData, prefix="ia"):
    action: str  # "menu" | "list" | "add" | "page" | "pick" | "del" | "del_yes"
    type: str = ""
    user_id: int = 0
    page: int = 0


class OrganizerCB(CallbackData, prefix="og"):
    action: str  # "list" | "add" | "page" | "pick" | "search" | "del" | "del_yes"
    user_id: int = 0
    page: int = 0
