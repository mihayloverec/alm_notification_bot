from aiogram.fsm.state import State, StatesGroup


class AddTournament(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_confirm = State()


class EditTournamentName(StatesGroup):
    waiting_for_value = State()


class EditTournamentDescription(StatesGroup):
    waiting_for_value = State()


class Broadcast(StatesGroup):
    waiting_for_audience = State()
    waiting_for_message = State()
    waiting_for_confirm = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()


class SearchPlayers(StatesGroup):
    waiting_for_query = State()


class Inquiry(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()


class AddOrganizer(StatesGroup):
    waiting_for_query = State()


class AddMenuButton(StatesGroup):
    waiting_for_text = State()
    waiting_for_url = State()


class EditMenuButtonText(StatesGroup):
    waiting_for_value = State()


class EditMenuButtonUrl(StatesGroup):
    waiting_for_value = State()
