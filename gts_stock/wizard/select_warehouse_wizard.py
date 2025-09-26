from odoo import models, fields, api, _
import base64


class SelectWarehouseWizard(models.TransientModel):
    _name = 'select.warehouse.wizard'

    company_id = fields.Many2one("res.company", string="Company", readonly=False, default=lambda self: self.env.company)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    location_id = fields.Many2one("stock.location", string="Location", tracking=True)

    def update_warehouse(self):
        if self.env.context.get('active_id'):
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if picking:
                picking.update({
                    'warehouse_id': self.warehouse_id.id,
                    'location_id': self.location_id.id,
                })
                if picking.move_ids:
                    for move in picking.move_ids:
                        move.update({
                            'location_id': self.location_id.id
                        })
                if picking.move_line_ids:
                    for line in picking.move_line_ids:
                        line.update({
                            'location_id': self.location_id.id
                        })

                picking.action_assign()

