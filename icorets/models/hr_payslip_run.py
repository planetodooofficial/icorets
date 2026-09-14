from odoo import models, api
from odoo.addons.hr_payroll.models.hr_payslip_run import STATUS_COLOR


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.depends('state')
    def _compute_color(self):
        for payslip_run in self:
            payslip_run.color = STATUS_COLOR.get(payslip_run.state, 0)
