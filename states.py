from aiogram.fsm.state import StatesGroup, State


class OrderStates(StatesGroup):
    choosing_package = State()
    confirming_package = State()
    waiting_ff_id = State()
    waiting_payment = State()


class BalanceTopupStates(StatesGroup):
    waiting_check = State()


class AdminStates(StatesGroup):
    waiting_custom_message = State()


class AdminOrderEditStates(StatesGroup):
    select_field = State()
    edit_value = State()


class AdminBalanceTopupStates(StatesGroup):
    waiting_amount = State()


class AdminManualMoneyBalanceStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()


class WithdrawStates(StatesGroup):
    waiting_amount = State()
    waiting_ff_id = State()


class WithdrawEdit(StatesGroup):
    waiting_text = State()


class AdminWithdrawEditStates(StatesGroup):
    waiting_text = State()


class AdminMenuStates(StatesGroup):
    menu = State()


class AdminEditPricesStates(StatesGroup):
    waiting_text = State()


class AdminPackagesStates(StatesGroup):
    menu = State()
    add_name = State()
    add_almaz = State()
    add_price = State()

    edit_select = State()
    edit_field = State()
    edit_value = State()

    delete_select = State()


class AdminContactTextStates(StatesGroup):
    waiting_text = State()


class VoucherStates(StatesGroup):
    choosing_quantity = State()


class AdminOrdersStates(StatesGroup):
    waiting_order_id = State()


class AdminUserSearchStates(StatesGroup):
    waiting_query = State()


class AdminVouchersStates(StatesGroup):
    menu = State()

    edit_select = State()
    edit_field = State()
    edit_value = State()


class PromoCodeStates(StatesGroup):
    waiting_code = State()


class AdminPromoStates(StatesGroup):
    menu = State()

    add_code = State()
    add_almaz = State()
    add_max_uses = State()
    add_expire = State()


class AdminBroadcastStates(StatesGroup):
    waiting_message = State()


class AdminMainMenuPhotoStates(StatesGroup):
    waiting_photo = State()


class AdminRoleStates(StatesGroup):
    menu = State()
    add_id = State()
    add_role = State()
    edit_select = State()
    edit_role = State()
    remove_select = State()


class AdminPaymentCardsStates(StatesGroup):
    menu = State()
    add_number = State()
    add_holder = State()
    add_bank = State()
    add_sort = State()
    add_active = State()
    edit_select = State()
    edit_field = State()
    edit_value = State()
    delete_select = State()
    activate_select = State()
    deactivate_select = State()


class AdminLogChatStates(StatesGroup):
    menu = State()
    set_chat_id = State()
    set_mode = State()


class BonusCodeStates(StatesGroup):
    menu = State()
    waiting_code_input = State()


class AdminStatsStates(StatesGroup):
    menu = State()
    detail = State()


class MainMenuTextEditState(StatesGroup):
    waiting_text = State()


class AdminContentButtonStates(StatesGroup):
    menu = State()
    add_label = State()
    add_content = State()
    edit_select = State()
    edit_content = State()
    delete_select = State()


from aiogram.fsm.state import StatesGroup, State


class ChanManage(StatesGroup):
    ADD = State()
    REMOVE = State()
