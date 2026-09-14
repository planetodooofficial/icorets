from odoo import models, fields, api, _
import base64

class UploadDocument(models.TransientModel):
    _name = 'upload.document'

    binary_file = fields.Binary('Upload Document', attachment=False)
    file_name = fields.Char('Upload Document')

    def update_pod_document(self):
        active_id = self.env.context.get('active_id')
        inv = self.env['account.move'].browse(active_id)
        # Unlink previous document if it exists
        if inv.pod_document_id:
            inv.pod_document_name = False  # Delete the previous document if any
            inv.pod_document_id = False  # Delete the previous document if any
        inv.write({'pod_document_id': self.binary_file,
                   'pod_document_name': self.file_name
                   })
