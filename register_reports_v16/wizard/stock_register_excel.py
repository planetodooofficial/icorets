from odoo import api, fields, models
from odoo.tools.safe_eval import datetime


class StockRegisterPoReport(models.TransientModel):
    _name = "stock.register.po.report"
    _description = "Stock Register Po Report"

    # type = fields.Char("Type")
    # year = fields.Char("Year")
    from_date = fields.Date("From Date", default='2024-10-01')
    to_date = fields.Date("To Date", default='2024-10-21')
    product_category = fields.Many2many('product.category', string='Product Category')



    def action_stock_register_excel_report(self):
        return self.env.ref('gts_register_reports_v16.stock_register_po_report_action_excel').report_action(self)

    # def action_location_wise_excel_report(self):
    #     return self.env.ref('gts_register_reports_v16.stock_location_wise_report_action_excel').report_action(self)