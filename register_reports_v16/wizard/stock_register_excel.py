from odoo import api, fields, models


class StockRegisterPoReport(models.TransientModel):
    _name = "stock.register.po.report"
    _description = "Stock Register Po Report"

    # type = fields.Char("Type")
    # year = fields.Char("Year")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")

    def action_stock_register_excel_report(self):
        return self.env.ref('register_reports_v16.stock_register_po_report_action_excel').report_action(self)