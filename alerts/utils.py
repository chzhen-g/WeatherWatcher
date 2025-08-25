def matches_conditions(snapshot, conditions: dict) -> bool:
    if not conditions:
        return True
    if "temp_below" in conditions and not (snapshot.temp < conditions["temp_below"]):
        return False
    if "temp_above" in conditions and not (snapshot.temp > conditions["temp_above"]):
        return False
    if conditions.get("rain") is True:
        raw = snapshot.raw or {}
        has_rain = "rain" in raw or any(w.get("main") == "Rain" for w in raw.get("weather", []))
        if not has_rain:
            return False
    return True
