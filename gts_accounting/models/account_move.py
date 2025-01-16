from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    pod_document_id = fields.Binary(string="POD Document", attachment=False)
    pod_document_name = fields.Char(string="POD Document Name")
    customer_appointment_date = fields.Date(string="Customer Appointment Date")
    transporter_name = fields.Char(string="Transporter Name")
    lr_number = fields.Char(string="LR Number")
    customer_delivery_number = fields.Char(string="Customer Delivery Number")
