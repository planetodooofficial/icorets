from odoo import models, api, fields, _


class InheritContracts(models.Model):
    _inherit = 'res.partner'

    is_approved = fields.Boolean('Approved', default=False, tracking=True)
    cancelled_cheque = fields.Binary('Cancelled Cheque', copy=False)
    pan_no = fields.Char('PAN NO')
    pan_card = fields.Binary('PAN Card', copy=False)
    gst_doc = fields.Binary('GST', copy=False)
    iec_number = fields.Char('IEC Number')
    cin = fields.Char('CIN')
    gst_doc_name = fields.Char('GST Doc Name')
    pan_file_name = fields.Char('PAN File Name')
    check_file_name = fields.Char('Cheque File Name')
    entity_type = fields.Selection([
        ('Sole Proprietorships', 'Sole Proprietorships'),
        ('Partnership', 'Partnership'),
        ('LLP', 'LLP'),
        ('PVT LTD', 'PVT LTD'),
        ('Public LTD', 'Public LTD'),
    ], string='Entity Type')
    is_msme = fields.Selection([('yes', 'YES'), ('no', 'NO')], default='no', string='MSME Registered')
    msme_doc = fields.Binary('MSME Certificate', copy=False)
    msme_doc_name = fields.Char('MSME Certificate Name')

    @api.model
    def _get_default_country(self):
        return self.env['res.country'].search([('code', '=', 'IN')], limit=1)

    country_id = fields.Many2one('res.country', string='Country', default=_get_default_country)

    @api.model
    def _get_frontend_writable_fields(self):
        frontend_writable_fields = super()._get_frontend_writable_fields()
        frontend_writable_fields |= {
            'entity_type', 'is_msme', 'pan_no', 'iec_number', 'cin',
            'l10n_in_gst_treatment', 'check_file_name', 'pan_file_name',
            'gst_doc_name', 'msme_doc_name',
        }
        return frontend_writable_fields

    @property
    def download_pan(self):
        self.ensure_one()
        filename = self.pan_file_name or 'pan_card'
        return f"/web/content/?model=res.partner&id={self.id}&filename_field=pan_file_name&field=pan_card&download=true&filename={filename}"

    @property
    def download_cheque(self):
        self.ensure_one()
        filename = self.check_file_name or 'cancelled_cheque'
        return f"/web/content/?model=res.partner&id={self.id}&filename_field=check_file_name&field=cancelled_cheque&download=true&filename={filename}"

    @property
    def download_gst(self):
        self.ensure_one()
        filename = self.gst_doc_name or 'gst_doc'
        return f"/web/content/?model=res.partner&id={self.id}&filename_field=gst_doc_name&field=gst_doc&download=true&filename={filename}"

    @property
    def download_msme(self):
        self.ensure_one()
        filename = self.msme_doc_name or 'msme_doc'
        return f"/web/content/?model=res.partner&id={self.id}&filename_field=msme_doc_name&field=msme_doc&download=true&filename={filename}"