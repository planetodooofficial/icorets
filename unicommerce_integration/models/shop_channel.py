from odoo import api, fields, models, _


class ShopSalesChannel(models.Model):
    _name = "shop.sales.channel"
    _description = "Sales Channel"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", tracking=True, help="Name of the sales channel", required=True)
    shop_instance_id = fields.Many2one(comodel_name="shop.instance", tracking=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id,
                                 tracking=True)
    sale_journal_id = fields.Many2one("account.journal", string="Sales Journal", tracking=True)
    analytics_id = fields.Many2one("account.analytic.account", string="Analytic Account", tracking=True,
                                   help="Analytic account to be used for sales")
    prepaid_holding_journal_id = fields.Many2one("account.journal", string="Prepaid Holding Journal", tracking=True,
                                                 help="Journal to hold the prepaid amount")
    cod_holding_journal_id = fields.Many2one("account.journal", string="COD Holding Journal", tracking=True,
                                             help="Journal to hold the COD amount")
    is_no_invoice = fields.Boolean(string="No Invoice", tracking=True, help="If checked, no invoice will be created")
