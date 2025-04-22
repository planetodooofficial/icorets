from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MailWizard(models.TransientModel):
    _name = 'mail.wizard'
    _description = 'Mail Wizard'

    to_partner_id = fields.Many2one(
        'res.partner',
        string='To',
        required=True
    )
    cc_partner_ids = fields.Many2many(
        'res.partner',
        relation='mail_wizard_cc_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string='CC'
    )
    subject = fields.Char(string='Subject', required=True)
    body = fields.Html(string='Body')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.onchange('to_partner_id')
    def _onchange_to_partner_id(self):
        if self.to_partner_id:
            self.body = f"""
                <p>Dear,<br/>
                <strong>{self.to_partner_id.name}</strong><br/>
                GST Number: <em>{self.to_partner_id.vat or 'N/A'}</em><br/><br/>

                Please find attached the ledger as on date and reconcile the same with a confirmation return email.<br/><br/>

                <br/>
                </p>
            """

    def action_send_mail(self):
        for wizard in self:
            if not wizard.to_partner_id.email:
                raise UserError("The selected partner doesn't have an email address.")

            cc_partners = wizard.cc_partner_ids.filtered('email')

            mail_vals = {
                'subject': wizard.subject,
                'body_html': wizard.body,
                'email_from': self.env.user.email or 'admin@example.com',
                'recipient_ids': [(4, wizard.to_partner_id.id)],
                'email_cc': ','.join(cc_partners.mapped('email')),
                'attachment_ids': [(6, 0, wizard.attachment_ids.ids)],
            }

            mail = self.env['mail.mail'].create(mail_vals)
            mail.send()

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_tds = fields.Boolean(string="Is TDS Account?")
    is_vat = fields.Boolean(string="Is VAT Account?")
