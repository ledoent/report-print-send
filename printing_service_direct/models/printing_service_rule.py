import base64
import logging

from odoo import _, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class PrintingServiceRule(models.Model):
    _name = "printing.service.rule"
    _description = "Print Service Auto-Print Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    picking_type_code = fields.Selection(
        [
            ("", "Any"),
            ("incoming", "Receipt"),
            ("outgoing", "Delivery"),
            ("internal", "Internal Transfer"),
        ],
        default="",
        string="Operation Type",
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Specific Operation",
        help="Optional: further narrow the rule to a specific operation type.",
    )
    domain = fields.Char(
        default="[]",
        help="Extra ORM domain filter evaluated against stock.picking records.",
    )
    report_id = fields.Many2one(
        "ir.actions.report",
        required=True,
        string="Report",
        domain=[("model", "=", "stock.picking")],
    )
    printer_id = fields.Many2one(
        "printing.service.printer", required=True, string="Printer"
    )
    copies = fields.Integer(default=1)

    def _matches(self, picking):
        self.ensure_one()
        if self.picking_type_code and self.picking_type_code != picking.picking_type_code:
            return False
        if self.picking_type_id and self.picking_type_id != picking.picking_type_id:
            return False
        if self.domain and self.domain != "[]":
            try:
                domain = safe_eval(self.domain)
                if not picking.filtered_domain(domain):
                    return False
            except Exception:
                _logger.warning(
                    "Rule %s: invalid domain %r, skipping domain filter",
                    self.name,
                    self.domain,
                )
        return True

    def _execute(self, picking):
        self.ensure_one()
        report = self.report_id
        printer = self.printer_id
        try:
            pdf_bytes, _ = report.sudo()._render(picking.ids)
            payload_b64 = base64.b64encode(pdf_bytes).decode()
            title = f"{report.name} - {picking.name}"
            for _ in range(max(1, self.copies)):
                printer.service_id.post_job(
                    printer_uuid=printer.printer_uuid,
                    payload_b64=payload_b64,
                    title=title,
                    external_id=picking.name,
                )
            _logger.info(
                "Printed %s × %d via rule '%s' on picker '%s'",
                picking.name,
                self.copies,
                self.name,
                printer.name,
            )
        except Exception:
            _logger.warning(
                "Print rule '%s' failed for picking %s",
                self.name,
                picking.name,
                exc_info=True,
            )
