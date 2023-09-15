from odoo import models, fields, api, _, Command


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', copy=False)

    def action_confirm(self):
        # create a purchase order for the sale order when it's confirmed
        res = super(InheritSaleOrder, self).action_confirm()
        for record in self:
            purchase_order = self.env['purchase.order'].search([('sale_order_id', '=', record.id)])
            if record.state == 'sale' and record.partner_id.is_gstin and not purchase_order:
                lst = list()
                for line in self.order_line:
                    po_line = line.prepare_purchase_order_line()
                    lst.append((0, 0, po_line))
                customer_journal_id = self.env['account.journal'].search([('type', '=', 'purchase'),
                                                                          ('l10n_in_gstin_partner_id', '=', self.partner_id.id),
                                                                          ('interbranch', '=', True)], limit=1)
                vendor_id = self.l10n_in_journal_id.l10n_in_gstin_partner_id
                purchase_order = self.env['purchase.order'].create({
                    'partner_id': vendor_id.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    'origin': record.name,
                    'date_order': record.date_order,
                    'state': 'draft',
                    'l10n_in_journal_id': customer_journal_id.id,
                    'gstin_id': customer_journal_id.l10n_in_gstin_partner_id.id,
                    'payment_term_id': record.payment_term_id.id,
                    'warehouse_id': record.warehouse_id.id,
                    'user_id': record.user_id.id,
                    'l10n_in_gst_treatment': record.l10n_in_gst_treatment,
                    'fiscal_position_id': record.fiscal_position_id.id,
                    'order_line': lst,
                })
                purchase_order.update({'sale_order_id': self.id})
                self.update({'purchase_order_id': purchase_order.id})
                purchase_order.button_confirm()

    def open_purchase_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            # 'domain': [('id', '=', self.purchase_order_id.id)],
            'res_id': self.purchase_order_id.id,
            'context': "{'create': False}"
        }


class InheritSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def prepare_purchase_order_line(self):
        self.ensure_one()
        res = {
            'article_code': self.article_code,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'hsn_id': self.hsn_id.id,
            'taxes_id': [Command.set(self.tax_id.ids)],
        }
        return res
