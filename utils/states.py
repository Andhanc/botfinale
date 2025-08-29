from aiogram.fsm.state import State, StatesGroup


class AiForm(StatesGroup):
    budget = State()
    coins = State()
    energy = State()
    other = State()


class SellForm(StatesGroup):
    device = State()
    price = State()
    condition = State()
    description = State()
    contact = State()


class CalculatorState(StatesGroup):
    choose_method = State()
    choose_manufacturer = State()
    choose_asic_model = State()
    choose_algorithm = State()
    input_hashrate = State()
    input_power = State()
    input_electricity_price = State()
    show_result = State()


class FreeAiState(StatesGroup):
    chat = State()


class ClientPriceNegotiation(StatesGroup):
    waiting_photo = State()
    waiting_comment = State()
    waiting_confirm = State()
    sent_ok = State()


class AdminBroadcast(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    waiting_confirm = State()
    sending = State()


class BetterPriceState(StatesGroup):
    waiting_photo = State()
    waiting_comment = State()
    waiting_confirm = State()
