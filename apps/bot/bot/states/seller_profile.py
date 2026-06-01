from aiogram.fsm.state import State, StatesGroup


class SellerProfileStates(StatesGroup):
    display_name = State()
    bio = State()
    contact_username = State()


class ProductCreationStates(StatesGroup):
    title = State()
    description = State()
    language = State()
    level = State()
    category = State()
    audience = State()
    price = State()
    product_file = State()
    previews = State()
    confirm = State()
