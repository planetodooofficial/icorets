odoo.define('accounting_pdf_reports.account_report', function (require) {
    'use strict';

    var accountReportsWidget = require('account_reports.account_report').accountReportsWidget;
    var core = require('web.core');
    var _t = core._t;

    accountReportsWidget.include({
        render_searchview_buttons: function() {
            this._super.apply(this, arguments);
            var self = this;

            // Set the default partner type if not already selected
            self.report_options.partner_type = self.report_options.partner_type || 'all';

            self.$searchview_buttons.find('.js_account_report_partner_choice_filter').click(function () {
                var $el = $(this);
                var selectedType = $el.data('type');

                // Update the partner_type based on selection
                self.report_options.partner_type = selectedType;
                var domain = [];

                if (selectedType === 'customer') {
                    domain = [['is_customer', '=', true]];
                    self.report_options.name_partner_type = 'Customer';
                } else if (selectedType === 'vendor') {
                    domain = [['is_supplier', '=', true]];
                    self.report_options.name_partner_type = 'Vendor';
                } else {
                    self.report_options.name_partner_type = 'All';
                }

                // Fetch partner IDs based on selection
                self._rpc({
                    model: 'res.partner',
                    method: 'search_read',
                    args: [domain, ['id', 'name']],
                }).then(function (result) {
                    self.report_options.partner_ids = result.map(partner => partner.id);
                    self.report_options.selected_partner_ids = [];

                    // Remove 'selected' class from all items
                    self.$searchview_buttons.find('.js_account_report_partner_choice_filter').removeClass('selected');

                    // Add 'selected' class to the clicked item
                    $el.addClass('selected');

                    // Store selected type in local storage (so it persists after reload)
                    localStorage.setItem('selected_partner_type', selectedType);

                    // Reload the report
                    self.reload();
                });
            });

            // Restore the selected option after reload
            var storedPartnerType = localStorage.getItem('selected_partner_type');
            if (storedPartnerType) {
                self.report_options.partner_type = storedPartnerType;
                self.$searchview_buttons.find('.js_account_report_partner_choice_filter[data-type="' + storedPartnerType + '"]').addClass('selected');
            }
        },
    });
});
