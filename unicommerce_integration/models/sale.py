from odoo import models, fields, api, _


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    unicommerce_order_id = fields.Many2one('unicommerce.orders', string='Unicommerce Order Id')
    shop_instance_id = fields.Many2one('shop.instance', string='Shop Instance')
    sales_channel_id = fields.Many2one('shop.sales.channel', string='Sales Channel')
    dump_sequence = fields.Char(string='Sequence')
