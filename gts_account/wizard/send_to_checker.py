from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SendChecker(models.TransientModel):
    _name = "send.checker"
    _description = "Send to Checker"

    checker_id = fields.Many2one('res.users', string="Checker User", required=True)

    def send_for_checking(self):
        self.ensure_one()
        res_model = self.env.context.get('active_model')
        res_id = self.env.context.get('active_id')
        if not res_model or not res_id:
            return

        record = self.env[res_model].sudo().browse(res_id)
        if record.exists():
            record.to_check = True
            record.checker_id = self.checker_id.id

            model_record = self.env['ir.model'].sudo().search([('model', '=', res_model)], limit=1)
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)

            if model_record and activity_type:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': model_record.id,
                    'res_id': res_id,
                    'user_id': self.checker_id.id,
                    'activity_type_id': activity_type.id,
                    'summary': f"Request to check {record.name or ''}",
                    'note': f"Request to check {record.name or ''}",
                })
