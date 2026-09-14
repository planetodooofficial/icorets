# -*- coding: utf-8 -*-
from odoo import fields, models


class EInvoiceTransaction(models.Model):
    _name = "po.einvoice.transact"
    _description = "eInvoice Transaction"

    name = fields.Char(string="IRN Number")
    ack_no = fields.Char(string="Ack No.")
    ack_date = fields.Date(string="Acknowledgement Date")
    qr_code = fields.Char(string="QR Code Data")
    move_id = fields.Many2one('account.move', string="Journal Entry")
    response = fields.Text(string="Response")
