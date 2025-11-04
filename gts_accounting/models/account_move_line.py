from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    without_sale_cogs = fields.Boolean(string="Without Sale Cogs", default=False, related="move_id.without_sale_cogs", store=True)

