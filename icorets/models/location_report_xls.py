import datetime
from odoo import api, models, fields, _


class LocationReportWizard(models.TransientModel):
    _name = 'locations.report'

    def location_report_xlsx(self):
        return self.env.ref('crm_timesheet.location_report_action_xls').report_action(self)
#
# class LocationReport(models.AbstractModel):
#     _name = "report.crm_timesheet.location_report_xls"
#     _inherit = "report.report_xlsx.abstract"

    # def generate_xlsx_report(self, workbook, data, sale_report):
    #     worksheet = workbook.add_worksheet()
    #     token_list = self.search_invnt(sale_report)
    #     for obj in sale_report:
    #
    #         # Formatting For Data in Excel Sheet
    #         date_format = workbook.add_format({'num_format': 'dd/mm/YYYY', 'font': 'Arial', 'align': 'center', 'valign': 'vcenter','font_size': 8,'border': 1})
    #         title_format = workbook.add_format({
    #             'font_size': 8,
    #             'font': 'Arial',
    #             'border': 1,
    #             'align': 'center',
    #             'bg_color': '#ccccff',
    #             'valign': 'vcenter'})
    #         output_format = workbook.add_format({
    #             'font_size': 8,
    #             'font': 'Arial',
    #             'align': 'left',
    #             'border': 1,
    #             'valign': 'vcenter'})
    #         header_format = workbook.add_format({
    #             'font_size': 14,
    #             'font': 'Arial',
    #             'bold': 1,
    #             'align': 'center',
    #             'valign': 'vcenter'})
    #
    #         # Heading for the values in Excel Sheet
    #         worksheet.merge_range('A1:', 'Location Report', header_format)
    #         headers = ['Brand','Category 1','Category 2','Category 3','Function Sport','Gender',
    #                    'Title','Composition / Material','Technology / Features','Event','HSN Code','Style Code',
    #                    'Article Code','EAN Code','ASIN','FSIN','Colour','Size','MRP','GST','IHO Stock', 'Bhiwandi Stock', 'Delhi Stock']
    #
    #         row = 2
    #
    #         for index, value in enumerate(headers):
    #             worksheet.write(row, index, value, title_format)
    #         row = 3
    #         col = 0
    #         # Adding values in Excel sheet from the Dictionary
    #         for token in token_list:
    #             worksheet.write(row, 0, token['Brand'] or ' ', date_format)
    #             worksheet.write(row, 1, token['Category 1'] or ' ', output_format)
    #             worksheet.write(row, 2, token['Category 2'] or ' ', output_format)
    #             worksheet.write(row, 3, token['Category 3'] or ' ', output_format)
    #             worksheet.write(row, 4, token['Function Sport'] or ' ', date_format)
    #             worksheet.write(row, 5, token['Gender'] or ' ', output_format)
    #             worksheet.write(row, 6, token['Title'] or ' ', date_format)
    #             worksheet.write(row, 7, token['Composition / Material'] or ' ', output_format)
    #             worksheet.write(row, 8, token['Technology / Features'] or ' ', output_format)
    #             worksheet.write(row, 9, token['Event'] or ' ', output_format)
    #             worksheet.write(row, 10, token['HSN Code'] or ' ', output_format)
    #             worksheet.write(row, 11, token['Style Code'] or ' ', output_format)
    #             worksheet.write(row, 12, token['Article Code'] or ' ', output_format)
    #             worksheet.write(row, 13, token['EAN Code'] or ' ', output_format)
    #             worksheet.write(row, 14, token['ASIN'] or ' ', output_format)
    #             worksheet.write(row, 14, token['FSIN'] or ' ', output_format)
    #             worksheet.write(row, 14, token['Colour'] or ' ', output_format)
    #             worksheet.write(row, 14, token['Size'] or ' ', output_format)
    #             worksheet.write(row, 14, token['MRP'] or ' ', output_format)
    #             worksheet.write(row, 14, token['GST'] or ' ', output_format)
    #             worksheet.write(row, 14, token['IHO Stock'] or ' ', output_format)
    #             worksheet.write(row, 14, token['Bhiwandi Stock'] or ' ', output_format)
    #             worksheet.write(row, 14, token['Delhi Stock'] or ' ', output_format)
    #             row = row + 1

    # def search_invnt(self, report_data):
    #     data_list = []
    #
    #     # Domains for filtering according to fields in form view
    #     search_domain = []
    #     # Location Filter
    #     search_domain.append(('location_id.usage','=', 'internal'))
    #
    #     # Filter records according to filters
    #     loc_products = self.env['stock.quant'].search(search_domain)
    #     # Assigning Data in a variable to sort in Dictionary
    #     for inv in loc_products:
    #         inv_dict = self.invoice_dict(inv)
    #         data_list.append(inv_dict)
    #
    #
    #     return data_list

    # Function for Assigning data in a Dictionary
    # def invoice_dict(self, inv):
    #     bom_assy = {
    #         'Brand':inv.product_id.brand_id_rel or '',
    #         'Category 1': inv.product_id.product_tmpl_id.categ_id.name or '',
    #         'Category 2': '',
    #         'Category 3': '',
    #         'Function Sport': inv.product_id.variants_func_spo or '',
    #         'Gender': inv.product_id.gender or '',
    #         'Title': inv.product_id.name or '',
    #         'Composition / Material': inv.product_id.material or '',
    #         'Technology / Features':inv.product_id.variants_tech_feat,
    #         'Event': inv.product_id.occasion or '',
    #         'HSN Code': inv.product_id.l10n_in_hsn_code or inv.product_id.sale_hsn,
    #         'Style Code': inv.product_id.style_code or '',
    #         'Article Code': inv.product_id.variant_article_code or '',
    #         'EAN Code': inv.product_id.barcode or '',
    #         'ASIN': inv.product_id.variants_asin or '',
    #         'FSIN': inv.product_id.variants_fsn or '',
    #         'Colour': inv.product_id.color or '',
    #         'Size': inv.product_id.size or '',
    #         'MRP': inv.product_id.standard_price or '',
    #         'GST': inv.product_id.taxes_id.ids or '',
    #         'IHO Stock': '',
    #         'Bhiwandi Stock': '',
    #         'Delhi Stock': '',
    #     }
    #     return bom_assy


