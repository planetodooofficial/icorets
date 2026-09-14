# -*- coding: utf-8 -*-
from odoo import fields, models


class ConfigEinvLogins(models.TransientModel):
    _name = 'config.einv.logins'
    _description = 'Configure E-Invoice Logins'

    partner_id = fields.Many2one('res.partner', string='GSTN Partner')
    gstn_username = fields.Char(string='Username')
    gstn_password = fields.Char(string='Password')
    save_password = fields.Boolean(string='Save Password')
    hide_cred = fields.Boolean(string='Hide Cred')
    hide_cred_group = fields.Boolean(string='Hide Cred Group')
