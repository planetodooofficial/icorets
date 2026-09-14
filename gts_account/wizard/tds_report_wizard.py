from odoo import api, fields, models, _


class WizardActionButton(models.TransientModel):
    _name = "wizard.action.button"
    _description = "TDS Report Wizard"

    from_date = fields.Date(string="From Date")
    end_date = fields.Date(string="End Date")

    def download_report(self):
        self.ensure_one()
        return self.env.ref('gts_account.wizard_button_report_xlsx').report_action(self)
