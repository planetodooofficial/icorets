# -*- coding: utf-8 -*-


{
    'name': 'Print Journal Entries Report in Odoo',
    'version': '16.0.0.2',
    'category': 'Account',
    'license': 'OPL-1',
    'summary': 'Allow to print pdf report of Journal Entries.',
    'description': """
    Allow to print pdf report of Journal Entries.
    journal entry

    
""",
    'price': 000,
    'currency': 'INR',
    'author': 'Teckzilla Technologies',
    'website': 'https://www.planetodoo.com',
    'depends': ['base','account'],
    'data': [
            'report/report_journal_entries.xml',
            'report/report_journal_entries_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    "images":[],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
