from math import ceil

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from schemas.telegram import TelegramEventType, TelegramScopeType
from telegram_bot.handlers.common import safe_edit_text
from telegram_bot.keyboards import (
    BUTTON_SUBSCRIPTIONS,
    CALLBACK_SUBSCRIPTIONS,
    CALLBACK_SUBS_ADD_AUDIENCE,
    CALLBACK_SUBS_ADD_OFFICE,
    CALLBACK_SUBS_DELETE_MENU,
    CALLBACK_SUBS_TOGGLE_SECURITY,
    build_subscription_delete_keyboard,
    build_subscription_event_keyboard,
    build_subscription_scope_keyboard,
    build_subscriptions_inline_keyboard,
)
from telegram_bot.services import (
    TelegramBotAccountFacade,
    TelegramBotScopeOption,
    TelegramBotSubscriptionFacade,
    TelegramBotSubscriptionSnapshot,
)
from telegram_bot.texts import (
    GENERIC_ERROR_TEXT,
    render_event_label,
    render_scope_label,
    render_subscription_delete_text,
    render_subscription_event_choice_text,
    render_subscription_result_text,
    render_subscription_scope_choice_text,
    render_subscriptions_text,
)

router = Router(name="subscriptions")
account_facade = TelegramBotAccountFacade()
subscription_facade = TelegramBotSubscriptionFacade()

OPTIONS_PAGE_SIZE = 8


def _is_auth_security_enabled(subscriptions: list[TelegramBotSubscriptionSnapshot]) -> bool:
    return any(
        item.enabled and item.scope_type == "user" and item.event_type == "auth_security"
        for item in subscriptions
    )


