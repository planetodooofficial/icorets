{
    'name': 'Icore',
    'version': '1.2',
    'summary': 'ACcessories and product',
    'sequence': -100,
    'description': """ product """,
    'category': 'Productivity',
    'website': 'https://www.odoomates.tech',
    'depends': ['base', 'sale', 'product','sale_stock','stock','account', 'approvals', 'account_accountant','purchase','l10n_in','po_accounting_v16'],
    'license': 'LGPL-3',
    'application': True,
    'data': ['security/ir.model.access.csv',
             'data/forecast_sequence.xml',
             'views/icore_field.xml',
             'views/inherit_res_partner_view.xml',
             'views/inherit_stock_warehouse_view.xml',
             'views/forecast_order_view.xml',
             'views/inherit_approval_request_view.xml',
             'wizard/forecast_order_wiz_view.xml',
             'report/credit_note.xml',
             'report/debit_note.xml',
             'report/amazon.xml',
             'report/flipkart_report.xml',
             'report/myntra_report.xml',
             'report/creditnote_urban.xml',
             'report/tax_invoice.xml',
             'report/purchase_order_report.xml',
             'report/book_my_show.xml',
             'report/fynd_mishop.xml',
             'report/retail_pro.xml',
             ],
    'website': 'https://planet-odoo.com/',
    'installable': True,
    'auto_install': False,

}
