from odoo import models, fields, api, _


class StockPickings(models.Model):
    _inherit = 'stock.picking'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)

    def change_warehouse(self):
        action = self.env["ir.actions.act_window"]._for_xml_id('gts_stock.action_select_warehouse_wizard_menu')
        return action
