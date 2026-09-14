{
    'name': 'GTS ICore Reports',
    'version': '19.0.1.0.0',
    'summary': 'ICore Accounting, Stock, Registers & Delivery Reports',
    'description': """
GTS ICore Reports Module for Odoo 19:
- Partner Ledger (PDF)
- Ledger Confirmation (PDF)
- Sales & Purchase Registers (Excel / CSV)
- Detailed Sales & Purchase Registers
- Stock Register & Location Wise Reports (Excel)
- GRN / GRS Details Import & Report
- E-waybill Invoice Custom Report
    """,
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': [
        'base',
        'account',
        'stock',
        'stock_account',
        'gts_account',
        'report_xlsx',
        'account_reports',
    ],
    'category': 'Accounting/Accounting',
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'report/report_actions.xml',
        'report/ewaybill_invoice_report.xml',
        'views/partner_ledger_views.xml',
        'views/ledger_confirmation.xml',
        'views/grn_details_data_view.xml',
        'wizard/stock_register_view.xml',
        'wizard/stock_location_wise_view.xml',
        'wizard/grs_details_view.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'gts_icore_reports/static/src/css/style.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
