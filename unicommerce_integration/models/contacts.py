from odoo import api, fields, models, _


class InheritPartner(models.Model):
    _inherit = 'res.partner'

    is_website_partner = fields.Boolean(string='Website Partner ?',
                                        help="Check this box if the partner is a playr website partner")
