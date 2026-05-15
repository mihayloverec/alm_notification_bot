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
