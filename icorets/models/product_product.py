from odoo import models, fields, api, _


class ProductVariantInherit(models.Model):
    _inherit = "product.product"

    variants_ean_code = fields.Char('EAN Code', tracking=True)
    default_code = fields.Char('Internal Reference', index=True, tracking=True)
    variant_article_code = fields.Char(string='Article Code', tracking=True)
    variants_asin = fields.Char('ASIN')
    variants_func_spo = fields.Char(related='product_tmpl_id.func_spo', string='Function / Sport')
    variants_gender = fields.Char(related='product_tmpl_id.gender', string='Gender')
    variants_tech_feat = fields.Char(related='product_tmpl_id.tech_feat', string='Technology / Features')
    variants_fsn = fields.Char('FSN')
    variant_cost = fields.Float('Invalid Cost')  # not used
    variant_packaging_cost = fields.Float('Packaging Cost')
    variant_total_cost = fields.Float('Total Cost')
    brand_id_rel = fields.Many2one(related='product_tmpl_id.brand_id', string="Brand")
    color = fields.Char('Color')
    size = fields.Char('Size')
    buin = fields.Char('BUIN')
    age_group = fields.Char(related='product_tmpl_id.age_group', string='Age Group')
    myntra = fields.Char('Myntra')
    ajio = fields.Char('Ajio')
    fancode = fields.Char('Fancode')
    blinkit = fields.Char('Blinkit')
    zepto = fields.Char('Zepto')
    swiggy = fields.Char('Swiggy')
    bigbasket = fields.Char('Bigbasket')
    product_net_weight = fields.Char(string='Product Net Weight (gms)11')
    product_dimension1 = fields.Char(string='Product Dimension (cm)')
    product_dimension2 = fields.Char(string='Product Dimension (cm)')
    product_dimension3 = fields.Char(string='Product Dimension (cm)')
    package_dimension1 = fields.Char(string='Package Dimension (cm)')
    package_dimension2 = fields.Char(string='Package Dimension (cm)')
    package_dimension3 = fields.Char(string='Package Dimension (cm)')
    package_weight = fields.Char(string='Package Weight (gms)')

    market_place_tittle = fields.Char(string='Marketplace Tittle')
    bullet_point_1 = fields.Char(string='Bullet Point 1')
    bullet_point_2 = fields.Char(string='Bullet Point 2')
    bullet_point_3 = fields.Char(string='Bullet Point 3')
    bullet_point_4 = fields.Char(string='Bullet Point 4')
    bullet_point_5 = fields.Char(string='Bullet Point 5')
    description = fields.Char(string='Description')

    google_drive_link = fields.Char(string='Google Drive Link')
    drop_box_link = fields.Char(string='Drop Box Link')
    country_origin = fields.Char(related='product_tmpl_id.country_origin', string='Country of Origin')

    # Inherited and removed domain
    product_template_variant_value_ids = fields.Many2many(
        'product.template.attribute.value',
        relation='product_variant_combination',
        string="Variant Values",
        ondelete='restrict',
    )

    # For updating standard price by sum of cost and packaging cost
    @api.onchange('standard_price', 'variant_packaging_cost')
    def sum_cost(self):
        if self.standard_price and self.variant_packaging_cost:
            self.variant_total_cost = self.standard_price + self.variant_packaging_cost

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            tmpl = rec.product_tmpl_id
            rec.product_net_weight = tmpl.product_net_weight
            rec.product_dimension1 = tmpl.product_dimension1
            rec.product_dimension2 = tmpl.product_dimension2
            rec.product_dimension3 = tmpl.product_dimension3
            rec.package_dimension1 = tmpl.package_dimension1
            rec.package_dimension2 = tmpl.package_dimension2
            rec.package_dimension3 = tmpl.package_dimension3
            rec.package_weight = tmpl.package_weight
            rec.market_place_tittle = tmpl.market_place_tittle
            rec.bullet_point_1 = tmpl.bullet_point_1
            rec.bullet_point_2 = tmpl.bullet_point_2
            rec.bullet_point_3 = tmpl.bullet_point_3
            rec.bullet_point_4 = tmpl.bullet_point_4
            rec.bullet_point_5 = tmpl.bullet_point_5
            rec.description = tmpl.description
        return res
