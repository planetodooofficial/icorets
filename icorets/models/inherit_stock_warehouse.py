from odoo import models, api, fields, _


class InheritStockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    priority = fields.Selection(
        [
            ('1', 'High priority'),
            ('2', 'Medium priority'),
            ('3', 'Low priority')
        ], string='Priority')