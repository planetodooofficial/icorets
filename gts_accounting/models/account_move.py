from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    pod_document_id = fields.Binary(string="POD Document", attachment=False)
    pod_document_name = fields.Char(string="POD Document Name")
    customer_appointment_date = fields.Date(string="Customer Appointment Date")
    transporter_name = fields.Char(string="Transporter Name")
    lr_number = fields.Char(string="LR Number")
    customer_delivery_number = fields.Char(string="Customer Delivery Number")

    quick_commerce = fields.Char(string="Quick Commerce")
    po_expiry_date = fields.Date(string="PO Expiry Date")
    eta = fields.Char(string="ETA")
    timing = fields.Char(string="Timing")
    appointment = fields.Char(string="Appointment")
    cn_number = fields.Char(string="CN Number")
    dn_number = fields.Char(string="DN Number")
    old_po = fields.Char(string="Old Po")
    reason = fields.Char(string="Reason")
    remarks = fields.Char(string="Remarks")
    asn_no = fields.Char(string="ASN No")
    vin_po_no = fields.Char(string="VIN Po No")
    vin_asn_no = fields.Char(string="VIN ASN No")
    shortage = fields.Char(string="Shortage")

    credit_invoice_ids = fields.Many2many('account.move', 'credit_invoices_rel', 'credit_id', 'invoice_id',
                                          string='Select Invoice')

    @api.onchange('credit_invoice_ids')
    def onchange_credit_invoice_ids(self):
        self.with_context(check_move_validity=False)
        self.invoice_line_ids = [(5, 0, 0)]

        line_vals = []
        for credit_invoice in self.credit_invoice_ids:
            for line in credit_invoice.invoice_line_ids:
                vals = {
                    'sequence': line.sequence,
                    'display_type': line.display_type or 'product',
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'account_id': line.account_id.id,
                    'tax_ids': [Command.set(line.tax_ids.ids)],
                }
                line_vals.append(Command.create(vals))

        print('\n\nline_vals+++++++++++++', line_vals)
        self.invoice_line_ids = line_vals

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if res.credit_invoice_ids:
            for line in res.line_ids:
                if line.display_type == 'product' and line.credit == 0 and line.debit == 0:
                    line.unlink()
            for invoice in res.credit_invoice_ids:
                invoice.update({
                    'reversal_move_id': [(4, res.id)]
                })
        return res

    def write(self, vals):
        res = super().write(vals)

        if self.credit_invoice_ids:
            for line in self.line_ids:
                if line.display_type == 'product' and line.credit == 0 and line.debit == 0:
                    line.unlink()

            for invoice in self.credit_invoice_ids:
                invoice.update({
                    'reversal_move_id': [(4, self.id)]
                })

        return res
