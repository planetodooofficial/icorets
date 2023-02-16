{
    'name': 'Icore',
    'version': '1.2',
    'summary': 'ACcessories and product',
    'sequence': -100,
    'description': """ product """,
    'category': 'Productivity',
    'website': 'https://www.odoomates.tech',
    'depends': ['base', 'sale', 'product','stock'],
    'license': 'LGPL-3',
    'application': True,
    'data': ['security/ir.model.access.csv',
             'views/icore_field.xml',
             ],

}
