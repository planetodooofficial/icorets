from odoo import api, fields, models


class StockVariantReport(models.TransientModel):
    _name = "stock.variant.report"
    _description = "Stock Variant Report"

    # type = fields.Char("Type")
    # year = fields.Char("Year")

    product_category = fields.Many2many('product.category', string='Product Category')



    def action_stock_variant_excel_report(self):
        return self.env.ref('icorets.stock_variant_report_action_excel').report_action(self)