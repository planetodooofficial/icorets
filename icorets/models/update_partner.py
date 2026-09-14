from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class JournalPartnerUpdateWizard(models.TransientModel):
    _name = 'journal.partner.update.wizard'
    _description = 'Wizard to update partner ID for the active invoice'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    active_invoice_name = fields.Char(string='Active Invoice', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(JournalPartnerUpdateWizard, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            active_invoice = self.env['account.move'].browse(active_ids[0])
            res['active_invoice_name'] = active_invoice.name
        return res

    def action_update_partner(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise ValidationError(_("No active invoice found."))

        for active_id in active_ids:
            journal_entry = self.env['account.move'].browse(active_id)
            if journal_entry:
                journal_entry.partner_id = self.partner_id.id
                for line in journal_entry.line_ids:
                    line.partner_id = self.partner_id.id

        return {'type': 'ir.actions.act_window_close'}
