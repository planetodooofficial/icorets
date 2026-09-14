from odoo import models, fields, api, _


class InheritResPartner(models.Model):
    _inherit = "res.partner"

    cust_alias_name = fields.Char("Alias Name", copy=False)
    pan_number = fields.Char("PAN Number", compute="_compute_pan_number", inverse="_inverse_pan_number", store=True)

    @api.depends('vat', 'l10n_in_pan_entity_id')
    def _compute_pan_number(self):
        for partner in self:
            if hasattr(partner, 'l10n_in_pan_entity_id') and partner.l10n_in_pan_entity_id:
                partner.pan_number = partner.l10n_in_pan_entity_id.name
            elif partner.vat and len(partner.vat) >= 12:
                partner.pan_number = partner.vat[2:12]
            elif not partner.pan_number:
                partner.pan_number = False

    def _inverse_pan_number(self):
        for partner in self:
            pass

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = list(domain or [])
        if name:
            domain += ['|', ('name', operator, name), ('cust_alias_name', operator, name)]
        return super()._name_search(name, domain, operator, limit, order)

    @api.depends('cust_alias_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'show_email', 'show_vat', 'lang', 'formatted_display_name')
    def _compute_display_name(self):
        super()._compute_display_name()
        for record in self:
            if record.cust_alias_name and record.display_name:
                record.display_name = "[%s] %s" % (record.cust_alias_name, record.display_name)


class InheritResCompany(models.Model):
    _inherit = "res.company"

    pan_number = fields.Char(related="partner_id.pan_number", string="PAN Number", readonly=False)
