import re
import json
import pytz
import base64
from odoo import models, fields, api, _
from odoo.tools import html_escape, float_is_zero
from odoo.exceptions import AccessError,UserError
from odoo.addons.iap import jsonrpc
from io import StringIO
import logging
from datetime import datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

DEFAULT_IAP_ENDPOINT = "https://l10n-in-edi.api.odoo.com"
DEFAULT_IAP_TEST_ENDPOINT = "https://l10n-in-edi-demo.api.odoo.com"


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    @api.model
    def _l10n_in_edi_connect_to_server(self, service, url_path, params):
        user_token = self.env["iap.account"].get("l10n_in_edi")
        IrConfigParam = self.env["ir.config_parameter"].sudo()
        params.update({
            "account_token": user_token.account_token,
            "dbuuid": self.env["ir.config_parameter"].sudo().get_param("database.uuid"),
            "username": service.gstn_username,
            "gstin": service.gstin,
        })
        gsp_provider = IrConfigParam.get_param("l10n_in.gsp_provider")
        if gsp_provider:
            params.update({"gsp_provider": gsp_provider})
        if self.env.company.sudo().l10n_in_edi_production_env:
            default_endpoint = DEFAULT_IAP_ENDPOINT
        else:
            default_endpoint = DEFAULT_IAP_TEST_ENDPOINT
        endpoint = self.env["ir.config_parameter"].sudo().get_param("l10n_in_edi.endpoint", default_endpoint)
        url = "%s%s" % (endpoint, url_path)
        try:
            response = jsonrpc(url, params=params, timeout=25)
            if response and not response.get("error"):
                if not service.token_validity:
                    service.token_validity = fields.Datetime.to_datetime(
                        response["data"]["TokenExpiry"]
                    ) - timedelta(hours=5, minutes=30, seconds=00)
                    service.token = response["data"]["AuthToken"]
            return response
        except AccessError as e:
            _logger.warning("Connection error: %s", e.args[0])
            return {
                "error": [{
                    "code": "404",
                    "message": _("Unable to connect to the online E-invoice service."
                                 "The web service may be temporary down. Please try again in a moment.")
                }]
            }