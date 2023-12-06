from odoo import models, fields, api

class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    latitude = fields.Float(string='Latitude', digits=(9, 6))
    longitude = fields.Float(string='Longitude', digits=(9, 6))
    google_maps_url = fields.Char(string='Google Maps URL', compute='_compute_google_maps_url', store=True)



    def _generate_google_maps_url(self, latitude, longitude):
        return f"https://www.google.com/maps?q={latitude},{longitude}"

    @api.depends('latitude', 'longitude')
    def _compute_google_maps_url(self):
        for line in self:
            if line.latitude and line.longitude:
                line.google_maps_url = self._generate_google_maps_url(line.latitude, line.longitude)
            else:
                line.google_maps_url = False

    @api.model
    def create(self, values):
        if 'lattitude' not in values or 'longitude' not in values:
            lat, lon = self._get_user_location()
            values['latitude'] = lat
            values['longitude'] = lon
        return super(AccountAnalyticLineInherit, self).create(values)

    def _get_user_location(self):
        user_location = self.env['base.geocoder'].geo_find(addr='')
        if user_location and isinstance(user_location,dict) and 'latitude' in user_location and 'longitude' in user_location:
            return user_location['latitude'], user_location['longitude']
        else:
            return 0.0, 0.0