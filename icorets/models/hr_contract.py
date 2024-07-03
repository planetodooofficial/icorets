from odoo import api, fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    total_wage_in_days = fields.Integer(string='Total Wage in Days')
    total_leave = fields.Integer(string='Total Leave')
    present_days = fields.Integer(string='Present Days', compute='_compute_present_days')
    expense = fields.Float(string='Expense')
    total_earned_ctc = fields.Float(string='Total Earned CTC', compute='_compute_total_earned_ctc')
    extra_present_days = fields.Integer("Extra Present Days")
    advance_payment = fields.Float("Advance Payment")

    @api.depends('total_wage_in_days', 'total_leave')
    def _compute_present_days(self):
        for record in self:
            record.present_days = record.total_wage_in_days - record.total_leave + record.extra_present_days + record.x_studio_total_paid_leave

    # def action_calculate_present_days(self):
    #     self._compute_present_days()

    @api.depends('present_days', 'total_wage_in_days', 'wage')
    def _compute_total_earned_ctc(self):
        for rec in self:
            if rec.total_wage_in_days != 0:  # Avoid division by zero
                rec.total_earned_ctc = (rec.wage / rec.total_wage_in_days) * rec.present_days
            else:
                rec.total_earned_ctc = 0
