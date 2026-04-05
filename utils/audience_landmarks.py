from schemas.audience import AudienceLandmarks


def normalize_landmarks(data: dict | None) -> dict:
    parsed = AudienceLandmarks.model_validate(data or {})

    result = parsed.model_dump(exclude_none=True)

    # убираем пустые строки, если фронт их прислал
    result = {
        k: v.strip()
        for k, v in result.items()
        if isinstance(v, str) and v.strip()
    }

    return result