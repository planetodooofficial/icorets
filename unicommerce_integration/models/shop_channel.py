from odoo import api, fields, models, _


class ShopSalesChannel(models.Model):
    _name = "shop.sales.channel"
    _description = "Sales Channel"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", tracking=True)
    shop_instance_id = fields.Many2one(comodel_name="shop.instance", tracking=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id,
                                 tracking=True)
    sale_journal_id = fields.Many2one("account.journal", string="Sales Journal", tracking=True)
    analytics_id = fields.Many2one("account.analytic.account", string="Analytic Account", tracking=True)
    prepaid_holding_journal_id = fields.Many2one("account.journal", string="Prepaid Holding Journal", tracking=True)
    cod_holding_journal_id = fields.Many2one("account.journal", string="COD Holding Journal", tracking=True)

