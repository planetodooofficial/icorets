import time
from odoo import api, models, _, fields
from odoo.exceptions import UserError


class ResPartnerCustom(models.Model):
    _name = 'res.partner.custom'

    custom_parent_id = fields.Many2one('res.partner', string='Custom Parent Id')
    custom_partner_id = fields.Many2one('res.partner', string='Custom Partner Id')

    @api.model
    def create(self, vals):
        existing_in_parent = self.search([('custom_partner_id', '=', vals.get('custom_partner_id'))])
        if existing_in_parent:
            raise UserError('Partner Already Exist in Some Another Partner')
        return super().create(vals)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    custom_child_ids = fields.One2many('res.partner.custom', 'custom_parent_id', string='Custom Child Ids')

    def check_parent(self):
        if self.custom_child_ids:
            return True
        else:
            return False
