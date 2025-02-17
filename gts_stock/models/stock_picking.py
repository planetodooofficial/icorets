from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class StockPickings(models.Model):
    _inherit = 'stock.picking'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    bulk_return_id = fields.Many2one('stock.picking', string="Bulk Return ID")

    def change_warehouse(self):
        action = self.env["ir.actions.act_window"]._for_xml_id('gts_stock.action_select_warehouse_wizard_menu')
        return action

    def _prepare_picking_default_values(self):
        selected_pickings = self.env.context.get('selected_pickings')
        selected_name = ', '.join(pick.name for pick in selected_pickings)
        vals = {
            'move_ids': [],
            'picking_type_id': self.picking_type_id.return_picking_type_id.id or self.picking_type_id.id,
            'state': 'draft',
            # 'origin': _("Return of %s") % self.name,
            'origin': _("Return of %s") % selected_name,
        }
        if self.location_dest_id:
            vals['location_id'] = self.location_dest_id.id
        if self.location_id:
            vals['location_dest_id'] = self.location_id.id
        return vals

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.product_uom_qty,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.id,
            'procure_method': 'make_to_stock',
        }
        if new_picking.picking_type_id.code == 'outgoing':
            vals['partner_id'] = new_picking.partner_id.id
        return vals


    def bulk_grn_return(self):
        customers = self.mapped('partner_id')
        if len(customers) > 1:
            raise UserError("Please select GRN with same Customer")

        new_picking = self[0].copy(self[0].with_context({'selected_pickings': self})._prepare_picking_default_values())

        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self[0]},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        returned_lines = 0

        for stock_picking in self:
            for move in stock_picking.move_ids:
                if move.product_uom_qty:
                    returned_lines += 1
                    vals = stock_picking._prepare_move_default_values(move, new_picking)
                    r = move.copy(vals)
                    vals = {}

                    move_orig_to_link = move.move_dest_ids.mapped('returned_move_ids')
                    move_orig_to_link |= move
                    move_orig_to_link |= move \
                        .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel')) \
                        .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                    move_dest_to_link = move.move_orig_ids.mapped('returned_move_ids')
                    move_dest_to_link |= move.move_orig_ids.mapped('returned_move_ids') \
                        .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel')) \
                        .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                    vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                    vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                    r.write(vals)

            stock_picking.bulk_return_id = new_picking.id

        if not returned_lines:
            raise UserError(_("Please check the GRN lines."))

        new_picking.action_confirm()

    def view_bulk_return_picking(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Picking',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.bulk_return_id.id,
            'target': 'current',
            'view_id': self.env.ref('stock.view_picking_form').id,
        }