class LocationReport(models.AbstractModel):
    _name = "report.crm_timesheet.location_report_xls"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):

        bold = workbook.add_format(
            {'font_size': 11, 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7', 'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        bold_red = workbook.add_format(
            {'font_size': 11,'color':'#FF0000', 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7', 'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        bold_one = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bg_color': '#b7b7b7'})
        sheet = workbook.add_worksheet('Location Report')
        sheet.set_column(0, 0, 20)
        sheet.set_column(0, 1, 25)
        sheet.set_column(0, 2, 25)
        sheet.set_column(0, 3, 25)
        sheet.set_column(0, 4, 25)
        sheet.set_column(0, 5, 25)
        sheet.set_column(0, 6, 25)
        sheet.set_column(0, 7, 25)
        sheet.set_column(0, 8, 25)
        sheet.set_column(0, 9, 25)
        sheet.set_column(0, 10, 25)
        sheet.set_column(0, 11, 25)
        sheet.set_column(0, 12, 25)
        sheet.set_column(0, 13, 25)
        sheet.set_column(0, 14, 25)
        sheet.set_column(0, 15, 25)
        sheet.set_column(0, 16, 25)
        sheet.set_column(0, 17, 25)
        sheet.set_column(0, 18, 25)
        sheet.set_column(0, 19, 25)
        sheet.set_column(0, 20, 25)
        sheet.set_column(0, 21, 25)
        sheet.set_column(0, 22, 25)
        sheet.set_column(0, 23, 25)

        # # **************************************************
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Category 1', bold)
        sheet.write(0, 2, 'Category 2', bold)
        sheet.write(0, 3, 'Category 3', bold)
        sheet.write(0, 4, 'Function Sport', bold)
        sheet.write(0, 5, 'Gender', bold)
        sheet.write(0, 6, 'Title', bold)
        sheet.write(0, 7, 'Composition / Material', bold)
        sheet.write(0, 8, 'Technology / Features', bold)
        sheet.write(0, 9, 'Event', bold)
        sheet.write(0, 10, 'HSN Code', bold)
        sheet.write(0, 11, 'Style Code', bold)
        sheet.write(0, 12, 'Article Code', bold)
        sheet.write(0, 13, 'EAN Code', bold)
        sheet.write(0, 14, 'ASIN', bold)
        sheet.write(0, 15, 'FSIN', bold)
        sheet.write(0, 16, 'Colour', bold)
        sheet.write(0, 17, 'Size', bold)
        sheet.write(0, 18, 'MRP', bold)
        sheet.write(0, 19, 'GST', bold)
        sheet.write(0, 20, 'IHO Stock', bold)
        sheet.write(0, 21, 'Bhiwandi Stock', bold)
        sheet.write(0, 22, 'Delhi Stock', bold)
        sheet.write(0, 23, 'Forecasted Qty', bold)

        row = 1
        col = 0
        search_domain = []
        search_domain.append(('location_id.usage', '=', 'internal'))

        stock_q = self.env['stock.quant'].search(search_domain)

        for line in stock_q:
            sheet.write(row, col, line.product_id.brand_id_rel.name or '')

            sheet.write(row, col + 1, line.product_id.categ_id.name or '')
            sheet.write(row, col + 2, line.product_id.categ_id.parent_id.name or '')
            sheet.write(row, col + 3, line.product_id.categ_id.parent_id.parent_id.name or '')
            sheet.write(row, col + 4, line.product_id.variants_func_spo or '')
            sheet.write(row, col + 5, line.product_id.gender or '')
            sheet.write(row, col + 6, line.product_id.name or '')
            sheet.write(row, col + 7, line.product_id.material or '')
            sheet.write(row, col + 8, line.product_id.variants_tech_feat)
            sheet.write(row, col + 9, line.product_id.occasion or '')
            sheet.write(row, col + 10, line.product_id.l10n_in_hsn_code or line.product_id.sale_hsn.hsnsac_code or '')
            sheet.write(row, col + 11, line.product_id.style_code or '')
            sheet.write(row, col + 12, line.product_id.variant_article_code or '')
            sheet.write(row, col + 13, line.product_id.barcode or '')
            sheet.write(row, col + 14, line.product_id.variants_asin or '')
            sheet.write(row, col + 15, line.product_id.variants_fsn or '')
            sheet.write(row, col + 16, line.product_id.color or '')
            sheet.write(row, col + 17, line.product_id.size or '')
            sheet.write(row, col + 18, line.product_id.lst_price or '')
            sheet.write(row, col + 19, (''.join([str(x) for x in line.product_id.taxes_id.name])) or '')
            sheet.write(row, col + 20, line.inventory_quantity_auto_apply if line.location_id.location_id.name == 'IHO' else '')
            sheet.write(row, col + 21, line.inventory_quantity_auto_apply if line.location_id.location_id.name == 'BHW' else '')
            sheet.write(row, col + 22, line.inventory_quantity_auto_apply if line.location_id.location_id.name == 'DEL' else '')
            sheet.write(row, col + 23, line.product_id.virtual_available or '')

            row = row + 1

