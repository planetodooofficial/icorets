from odoo import api, fields, models


class StockRegisterPoReport(models.TransientModel):
    _name = "stock.register.po.report"
    _description = "Stock Register PO Report"

    from_date = fields.Date("From Date", default=lambda self: fields.Date.today().replace(day=1))
    to_date = fields.Date("To Date", default=fields.Date.today)
    product_category = fields.Many2many('product.category', string='Product Category')

    def action_stock_register_excel_report(self):
        return self.env.ref('gts_icore_reports.stock_register_po_report_action_excel').report_action(self)

    def action_location_wise_excel_report(self):
        return self.env.ref('gts_icore_reports.stock_location_wise_report_action_excel').report_action(self)
