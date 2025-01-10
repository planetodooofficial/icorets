from odoo import api, fields, models
from odoo.tools.safe_eval import datetime


class StockRegisterPoReport(models.TransientModel):
    _inherit = "stock.register.po.report"

    def action_location_wise_excel_report(self):
        #Generate Location Stock Report
        return self.env.ref('gts_icore_reports.stock_location_wise_report_action_excel').report_action(self)
