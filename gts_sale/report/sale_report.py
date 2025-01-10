from odoo import models, fields, api


class SaleReport(models.Model):
    _inherit = "sale.report"

    client_order_ref = fields.Char(string="P O No")

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['client_order_ref'] = "s.client_order_ref"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            s.client_order_ref"""
        return res
