import datetime

from odoo import models, api, fields, _


class ShortClose(models.Model):
    _name = 'short.close'

    reason_id = fields.Many2one('reason.reason')
    desc = fields.Char('Description')

    def confirm_short_close(self):
        active_id = self.env.context.get("active_id")
        print(active_id)
        search_so = self.env['sale.order'].search([('id', '=', active_id)])

        search_so.reason_id = self.reason_id
        search_so.desc = self.desc
        search_so.closer_date = fields.Datetime.now()
        search_so.is_short_close = True

        for rec in search_so.picking_ids:
            if rec.state not in ['done','cancel']:
                rec.action_cancel()

        for line in search_so.order_line:
            line.product_uom_qty = line.qty_delivered

