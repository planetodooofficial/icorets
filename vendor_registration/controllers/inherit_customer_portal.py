import base64
import json
from werkzeug.exceptions import Forbidden

from odoo import _
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal

GST_TREATMENT_MAPPING = {
    'Registered Business - Regular': 'regular',
    'Registered Business - Composition': 'composition',
    'Unregistered Business': 'unregistered',
    'Consumer': 'consumer',
    'Overseas': 'overseas',
    'Special Economic Zone': 'special_economic_zone',
    'Deemed Export': 'deemed_export',
    'UIN Holders': 'uin_holders',
}


class CustomerPortalInherit(CustomerPortal):

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, **kwargs):
        if request.httprequest.method == 'POST':
            partner_sudo = request.env.user.partner_id
            self._create_or_update_address(partner_sudo, **kwargs)
            return request.redirect('/my/account')
        return super().account(**kwargs)

    def _prepare_address_form_values(
        self, partner_sudo, address_type='billing', use_delivery_as_billing=False, callback='', **kwargs
    ):
        values = super()._prepare_address_form_values(
            partner_sudo,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback,
            **kwargs,
        )
        values['vat_label'] = _("GST Number")
        return values

    def _create_or_update_address(
        self,
        partner_sudo,
        address_type='billing',
        use_delivery_as_billing=False,
        callback='/my/addresses',
        required_fields=False,
        verify_address_values=True,
        **form_data
    ):
        # Extract and prepare file attachments
        files_to_save = {}
        for field_name, name_field in [
            ('pan_card', 'pan_file_name'),
            ('cancelled_cheque', 'check_file_name'),
            ('gst_doc', 'gst_doc_name'),
            ('msme_doc', 'msme_doc_name'),
        ]:
            file = request.httprequest.files.get(field_name) or form_data.pop(field_name, None)
            if file and hasattr(file, 'read') and getattr(file, 'filename', None):
                content = file.read()
                if content:
                    files_to_save[field_name] = base64.b64encode(content)
                    files_to_save[name_field] = file.filename

        # Extract bank fields before base processing
        bank_name = form_data.pop('bank_id', None)
        acc_number = form_data.pop('acc_number', None)
        usd_account_name = form_data.pop('usd_account_name', None)
        ifsc_number = form_data.pop('ifsc_number', None)
        swift_code = form_data.pop('swift_code', None)
        currency_name = form_data.pop('currency_id', None)

        # Map display name of GST treatment to selection key if necessary
        gst_treatment_val = form_data.get('l10n_in_gst_treatment')
        if gst_treatment_val in GST_TREATMENT_MAPPING:
            form_data['l10n_in_gst_treatment'] = GST_TREATMENT_MAPPING[gst_treatment_val]

        partner_sudo, feedback_dict = super()._create_or_update_address(
            partner_sudo,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback,
            required_fields=required_fields,
            verify_address_values=verify_address_values,
            **form_data,
        )

        # If validation failed, return without saving custom fields
        if feedback_dict.get('invalid_fields'):
            return partner_sudo, feedback_dict

        # Save files on partner
        if files_to_save and partner_sudo:
            partner_sudo.sudo().write(files_to_save)

        # Handle bank and partner bank creation/update
        if partner_sudo and (bank_name or acc_number or ifsc_number or swift_code):
            domain = []
            if bank_name:
                domain.append(('name', '=', bank_name))
            if ifsc_number:
                domain.append(('bic', '=', ifsc_number))

            bank = request.env['res.bank'].sudo().search(domain, limit=1) if domain else False
            bank_vals = {}
            if swift_code:
                bank_vals['swift_code'] = swift_code
            if usd_account_name:
                bank_vals['usd_account_name'] = usd_account_name

            if not bank and bank_name:
                create_vals = {
                    'name': bank_name,
                    'bic': ifsc_number or False,
                    'swift_code': swift_code or False,
                    'usd_account_name': usd_account_name or False,
                }
                bank = request.env['res.bank'].sudo().create(create_vals)
            elif bank and bank_vals:
                bank.sudo().write(bank_vals)

            if bank and acc_number:
                partner_bank = partner_sudo.bank_ids.filtered(lambda b: b.bank_id == bank)
                if partner_bank:
                    partner_bank[0].sudo().write({'acc_number': acc_number})
                elif partner_sudo.bank_ids:
                    partner_sudo.bank_ids[0].sudo().write({
                        'bank_id': bank.id,
                        'acc_number': acc_number,
                    })
                else:
                    request.env['res.partner.bank'].sudo().create({
                        'partner_id': partner_sudo.id,
                        'bank_id': bank.id,
                        'acc_number': acc_number,
                    })

        return partner_sudo, feedback_dict
