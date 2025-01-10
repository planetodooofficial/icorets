from csv import DictReader
from odoo import models, fields, api, _
from io import BytesIO
import base64
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
                    'sku': row[14]  if str(row[14]) != 'nan' else '',
                    'ean': row[15]  if str(row[15]) != 'nan' else '',
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
                    'pod_status': '',  # Fetch Selection value
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
                    'total_sgst': float(row[39]) if str(row[39]) != 'nan' else 0,
                    'total_cgst': float(row[40]) if str(row[40]) != 'nan' else 0,
                    'sgst_sale_2_5_mh': float(row[41]) if str(row[41]) != 'nan' else 0,
                    'cgst_sale_2_5_mh': float(row[42]) if str(row[42]) != 'nan' else 0,
                    'total_igst': float(row[43]) if str(row[43]) != 'nan' else 0,
                    'igst_12_output_mh': float(row[44]) if str(row[44]) != 'nan' else 0,
                    'igst_5_output_mh': float(row[45]) if str(row[45]) != 'nan' else 0,
                    'sgst_sale_6_mh': float(row[46]) if str(row[46]) != 'nan' else 0,
                    'cgst_sale_6_mh': float(row[47]) if str(row[47]) != 'nan' else 0,
                    'sgst_sale_9_mh': float(row[48]) if str(row[48]) != 'nan' else 0,
                    'cgst_sale_9_mh': float(row[49]) if str(row[49]) != 'nan' else 0,
                    'igst_18_output_mh': float(row[50]) if str(row[50]) != 'nan' else 0,
                    'igst_5_output_dl': float(row[51]) if str(row[51]) != 'nan' else 0,
                    'sgst_sale_9': float(row[52]) if str(row[52]) != 'nan' else 0,
                    'cgst_sale_9': float(row[53]) if str(row[53]) != 'nan' else 0,
                    'igst_18': float(row[54]) if str(row[54]) != 'nan' else 0,
                    'igst_0_output_mh': float(row[55]) if str(row[55]) != 'nan' else 0,
                }
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
