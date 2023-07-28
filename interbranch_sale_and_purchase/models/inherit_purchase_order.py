from odoo import models, fields, api, _, Command


class InheritPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', copy=False)

    def button_confirm(self):
        res = super(InheritPurchaseOrder, self).button_confirm()
        for record in self:
            sale_order = self.env['sale.order'].search([('purchase_order_id', '=', record.id)])
            if record.state == 'purchase' and record.partner_id.is_gstin and not sale_order:
                lst = list()
                for line in self.order_line:
                    so_line = line.prepare_sale_order_line()
                    lst.append((0, 0, so_line))
                partner_id = self.gstin_id
                vendor_journal_id = self.env['account.journal'].search([('type', '=', 'sale'),
                                                                         ('l10n_in_gstin_partner_id', '=', self.partner_id.id),
                                                                         ('interbranch', '=', True),
                                                                        ('default_account_id', '!=', False)], limit=1)
                sale_order = self.env['sale.order'].create({
                    'partner_id': partner_id.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.currency_id.id,
                    'origin': record.name,
                    'date_order': record.date_order,
                    'state': 'draft',
                    'l10n_in_journal_id': vendor_journal_id.id,
                    'gstin_id': record.partner_id.id,
                    'payment_term_id': record.payment_term_id.id,
                    'warehouse_id': record.warehouse_id.id,
                    'user_id': record.user_id.id,
                    'l10n_in_gst_treatment': record.l10n_in_gst_treatment,
                    'fiscal_position_id': record.fiscal_position_id.id,
                    'order_line': lst,
                })
                sale_order.update({'purchase_order_id': self.id})
                self.update({'sale_order_id': sale_order.id})
                sale_order.action_confirm()

    def open_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'view_mode': 'form',
            'res_model': 'sale.order',
            # 'domain': [('id', '=', self.purchase_order_id.id)],
            'res_id': self.sale_order_id.id,
            'context': "{'create': False}"
        }





class InheritPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def prepare_sale_order_line(self):
        self.ensure_one()
        res = {
            'article_code': self.article_code,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_qty,
            'price_unit': self.price_unit,
            'hsn_id': self.hsn_id.id,
            'tax_id': [Command.set(self.taxes_id.ids)],
        }
        return res