def _paginate(items: list, page: int, page_size: int = OPTIONS_PAGE_SIZE) -> tuple[list, int, int]:
    total_pages = max(1, ceil(max(1, len(items)) / page_size))
    normalized_page = min(max(page, 1), total_pages)
    start = (normalized_page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages, normalized_page


def _scope_type_from_code(scope_code: str):
    if scope_code == "a":
        return TelegramScopeType.audience
    if scope_code == "o":
        return TelegramScopeType.office
    raise ValueError("Unsupported scope code")


def _event_type_from_code(event_code: str):
    if event_code == "f":
        return TelegramEventType.hardware_fault
    if event_code == "r":
        return TelegramEventType.hardware_recovered
    raise ValueError("Unsupported event code")


async def _show_subscriptions(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Telegram subscriptions request received without from_user")
        await message.answer(GENERIC_ERROR_TEXT)
        return

    snapshot = await account_facade.get_snapshot(telegram_id=message.from_user.id)
    await message.answer(
        render_subscriptions_text(snapshot),
        reply_markup=build_subscriptions_inline_keyboard(
            auth_security_enabled=_is_auth_security_enabled(snapshot.subscriptions),
        ),
    )


async def _edit_subscriptions(call: CallbackQuery, *, success_answer: str | None = None) -> None:
    if call.from_user is None:
        await call.answer()
        return

    snapshot = await account_facade.get_snapshot(telegram_id=call.from_user.id)
    await safe_edit_text(
        call,
        text=render_subscriptions_text(snapshot),
        reply_markup=build_subscriptions_inline_keyboard(
            auth_security_enabled=_is_auth_security_enabled(snapshot.subscriptions),
        ),
        success_answer=success_answer,
    )


async def _edit_event_choice(call: CallbackQuery, *, scope_code: str) -> None:
    scope_label = render_scope_label(_scope_type_from_code(scope_code).value)
    await safe_edit_text(
        call,
        text=render_subscription_event_choice_text(scope_label=scope_label),
        reply_markup=build_subscription_event_keyboard(scope_code=scope_code),
    )


async def _edit_scope_choice(call: CallbackQuery, *, scope_code: str, event_code: str, page: int) -> None:
    if scope_code == "a":
        all_options = await subscription_facade.list_audience_options()
    else:
        all_options = await subscription_facade.list_office_options()

    options, total_pages, normalized_page = _paginate(all_options, page)
    scope_label = render_scope_label(_scope_type_from_code(scope_code).value)
    event_label = render_event_label(_event_type_from_code(event_code).value)

    await safe_edit_text(
        call,
        text=render_subscription_scope_choice_text(
            scope_label=scope_label,
            event_label=event_label,
            page=normalized_page,
            total_pages=total_pages,
        ),
        reply_markup=build_subscription_scope_keyboard(
            options=options,
            scope_code=scope_code,
            event_code=event_code,
            page=normalized_page,
            total_pages=total_pages,
        ),
    )


async def _edit_delete_menu(call: CallbackQuery, *, page: int) -> None:
    if call.from_user is None:
        await call.answer()
        return

    snapshot = await account_facade.get_snapshot(telegram_id=call.from_user.id)
    active_subscriptions = [item for item in snapshot.subscriptions if item.enabled]
    page_items, total_pages, normalized_page = _paginate(active_subscriptions, page)

    await safe_edit_text(
        call,
        text=render_subscription_delete_text(
            active_count=len(active_subscriptions),
            page=normalized_page,
            total_pages=total_pages,
        ),
        reply_markup=build_subscription_delete_keyboard(
            subscriptions=page_items,
            page=normalized_page,
            total_pages=total_pages,
        ),
    )


@router.message(Command("subscriptions"))
@router.message(F.text == BUTTON_SUBSCRIPTIONS)
async def subscriptions_handler(message: Message) -> None:
    await _show_subscriptions(message)


@router.callback_query(F.data == CALLBACK_SUBSCRIPTIONS)
async def subscriptions_callback(call: CallbackQuery) -> None:
    await _edit_subscriptions(call)


@router.callback_query(F.data == CALLBACK_SUBS_ADD_AUDIENCE)
async def add_audience_subscription_callback(call: CallbackQuery) -> None:
    await _edit_event_choice(call, scope_code="a")


@router.callback_query(F.data == CALLBACK_SUBS_ADD_OFFICE)
async def add_office_subscription_callback(call: CallbackQuery) -> None:
    await _edit_event_choice(call, scope_code="o")


@router.callback_query(F.data.startswith("subs:event:"))
async def subscription_event_callback(call: CallbackQuery) -> None:
    _, _, scope_code, event_code = (call.data or "").split(":")
    await _edit_scope_choice(call, scope_code=scope_code, event_code=event_code, page=1)


@router.callback_query(F.data.startswith("subs:page:"))
async def subscription_page_callback(call: CallbackQuery) -> None:
    _, _, scope_code, event_code, page_value = (call.data or "").split(":")
    await _edit_scope_choice(
        call,
        scope_code=scope_code,
        event_code=event_code,
        page=int(page_value),
    )


@router.callback_query(F.data.startswith("subs:create:"))
async def subscription_create_callback(call: CallbackQuery) -> None:
    if call.from_user is None:
        await call.answer()
        return

    _, _, scope_code, event_code, scope_id = (call.data or "").split(":")
    result = await subscription_facade.create_subscription(
        telegram_id=call.from_user.id,
        scope_type=_scope_type_from_code(scope_code),
        scope_id=int(scope_id),
        event_type=_event_type_from_code(event_code),
    )
    await _edit_subscriptions(
        call,
        success_answer=render_subscription_result_text(result),
    )


@router.callback_query(F.data == CALLBACK_SUBS_TOGGLE_SECURITY)
async def toggle_security_subscription_callback(call: CallbackQuery) -> None:
    if call.from_user is None:
        await call.answer()
        return

    result = await subscription_facade.toggle_auth_security(telegram_id=call.from_user.id)
    await _edit_subscriptions(
        call,
        success_answer=render_subscription_result_text(result),
    )


@router.callback_query(F.data.startswith("subs:delete:"))
async def subscription_delete_menu_callback(call: CallbackQuery) -> None:
    _, _, page_value = (call.data or "").split(":")
    await _edit_delete_menu(call, page=int(page_value))


@router.callback_query(F.data.startswith("subs:del:"))
async def subscription_delete_callback(call: CallbackQuery) -> None:
    if call.from_user is None:
        await call.answer()
        return

    _, _, subscription_id = (call.data or "").split(":")
    result = await subscription_facade.delete_subscription(
        telegram_id=call.from_user.id,
        subscription_id=int(subscription_id),
    )
    await _edit_subscriptions(
        call,
        success_answer=render_subscription_result_text(result),
    )
