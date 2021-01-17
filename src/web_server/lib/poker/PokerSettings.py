class PokerSettingsDefaults:
    SMALL_BLIND_VALUE = 2
    MAX_BUY_IN = 20000


class PokerSettings:
    def __init__(self, settings: dict):
        self.small_blind_value = int(settings.get("small_blind_value", PokerSettingsDefaults.SMALL_BLIND_VALUE))
        self.max_buy_in = int(settings.get("max_buy_in", PokerSettingsDefaults.MAX_BUY_IN))

    def to_json(self):
        return {
            "small_blind_value": self.small_blind_value,
            "max_buy_in": self.max_buy_in
        }
