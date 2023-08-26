from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FOManual(models.TransientModel):
    _name = "forecast.order"
    _description = "Forecast Order"

    forecast_order_ids = fields.One2many("forecast.order.line", "forecast_order_id")

    def action_fo_confirm(self):
        active_fo_id = self.env.context.get('active_id')
        current_fo = self.env["sale.order"].browse(active_fo_id)
        fo_backorder_lines = {}
        top_priority_so_vals = {}
        medium_priority_so_vals = {}
        low_priority_so_vals = {}
        top_priority_location = []
        medium_priority_location = []
        low_priority_location = []
        received = 0
        unlink_lines = []

        for rec in self.forecast_order_ids:
            if rec.total_received_qty <= rec.demand_qty and rec.total_received_qty > 0 and rec.demand_qty > 0:
                rec.so_line_id.product_uom_qty = rec.total_received_qty
                received += rec.total_received_qty
                if rec.top_priority_stock > 0:
                    if rec.top_priority_warehouse not in top_priority_location:
                        top_priority_location.append(rec.top_priority_warehouse)
                    if rec.so_line_id not in top_priority_so_vals:
                        top_priority_so_vals[rec.so_line_id] = rec.top_priority_stock
                    else:
                        top_priority_so_vals[rec.so_line_id] += rec.top_priority_stock
                if rec.medium_priority_stock > 0:
                    if rec.medium_priority_warehouse not in medium_priority_location:
                        medium_priority_location.append(rec.medium_priority_warehouse)
                    if rec.so_line_id not in medium_priority_so_vals:
                        medium_priority_so_vals[rec.so_line_id] = rec.medium_priority_stock
                    else:
                        medium_priority_so_vals[rec.so_line_id] += rec.medium_priority_stock
                if rec.low_priority_stock > 0:
                    if rec.low_priority_warehouse not in low_priority_location:
                        low_priority_location.append(rec.low_priority_warehouse)
                    if rec.so_line_id not in low_priority_so_vals:
                        low_priority_so_vals[rec.so_line_id] = rec.low_priority_stock
                    else:
                        low_priority_so_vals[rec.so_line_id] += rec.low_priority_stock

                if rec.total_received_qty < rec.demand_qty and rec.demand_qty > 0:
                    remaining_qty = rec.demand_qty - rec.total_received_qty
                    if rec.so_line_id not in fo_backorder_lines:
                        fo_backorder_lines[rec.so_line_id] = remaining_qty
                    else:
                        fo_backorder_lines[rec.so_line_id] += remaining_qty
            elif rec.total_received_qty == 0 and rec.demand_qty > 0:
                if rec.so_line_id not in fo_backorder_lines:
                    fo_backorder_lines[rec.so_line_id] = rec.demand_qty
                else:
                    fo_backorder_lines[rec.so_line_id] += rec.demand_qty
                if rec.so_line_id not in unlink_lines:
                    unlink_lines.append(rec.so_line_id)

        fo_backorder_line_lst = []

        if received != 0:
            for fo_b_line, fo_b_qty in fo_backorder_lines.items():
                fo_bo_line_vals = (0, 0, {
                    'product_id': fo_b_line.product_id.id,
                    'product_template_id': fo_b_line.product_template_id.id,
                    'name': fo_b_line.name,
                    'product_uom_qty': fo_b_qty,
                    'product_uom': fo_b_line.product_uom.id,
                    'price_unit': fo_b_line.price_unit,
                    'tax_id': [(4, tax_id.id) for tax_id in fo_b_line.tax_id] if fo_b_line.tax_id else False,
                    'discount': fo_b_line.discount,
                    'hsn_id': fo_b_line.hsn_id.id,
                })
                fo_backorder_line_lst.append(fo_bo_line_vals)
        fo_bo_vals = {
            'is_fo': True,
            'partner_id': current_fo.partner_id.id,
            'l10n_in_gst_treatment': current_fo.l10n_in_gst_treatment,
            'partner_invoice_id': current_fo.partner_invoice_id.id,
            'partner_shipping_id': current_fo.partner_shipping_id.id,
            'pricelist_id': current_fo.pricelist_id.id,
            'payment_term_id': current_fo.payment_term_id.id,
            'l10n_in_journal_id': current_fo.l10n_in_journal_id.id,
            'event': current_fo.event,
            'no_of_cartons': current_fo.no_of_cartons,
            'user_id': current_fo.user_id.id,
            'team_id': current_fo.team_id.id,
            'order_line': fo_backorder_line_lst
        }
        if len(fo_backorder_line_lst) > 0:
            fo_bo_id = self.env["sale.order"].create(fo_bo_vals)
            for unlink_line in unlink_lines:
                unlink_line.unlink()
            current_fo.write({'state': 'done'})

        if len(top_priority_so_vals) > 0:
            top_priority_so_line_lst = []
            for top_priority_so_line, qty in top_priority_so_vals.items():
                top_priority_so_line_vals = (0, 0, {
                    'product_id': top_priority_so_line.product_id.id,
                    'product_template_id': top_priority_so_line.product_template_id.id,
                    'name': top_priority_so_line.name,
                    'product_uom_qty': qty,
                    'product_uom': top_priority_so_line.product_uom.id,
                    'price_unit': top_priority_so_line.price_unit,
                    'tax_id': [(4, tax_id.id) for tax_id in top_priority_so_line.tax_id] if top_priority_so_line.tax_id else False,
                    'discount': top_priority_so_line.discount,
                    'hsn_id': top_priority_so_line.hsn_id.id,
                })
                top_priority_so_line_lst.append(top_priority_so_line_vals)
            top_priority_so_vals = {
                'is_fo': False,
                'partner_id': current_fo.partner_id.id,
                'l10n_in_gst_treatment': current_fo.l10n_in_gst_treatment,
                'partner_invoice_id': current_fo.partner_invoice_id.id,
                'partner_shipping_id': current_fo.partner_shipping_id.id,
                'pricelist_id': current_fo.pricelist_id.id,
                'payment_term_id': current_fo.payment_term_id.id,
                'l10n_in_journal_id': current_fo.l10n_in_journal_id.id,
                'event': current_fo.event,
                'no_of_cartons': current_fo.no_of_cartons,
                'user_id': current_fo.user_id.id,
                'team_id': current_fo.team_id.id,
                'warehouse_id': top_priority_location[0].warehouse_id.id,
                'location_id': top_priority_location[0].id,
                'order_line': top_priority_so_line_lst,
            }
            if len(top_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(top_priority_so_vals)

        if len(medium_priority_so_vals) > 0:
            medium_priority_so_line_lst = []
            for medium_priority_so_line, qty in medium_priority_so_vals.items():
                medium_priority_so_line_vals = (0, 0, {
                    'product_id': medium_priority_so_line.product_id.id,
                    'product_template_id': medium_priority_so_line.product_template_id.id,
                    'name': medium_priority_so_line.name,
                    'product_uom_qty': qty,
                    'product_uom': medium_priority_so_line.product_uom.id,
                    'price_unit': medium_priority_so_line.price_unit,
                    'tax_id': [(4, tax_id.id) for tax_id in medium_priority_so_line.tax_id] if medium_priority_so_line.tax_id else False,
                    'discount': medium_priority_so_line.discount,
                    'hsn_id': medium_priority_so_line.hsn_id.id,
                })
                medium_priority_so_line_lst.append(medium_priority_so_line_vals)
            medium_priority_so_vals = {
                'is_fo': False,
                'partner_id': current_fo.partner_id.id,
                'l10n_in_gst_treatment': current_fo.l10n_in_gst_treatment,
                'partner_invoice_id': current_fo.partner_invoice_id.id,
                'partner_shipping_id': current_fo.partner_shipping_id.id,
                'pricelist_id': current_fo.pricelist_id.id,
                'payment_term_id': current_fo.payment_term_id.id,
                'l10n_in_journal_id': current_fo.l10n_in_journal_id.id,
                'event': current_fo.event,
                'no_of_cartons': current_fo.no_of_cartons,
                'user_id': current_fo.user_id.id,
                'team_id': current_fo.team_id.id,
                'warehouse_id': medium_priority_location[0].warehouse_id.id,
                'location_id': medium_priority_location[0].id,
                'order_line': medium_priority_so_line_lst,
            }
            if len(medium_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(medium_priority_so_vals)

        if len(low_priority_so_vals) > 0:
            low_priority_so_line_lst = []
            for low_priority_so_line, qty in low_priority_so_vals.items():
                medium_priority_so_line_vals = (0, 0, {
                    'product_id': low_priority_so_line.product_id.id,
                    'product_template_id': low_priority_so_line.product_template_id.id,
                    'name': low_priority_so_line.name,
                    'product_uom_qty': qty,
                    'product_uom': low_priority_so_line.product_uom.id,
                    'price_unit': low_priority_so_line.price_unit,
                    'tax_id': [(4, tax_id.id) for tax_id in low_priority_so_line.tax_id] if low_priority_so_line.tax_id else False,
                    'discount': low_priority_so_line.discount,
                    'hsn_id': low_priority_so_line.hsn_id.id,
                })
                low_priority_so_line_lst.append(medium_priority_so_line_vals)
            low_priority_so_vals = {
                'is_fo': False,
                'partner_id': current_fo.partner_id.id,
                'l10n_in_gst_treatment': current_fo.l10n_in_gst_treatment,
                'partner_invoice_id': current_fo.partner_invoice_id.id,
                'partner_shipping_id': current_fo.partner_shipping_id.id,
                'pricelist_id': current_fo.pricelist_id.id,
                'payment_term_id': current_fo.payment_term_id.id,
                'l10n_in_journal_id': current_fo.l10n_in_journal_id.id,
                'event': current_fo.event,
                'no_of_cartons': current_fo.no_of_cartons,
                'user_id': current_fo.user_id.id,
                'team_id': current_fo.team_id.id,
                'warehouse_id': low_priority_location[0].warehouse_id.id,
                'location_id': low_priority_location[0].id,
                'order_line': low_priority_so_line_lst,
            }
            if len(low_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(low_priority_so_vals)


class FOLineManual(models.TransientModel):
    _name = "forecast.order.line"
    _description = "Forecast Order Line"

    forecast_order_id = fields.Many2one("forecast.order", "Forecast Order")
    product_id = fields.Many2one("product.product", "Product")
    so_line_id = fields.Many2one("sale.order.line", "SO Line")
    demand_qty = fields.Float("Demand")
    top_priority_stock = fields.Float("Received", help="Receive Qty From Top Priority Warehouse")
    medium_priority_stock = fields.Float("Received", help="Receive Qty From Medium Priority Warehouse")
    low_priority_stock = fields.Float("Received", help="Receive Qty From Low Priority Warehouse")
    top_priority_warehouse = fields.Many2one("stock.location", "TPW", help="Top Priority Warehouse")
    medium_priority_warehouse = fields.Many2one("stock.location", "MPW", help="Medium Priority Warehouse")
    low_priority_warehouse = fields.Many2one("stock.location", "LPW", help="Low Priority Warehouse")
    top_priority_qty_avail = fields.Float("TPAQ", help="Top Priority Stock Available")
    medium_priority_qty_avail = fields.Float("MPAQ", help="Medium Priority Stock Available")
    low_priority_qty_avail = fields.Float("LPAQ", help="Low Priority Stock Available")
    total_received_qty = fields.Float("Total Qty Received", compute="_compute_total_qty_received")

    @api.depends("top_priority_stock", "medium_priority_stock", "low_priority_stock")
    def _compute_total_qty_received(self):
        for rec in self:
            rec.top_priority_stock = abs(rec.top_priority_stock)
            rec.medium_priority_stock = abs(rec.medium_priority_stock)
            rec.low_priority_stock = abs(rec.low_priority_stock)
            if (rec.top_priority_stock > rec.top_priority_qty_avail) or (rec.medium_priority_stock > rec.medium_priority_qty_avail) or (rec.low_priority_stock > rec.low_priority_qty_avail):
                raise ValidationError("You cannot receive more than what is currently in stock.")
            rec.total_received_qty = rec.top_priority_stock + rec.medium_priority_stock + rec.low_priority_stock