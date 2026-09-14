# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EInvoiceService(models.Model):
    _name = "po.einvoice.service"
    _description = "eInvoice Service"

    partner_id = fields.Many2one("res.partner", string="GSTN Partner")
    gstin = fields.Char(string="GSTIN")
    gstn_username = fields.Char(string="Username")
    gstn_password = fields.Char(string="Password")
    token = fields.Char(string="Token")
    token_validity = fields.Datetime(string="Valid Until")
    is_token_valid = fields.Boolean(compute="_compute_is_token_valid", string="Valid Token")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.gstin = self.partner_id.vat

    @api.depends('token_validity')
    def _compute_is_token_valid(self):
        now = fields.Datetime.now()
        for service in self:
            service.is_token_valid = bool(service.token_validity and service.token_validity > now)
