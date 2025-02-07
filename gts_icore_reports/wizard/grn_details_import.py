from csv import DictReader
from odoo import models, fields, api, _
from io import BytesIO
import base64
from datetime import datetime, date
import pandas as pd


class GrnDetails(models.TransientModel):
    _name = "grn.details"

    file = fields.Binary("File")
    file_name = fields.Char("File Name")

    def _get_user_by_name(self, name):
        user = self.env['res.users'].search([('name', 'ilike', name)], limit=1)
        return user.id

    def _get_partner_by_name(self, name):
        partner = self.env['res.partner'].search([('name', 'ilike', name)], limit=1)
        return partner.id

    def _get_product_by_name(self, name):
        product = self.env['product.product'].search([('default_code', 'ilike', name)], limit=1)
        return product

    def action_upload(self):
        self.ensure_one()
        # Decode the uploaded file
        excel_data = base64.b64decode(self.file)

        # Load file into pandas from memory
        excel_file = BytesIO(excel_data)

        # Use pandas to read the Excel file
        sheets = pd.ExcelFile(excel_file)
        tree_view_id = self.env.ref('gts_icore_reports.view_grn_details_data_invoice_tree').id
        # Check all available sheets
        print("Available sheets:", sheets.sheet_names)
        grn_details = self.env['grn.details.data']
        # Read the second sheet (index 1 as sheets are zero-indexed)
        if len(sheets.sheet_names) > 1:
            df = sheets.parse(sheets.sheet_names[1])
            records_list = []
            for index, row in df.iterrows():
                if row[0] == 'Invoice NO':
                    continue
                product = self._get_product_by_name(row[14])

                if isinstance(row[27], datetime):
                    delivery_date = row[27]
                    delivery_date = delivery_date.date()
                elif isinstance(row[27], date):
                    delivery_date = row[27]
                else:
                    delivery_date = None

                if row[28] == 'POD Not Received':
                    pod_status = 'pending'
                elif row[28] == 'POD Received':
                    pod_status = 'completed'
                else:
                    pod_status = ''

                if isinstance(row[40], date):
                    row_40 = row[40]
                else:
                    row_40 = None
                if isinstance(row[48], date):
                    row_48 = row[48]
                else:
                    row_48 = None

                # print('row[40]+++++++++++++++++++', row[40], type(row[40]))
                # print('row[48]+++++++++++++++++++', row[48], type(row[48]))

                vals = {
                    'invoice_no': row[0],
                    'invoice_date': row[1] if str(row[1]) != 'nan' else None,
                    'salesperson': self._get_user_by_name(row[2]),  # Fetch Many2one user by name
                    'customer': self._get_partner_by_name(row[3]),  # Fetch Many2one partner by name
                    'city': row[4] if str(row[4]) != 'nan' else '',
                    'state': row[5] if str(row[5]) != 'nan' else '',
                    'pin': row[6] if str(row[6]) != 'nan' else '',
                    'gst_no': row[7] if str(row[7]) != 'nan' else '',
                    'analytic': row[8] if str(row[8]) != 'nan' else '',
                    'product': product.id,  # Fetch Many2one product by name
                    'mrp': row[10] if str(row[10]) != 'nan' else '',
                    'article_code': row[11] if str(row[11]) != 'nan' else '',
                    'so_number': row[12] if str(row[12]) != 'nan' else '',
                    'po_number': row[13] if str(row[13]) != 'nan' else '',
                    'sku': row[14] if str(row[14]) != 'nan' else '',
                    'ean': row[15] if str(row[15]) != 'nan' else '',
                    'brand': row[16] if str(row[16]) != 'nan' else '',
                    'uom': product.uom_id.id,  # Fetch Many2one UOM by name
                    'size': row[18] if str(row[18]) != 'nan' else '',
                    'color': row[19] if str(row[19]) != 'nan' else '',
                    'invoice_class': row[20] if str(row[20]) != 'nan' else '',
                    'subclass': row[21] if str(row[21]) != 'nan' else '',
                    'quantity': row[22] if not isinstance(row[22], str) else 0,

                    'grn_quantity': row[23] if not isinstance(row[23], str) else 0,
                    'shortage': row[24] if not isinstance(row[24], str) else 0,
                    'transporter': row[25],
                    'delivery_status': row[26],
                    # 'delivery_date': row[27],
                    'delivery_date': delivery_date,
                    'pod_status': pod_status,
                    'remark': row[29],

                    'unit_price': row[30],
                    'discount': float(row[31]),
                    'price_subtotal': float(row[32]),
                    'taxes': row[33],
                    'bill_net_amt': float(row[34]) if str(row[34]) != 'nan' else 0,
                    'price_total': float(row[35]) if str(row[35]) != 'nan' else 0,
                    'invoice_untaxed_amt': float(row[36]) if str(row[36]) != 'nan' else 0,
                    'invoice_tax_amount': float(row[37]) if str(row[37]) != 'nan' else 0,
                    'invoice_total_amt': float(row[38]) if str(row[38]) != 'nan' else 0,

                    'payment_ref': row[39] if str(row[39]) != 'nan' else '',

                    'customer_appointment_date': row_40,
                    'transporter_name': row[41] if str(row[41]) != 'nan' else False,
                    'lr_number': row[42] if str(row[42]) != 'nan' else False,
                    'customer_delivery_number': row[43] if str(row[43]) != 'nan' else False,

                    'quick_commerce': row[44] if str(row[44]) != 'nan' else False,
                    'no_of_box': row[45] if str(row[45]) != 'nan' else False,
                    'ship_from': row[46] if str(row[46]) != 'nan' else False,
                    'ship_to': row[47] if str(row[47]) != 'nan' else False,
                    'po_expiry_date': row_48,
                    'eta': row[49] if str(row[49]) != 'nan' else False,
                    'timing': row[50] if str(row[50]) != 'nan' else False,
                    'appointment': row[51] if str(row[51]) != 'nan' else False,
                    'cn_number': row[52] if str(row[52]) != 'nan' else False,
                    'dn_number': row[53] if str(row[53]) != 'nan' else False,
                    'old_po': row[54] if str(row[54]) != 'nan' else False,
                    'reason': row[55] if str(row[55]) != 'nan' else False,
                    'asn_no': row[56] if str(row[56]) != 'nan' else False,
                    'vin_po_no': row[57] if str(row[57]) != 'nan' else False,
                    'vin_asn_no': row[58] if str(row[58]) != 'nan' else False,

                    'total_sgst': (row[59]) if str(row[59]) != 'nan' else 0,
                    'total_cgst': (row[60]) if str(row[60]) != 'nan' else 0,
                    'sgst_sale_2_5_mh': (row[61]) if str(row[61]) != 'nan' else 0,
                    'cgst_sale_2_5_mh': (row[62]) if str(row[62]) != 'nan' else 0,
                    'total_igst': (row[63]) if str(row[63]) != 'nan' else 0,
                    'igst_12_output_mh': (row[64]) if str(row[64]) != 'nan' else 0,
                    'igst_5_output_mh': (row[65]) if str(row[65]) != 'nan' else 0,
                    'sgst_sale_6_mh': (row[66]) if str(row[66]) != 'nan' else 0,
                    'cgst_sale_6_mh': (row[67]) if str(row[67]) != 'nan' else 0,
                    'sgst_sale_9_mh': (row[68]) if str(row[68]) != 'nan' else 0,
                    'cgst_sale_9_mh': (row[69]) if str(row[69]) != 'nan' else 0,
                    'igst_18_output_mh': (row[70]) if str(row[70]) != 'nan' else 0,
                    'igst_5_output_dl': (row[71]) if str(row[71]) != 'nan' else 0,
                    'sgst_sale_9': (row[72]) if str(row[72]) != 'nan' else 0,
                }

                if len(row) > 73 and row[73] and str(row[73]) != 'nan':
                    vals.update({'cgst_sale_9': (row[73]) if row[73] and str(row[73]) != 'nan' else 0,})
                else:
                    vals.update({'cgst_sale_9': 0})

                if len(row) > 74 and row[74] and str(row[74]) != 'nan':
                    vals.update({'igst_18': (row[74]) if str(row[74]) != 'nan' else 0, })
                else:
                    vals.update({'igst_18': 0})

                if len(row) > 75 and row[75] and str(row[75]) != 'nan':
                    vals.update({'igst_0_output_mh': (row[75]) if str(row[75]) != 'nan' else 0, })
                else:
                    vals.update({'igst_0_output_mh': 0})


                print("----vals", vals)
                records = grn_details.search(
                    [('invoice_no', '=', vals.get('invoice_no')), ('sku', '=', vals.get('sku'))])
                if records:
                    records.write(vals)
                else:
                    grn_record = grn_details.create(vals)
                    records_list.append(grn_record.id)
                # for column_name, value in row.items():
                #     print(f"column_values-----{column_name}: {value}")
                #     vals = {
                #
                #     }
                # Example: Access specific cell values
                # Value in first row, second column (assuming zero-based index)
            specific_value = df.iloc[0, 1]
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree')],
                'view_mode': 'tree,form,pivot',
                'name': _('GRN Details Report'),
                'res_model': 'grn.details.data',
                'domain': [('id', 'in', records_list)],
                'context': {'create': False, 'edit': False},
            }
            # print("--------start date", start_date, 'end date', end_date, 'st_start_date', st_start_date, 'st_end_date',st_end_date)
            # tt
            return action
