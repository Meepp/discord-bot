class CustomEmoji:
    jimbo = "<:Jimbo:432177172686569502>"
    arrow_left = "◀️"
    arrow_right = "▶️"
    dani = "<:dani:805154104740806706>"
    omegalul = "<:OmegaLUL:422863487086231552>"
    pepohmm = "<:pepoHmm:860221819205976085>"
    rat = "<:xdd:930502955159920761>"
    worrysusge = "<:worrysusge:934224455067123723>"
    sussy = "<a:sussy:938104411866152970>"
    monkasteer = "<a:monkaSTEER:860219322554908742>"
    mods = "<a:MODS:922515013141401702>"

    def lookup_emote(self, emote):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        for member in members:
            if member == emote:
                return getattr(self, member)