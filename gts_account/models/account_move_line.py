from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    without_sale_cogs = fields.Boolean(
        string="Without Sale Cogs",
        default=False,
        related="move_id.without_sale_cogs",
        store=True
    )
    is_os_line = fields.Boolean(string="Is OS Line")
    hsn_id = fields.Many2one(
        'hsn.code',
        string='HSN / SAC Code',
        domain="[('company_id', '=', company_id)]"
    )
    custom_label = fields.Char(string='Custom Label')
    partial_reconcile_ids = fields.One2many('partial.line', 'payment_line', string="Partial Reconcile Lines")

    @api.onchange('hsn_id')
    def _onchange_hsn_id(self):
        if self.hsn_id and self.hsn_id.taxes_id:
            self.tax_ids = [(6, 0, [self.hsn_id.taxes_id.id])]

    def _get_computed_taxes(self):
        res = super()._get_computed_taxes()
        if self.move_id.move_type == 'in_invoice' and self.move_id.taxes_id:
            return res + self.move_id.taxes_id
        return res

    def action_reconcile_wiz(self):
        self.ensure_one()
        payment_type = 'inbound'
        if self.move_id.move_type == 'entry':
            if self.move_id.custom_payment_type == 'inbound':
                payment_type = 'inbound'
            elif self.move_id.custom_payment_type == 'outbound':
                payment_type = 'outbound'
        elif self.move_id.move_type == 'out_invoice':
            payment_type = 'inbound'
        elif self.move_id.move_type == 'in_invoice':
            payment_type = 'outbound'

        return {
            'name': _("Reconcile"),
            'type': 'ir.actions.act_window',
            'res_model': 'partial.line',
            'view_mode': "list",
            'view_id': self.env.ref('gts_account.partial_reconcile_tree_view_wizard').id,
            'context': {
                'default_custom_payment_type': payment_type,
                'default_partner_id': self.partner_id.id,
                'default_payment_line': self.id,
                'default_entry_id': self.move_id.id
            },
            'target': 'new',
            'domain': [('id', 'in', self.partial_reconcile_ids.ids)],
        }
