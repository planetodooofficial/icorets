{
    'name': 'GTS Account',
    'version': '19.0.1.0.0',
    'summary': 'GTS Account & Indian Localization Features',
    'description': """
GTS Account module for Odoo 19:
- Partner Ledger Report
- POD Upload and Logistics Tracking
- TDS & Deductee Types Management
- HSN / SAC Masters
- Partial & Advance Payments Reconciliation
- Payments by Terms on Sales and Purchase Orders
- Maker / Checker Approval Workflows
- Multi-currency and Contra Entries
    """,
    'author': 'Geotechnosoft',
    'maintainer': 'Geotechnosoft',
    'company': 'Geotechnosoft',
    'website': 'https://planet-odoo.com/',
    'depends': [
        'base',
        'account',
        'sale',
        'purchase',
        'l10n_in',
        'l10n_in_sale',
        'account_reports',
        'mail',
        'report_xlsx',
    ],
    'category': 'Accounting/Accounting',
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/tds_report_views.xml',
        'report/purchase_invoice_report.xml',
        'data/mail_template_view.xml',
        'data/partner_ledger.xml',
        'data/sale_order_templates.xml',
        'wizard/upload_document_view.xml',
        'wizard/mail_wizard_views.xml',
        'wizard/payment_wizard_views.xml',
        'wizard/send_to_checker_views.xml',
        'wizard/tds_report_wizard_views.xml',
        'views/account_deductee_type_views.xml',
        'views/tds_section_views.xml',
        'views/hsn_code_views.xml',
        'views/account_tax_views.xml',
        'views/account_account_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/account_payment_views.xml',
        'views/account_payment_term_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
