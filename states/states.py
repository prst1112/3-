from aiogram.fsm.state import State, StatesGroup


class DealCreate(StatesGroup):
    choosing_currency = State()
    entering_amount = State()
    entering_description = State()


class BuyerPay(StatesGroup):
    waiting_screenshot = State()


class RequisiteAdd(StatesGroup):
    entering_card_country = State()
    entering_value = State()
