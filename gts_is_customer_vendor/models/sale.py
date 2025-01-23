# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.sale.models.sale_order import READONLY_FIELD_STATES


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # partner_id = fields.Many2one(
    #     'res.partner', string='Customer', readonly=True,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     required=True, change_default=True, index=True, tracking=1,
    #     domain="['|',('customer_rank','>', 0),('is_customer','=',True)]", )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True, readonly=False, change_default=True, index=True,
        tracking=1,
        domain="[('company_id', 'in', (False, company_id)),'|',('customer_rank','>', 0),('is_customer','=',True)]")
