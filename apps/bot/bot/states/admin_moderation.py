from aiogram.fsm.state import State, StatesGroup


class AdminModerationStates(StatesGroup):
    reject_reason = State()
    changes_reason = State()
