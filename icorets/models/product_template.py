from odoo import models, fields, api, _


class ProductInherit(models.Model):
    _inherit = "product.template"

    material = fields.Char('Moc')
    brand_id = fields.Many2one('product.brand', 'Brand')
    occasion = fields.Char('Event')
    style_code = fields.Char('Style Code', tracking=True)
    parent_buin = fields.Char('Parent buin')
    user_defined_miscallaneous1 = fields.Char('User Defined Miscallaneous1')
    user_defined_miscallaneous2 = fields.Char('User Defined Miscallaneous2')
    user_defined_miscallaneous3 = fields.Char('User Defined Miscallaneous3')
    user_defined_miscallaneous4 = fields.Char('User Defined Miscallaneous4')
    user_defined_miscallaneous5 = fields.Char('User Defined Miscallaneous5')
    age_group = fields.Char(string='Age Group')

    product_net_weight = fields.Char('Product Net Weight (gms)')
    product_dimension1 = fields.Char('Product Length (cm)')
    product_dimension2 = fields.Char('Product Breadth (cm)')
    product_dimension3 = fields.Char('Product Height (cm)')
    package_dimension1 = fields.Char('Package Length (cm)')
    package_dimension2 = fields.Char('Package Breadth (cm)')
    package_dimension3 = fields.Char('Package Height (cm)')
    package_weight = fields.Char('Package Gross Weight (gms)')

    # technical details
    manufactured_by = fields.Char('Manufactured By')
    marketed_by = fields.Char('Marketed By / Customer Care')
    length = fields.Float('Length (Dimensions)')
    width = fields.Float('width (Dimensions)')
    height = fields.Float('height (Dimensions)')
    weight = fields.Float('Weight (Dimensions)')
    manufacture_year = fields.Date('Manufacture Year')

    func_spo = fields.Char('Function / Sport')
    gender = fields.Char('Gender')
    tech_feat = fields.Char('Technology / Features')

    market_place_tittle = fields.Char('Marketplace Tittle')
    bullet_point_1 = fields.Char('Bullet Point 1')
    bullet_point_2 = fields.Char('Bullet Point 2')
    bullet_point_3 = fields.Char('Bullet Point 3')
    bullet_point_4 = fields.Char('Bullet Point 4')
    bullet_point_5 = fields.Char('Bullet Point 5')
    description = fields.Char('Description')
    google_drive_link = fields.Char('Google Drive Link')
    drop_box_link = fields.Char('Drop Box Link')
    country_origin = fields.Char('Country of Origin')

    _sql_constraints = [
        ('buin_unique', 'unique(buin)', "BUIN code can only be assigned to one product !"),
    ]

    # Added func for hsn
    @api.onchange('sale_hsn')
    def set_hsn(self):
        if self.sale_hsn:
            self.l10n_in_hsn_code = self.sale_hsn.hsnsac_code


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _rec_name = 'name'

    name = fields.Char('Brand Name')


class ReasonReason(models.Model):
    _name = 'reason.reason'
    _description = 'Reason'

    name = fields.Char(string='Reason')


class InheritProductAttribute(models.Model):
    _inherit = 'product.attribute'

    is_colour = fields.Boolean()
    is_size = fields.Boolean()
