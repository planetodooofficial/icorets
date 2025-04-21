from odoo import models, fields, api, _

class MailWizard(models.TransientModel):
    _name = 'mail.wizard'
    _description = 'Mail Wizard'

    to_partner_ids = fields.Many2many(
        'res.partner',
        relation='mail_wizard_to_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string='To'
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

    def action_send_mail(self):
        for wizard in self:
            # Filter partners with email
            to_partners = wizard.to_partner_ids.filtered('email')
            cc_partners = wizard.cc_partner_ids.filtered('email')

            # Prepare the mail values
            mail_vals = {
                'subject': wizard.subject,
                'body_html': wizard.body,
                'email_from': self.env.user.email or 'admin@example.com',
                'recipient_ids': [(4, partner.id) for partner in to_partners],
                'email_cc': ','.join(cc_partners.mapped('email')),
                'attachment_ids': [(6, 0, wizard.attachment_ids.ids)],

            }

            mail = self.env['mail.mail'].create(mail_vals)
            mail.send()

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_tds = fields.Boolean(string="Is TDS Account?")
    is_vat = fields.Boolean(string="Is VAT Account?")
