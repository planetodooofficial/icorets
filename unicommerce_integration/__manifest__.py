{
    'name': 'Unicommerce Integration',
    'version': '1.0',
    'category': '',
    'sequence': -1,
    'summary': 'Magento Integration',
    'description': """
        Unicommerce Odoo Integration
        ========================
        This module is used to integrate magento with odoo sales
    """,
    'author': 'Teckzilla Technologies',
    'website': 'https://www.teckzilla.net/',
    'depends': ['base', 'sale', 'stock', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/crons.xml',
        'views/unicommerce_orders_view.xml',
        'views/shop_instance_view.xml',
        'views/shop_import_logs_view.xml',
        'views/shop_channel.xml',
        'views/menu_items.xml',
        'views/sale.xml',
        'views/account.xml',
        # 'views/stock_picking.xml',
        # 'views/stock_location.xml',
        'views/contacts.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
