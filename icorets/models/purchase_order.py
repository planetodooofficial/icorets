from odoo import models, fields, api, _
from odoo.tools import get_lang, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_round


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    is_approve = fields.Boolean('Is Approve')

    reason_id = fields.Many2one('reason.reason')
    desc = fields.Char('Description')
    is_short_close = fields.Boolean(store=True)
    closer_date = fields.Datetime()


    # Onchange for selecting warehouse
    @api.onchange('picking_type_id')
    def onchange_delivery_name(self):
        for rec in self:
            return {'domain': {'warehouse_id': [('id', '=', rec.picking_type_id.warehouse_id.id)]}}

    # For getting user which used approve button in purchase order in pdf
    def button_approve(self, force=False):
        res = super(PurchaseOrderInherit, self).button_approve()
        self.is_approve = True
        return res

    def short_close(self):
        view = self.env.ref('icorets.view_short_close_wizard')
        return {
            'name': 'Short Close',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'short.close',
            'view_id': view.id,
            'target': 'new',
        }

    def short_close_purchase_order(self):
        view = self.env.ref('icorets.view_short_close_wizard')
        return {
            'name': 'Short Close',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'short.close',
            'view_id': view.id,
            'target': 'new',
            'context': {
                'purchase_order_ids': self.ids
            }
        }

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrderInherit, self)._prepare_invoice()
        invoice_vals['gstin_id'] = self.gstin_id.id
        invoice_vals['journal_id'] = self.l10n_in_journal_id.id
        return invoice_vals


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    tax_amount_line = fields.Monetary(string='Total Amount', readonly=True,
                                      compute="check_tax_amount", currency_field='currency_id')

    remark = fields.Text('Remarks')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.purchase_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')
    color = fields.Char(string='Color', related='product_id.color')

    @api.depends('product_qty', 'product_uom_id', 'product_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.product_id:
                product = line.product_id
                if product.default_code:
                    name = f"[{product.default_code}] {product.name}"
                else:
                    name = f"{product.name or ''}"
                if product.description_purchase:
                    name += f"\n{product.description_purchase}"
                line.name = name

    @api.depends('product_qty', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            if line.product_qty < 0:
                line.product_qty = abs(line.product_qty)
            if line.price_unit < 0:
                line.price_unit = abs(line.price_unit)
        super()._compute_amount()

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLineInherit, self)._prepare_account_move_line(move)
        hsn = self.product_id.product_tmpl_id.purchase_hsn
        res.update({'hsn_id': hsn.id})
        return res

    def fetch_size(self):
        lst = []
        for rec in self:
            if rec.product_id.product_template_attribute_value_ids:
                i = 0
                for size in rec.product_id.product_template_attribute_value_ids:
                    if i % 2 != 0:
                        lst.append(size.name)
                    i += 1
        if len(lst) > 0:
            return lst[0]

    def fetch_color(self):
        lst = []
        for rec in self:
            if rec.product_id.product_template_attribute_value_ids:
                i = 0
                for color in rec.product_id.product_template_attribute_value_ids:
                    if i % 2 == 0:
                        lst.append(color.name)
                    i += 1
        if len(lst) > 0:
            return lst[0]

    @api.depends('tax_ids')
    def check_tax_amount(self):
        for rec in self:
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    rec.tax_amount_line += (rec.price_unit * tax.amount) / 100
            else:
                rec.tax_amount_line = 0
