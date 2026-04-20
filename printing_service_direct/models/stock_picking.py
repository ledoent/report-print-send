import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        result = super().button_validate()
        if result is True:
            self.sudo()._trigger_service_print()
        return result

    def _trigger_service_print(self):
        rules = self.env["printing.service.rule"].search(
            [("active", "=", True)], order="sequence"
        )
        if not rules:
            return
        for picking in self:
            for rule in rules.filtered(lambda r: r._matches(picking)):
                rule._execute(picking)
