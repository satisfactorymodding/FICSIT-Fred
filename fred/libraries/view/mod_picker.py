import logging

import nextcord.ui


class ModPicker(nextcord.ui.View):
    def __init__(self, mods: list[dict]):
        super().__init__()
        self.select = ModSelect()
        for mod in mods:
            self.select.add_mod_option(mod)
        self.add_item(self.select)

    def set_callback(self, callback):
        self.select.callback = callback


class ModSelect(nextcord.ui.Select):
    def __init__(self):
        super().__init__()

    def add_mod_option(self, mod: dict):
        self.add_option(label=mod.get("name"))
