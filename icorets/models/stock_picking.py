from odoo import models, fields, api, _


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    def get_report_xlsx(self):
        return self.env.ref('icorets.get_sale_order_xls').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for picking in res:
            if picking.origin:
                stock_transfers_search = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if stock_transfers_search and stock_transfers_search.location_id:
                    picking.location_id = stock_transfers_search.location_id.id
        return res

    def update_picking_list_wizard(self):
        return {
            'name': 'Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'packing.list.manual',
            'view_mode': 'form',
            'view_id': self.env.ref('icorets.view_bag_entry_manual_wizard_form').id,
            'target': 'new',
        }


class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for line in res:
            if line.origin:
                stock_transfers_search = self.env['sale.order'].search([('name', '=', line.origin)], limit=1)
                if stock_transfers_search and line.picking_id and line.picking_id.location_id:
                    line.location_id = line.picking_id.location_id.id
        return res
