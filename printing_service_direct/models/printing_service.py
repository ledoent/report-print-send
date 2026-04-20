import base64
import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PrintingService(models.Model):
    _name = "printing.service"
    _description = "Print Service Connection"

    name = fields.Char(required=True, default="Print Service")
    url = fields.Char(
        required=True,
        help="Base URL of the print service, e.g. https://print-service.hz.ledoweb.com",
    )
    api_key = fields.Char(required=True)
    active = fields.Boolean(default=True)
    printer_ids = fields.One2many(
        "printing.service.printer", "service_id", string="Printers"
    )

    def _request(self, method, path, **kwargs):
        self.ensure_one()
        url = self.url.rstrip("/") + path
        headers = kwargs.pop("headers", {})
        headers["X-API-Key"] = self.api_key
        try:
            response = requests.request(
                method, url, headers=headers, timeout=15, **kwargs
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            raise UserError(_("Print service error: %s") % detail) from e
        except requests.exceptions.RequestException as e:
            raise UserError(_("Could not reach print service: %s") % e) from e
        return response

    def action_test_connection(self):
        self.ensure_one()
        self._request("GET", "/healthz")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Connection to %s successful.") % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_refresh_printers(self):
        self.ensure_one()
        response = self._request("GET", "/api/v1/printers")
        printers_data = response.json()
        Printer = self.env["printing.service.printer"]
        synced = 0
        for p in printers_data:
            if not p.get("is_active"):
                continue
            printer_uuid = str(p["id"])
            printer_type = "label" if p.get("printer_type") == "zpl" else "document"
            vals = {
                "name": p["name"],
                "service_id": self.id,
                "printer_uuid": printer_uuid,
                "printer_type": printer_type,
            }
            existing = Printer.search([("printer_uuid", "=", printer_uuid)], limit=1)
            if existing:
                existing.write(vals)
            else:
                Printer.create(vals)
            synced += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Synced %d printer(s) from %s.") % (synced, self.name),
                "type": "success",
                "sticky": False,
            },
        }

    def post_job(self, printer_uuid, payload_b64, title=None, external_id=None):
        self.ensure_one()
        body = {
            "printer_id": printer_uuid,
            "content_type": "pdf_base64",
            "payload": payload_b64,
        }
        if title:
            body["title"] = title
        if external_id:
            body["external_id"] = external_id
        response = self._request("POST", "/api/v1/jobs", json=body)
        return response.json()
