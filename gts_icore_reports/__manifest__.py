
{
    'name': 'ICore Reports',
    'version': '14.0',
    'summary': 'ICore Reports',
    'description': 'Partner Ledger Report',
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': ['base','account_reports','account','po_accounting_v16', 'register_reports_v16'],
    'category': 'Accounting',
    'demo': [],
    'data': [
            'security/ir.model.access.csv',
            'report/report_actions.xml',
            'wizard/stock_location_wise_view.xml',
            'wizard/grs_details_view.xml',
            'views/grn_details_data_view.xml',
             ],
    'installable': True,
    'images': [],
    'qweb': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
