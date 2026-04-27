from schemas.telegram import TelegramEventType
from utils.telegram_format import code, h


class TelegramNotificationRenderer:
    def build_hardware_state_message(
        self,
        *,
        hardware_id: int,
        audience_id: int,
        event_type: TelegramEventType,
        hardware_type: str | None = None,
        title: str | None = None,
        description: str | None = None,
        inv_number: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> str:
        if event_type == TelegramEventType.hardware_fault:
            header = "🚨 <b>Неисправность оборудования</b>"
        elif event_type == TelegramEventType.hardware_recovered:
            header = "✅ <b>Оборудование восстановлено</b>"
        else:
            raise ValueError(f"Unsupported telegram event type: {event_type}")

        lines = [
            header,
            "",
            f"Аудитория: {code(audience_id)}",
            f"Оборудование: {code(hardware_id)}",
        ]
        if hardware_type:
            lines.append(f"Тип: {h(self._render_hardware_type(hardware_type))}")
        if x is not None and y is not None:
            lines.append(f"Место: ряд {y + 1}, позиция {x + 1}")
        if title:
            lines.append(f"Название: {h(title)}")
        if description:
            lines.append(f"Комментарий: {h(description)}")
        if inv_number:
            lines.append(f"Инвентарный номер: {code(inv_number)}")

        return "\n".join(lines)

    def build_auth_security_message(
        self,
        *,
        event_name: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        title, details = self._render_auth_security_event(event_name)
        lines = [title, details]
        if ip:
            lines.append(f"IP: {code(ip)}")
        if user_agent:
            lines.append(f"Устройство: {h(user_agent)}")

        return "\n".join(lines)

    @staticmethod
    def _render_hardware_type(hardware_type: str) -> str:
        return {
            "computer": "компьютер",
            "tv": "телевизор",
            "projector": "проектор",
            "printer": "принтер",
            "switch": "коммутатор",
            "router": "роутер",
            "server": "сервер",
            "other": "другое",
        }.get(hardware_type, hardware_type)

    @staticmethod
    def _render_auth_security_event(event_name: str) -> tuple[str, str]:
        normalized_name = event_name.strip().lower()
        if normalized_name == "выполнен вход в аккаунт":
            return (
                "🔐 <b>Вход в аккаунт</b>",
                "В ваш аккаунт выполнен новый вход.",
            )
        if normalized_name == "изменён пароль аккаунта":
            return (
                "🔑 <b>Пароль изменён</b>",
                "Пароль вашего аккаунта был изменён.",
            )
        if normalized_name == "выполнен выход на всех устройствах":
            return (
                "🚪 <b>Выход на всех устройствах</b>",
                "Все активные сессии были завершены.",
            )
        return (
            "🛡 <b>Событие безопасности аккаунта</b>",
            h(event_name),
        )
