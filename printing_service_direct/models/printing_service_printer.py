from odoo import fields, models


class PrintingServicePrinter(models.Model):
    _name = "printing.service.printer"
    _description = "Print Service Printer"
    _order = "name"

    name = fields.Char(required=True)
    service_id = fields.Many2one(
        "printing.service", required=True, ondelete="cascade"
    )
    printer_uuid = fields.Char(
        required=True,
        help="UUID of this printer in the print service",
    )
    printer_type = fields.Selection(
        [("document", "Document / Laser"), ("label", "Label / Thermal")],
        required=True,
        default="document",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("printer_uuid_uniq", "unique(printer_uuid)", "Printer UUID must be unique."),
    ]
