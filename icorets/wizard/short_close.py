import datetime

from odoo import models, api, fields, _


class ShortClose(models.Model):
    _name = 'short.close'

    reason_id = fields.Many2one('reason.reason')
    desc = fields.Char('Description')

    def confirm_short_close(self):

        if self.env.context.get('sale_order_ids'):
            to_browse = self.env.context.get('sale_order_ids')
        else:
            to_browse = self.env.context.get("active_ids")

        # active_id = self.env.context.get("active_id")
        # print(active_id)
        # search_so = self.env['sale.order'].search([('id', '=', active_id)])
        search_so = self.env['sale.order'].browse(to_browse)

        for sale in search_so:
            sale.reason_id = self.reason_id
            sale.desc = self.desc
            sale.closer_date = fields.Datetime.now()
            sale.is_short_close = True

            for rec in sale.picking_ids:
                if rec.state not in ['done','cancel']:
                    rec.action_cancel()

            for line in sale.order_line:
                line.product_uom_qty = line.qty_delivered

