odoo.define('bi_payslip_portal.portal', function (require) {
'use strict';
	
	var publicWidget = require('web.public.widget');
	var rpc = require('web.rpc');

	publicWidget.registry.payslip = publicWidget.Widget.extend({
	    selector: '#wrap',
	    events: {
	        'click a[href="#from_to"]': '_onSearchCustomDate',
	        'click a[href="#batch"]': '_onSearchBatch',
	        'click .apply_date_range': '_onApplyDate',
	        'click .close_modal': '_onClose',
	    },

	    start: function(){
	    	if($('a[href="#from_to"]').hasClass('active')){
	    		$('.o_portal_search_panel input').attr('disabled', true);
	    	};
	    },

	    _onSearchCustomDate: function(ev){
	    	ev.preventDefault();
	    	var modal = document.getElementById('rangemodal');
	    	modal.style.display = "block";
	    },

	    _onApplyDate: function(ev){
	    	ev.preventDefault();
	    	$('.o_portal_search_panel input').attr('disabled',true);
	    	var modal = document.getElementById('rangemodal');
	    	var date_from = $('input[name="date_from"]').val();
	    	var date_to = $('input[name="date_to"]').val();
	    	var search = moment(date_from.toString()).format("MM/DD/YYYY") +'-' + moment(date_to.toString()).format("MM/DD/YYYY");
	    	$('.o_portal_search_panel input').attr('value',search);
	    	modal.style.display = "none";
	    },
	    _onSearchBatch: function(ev){
	    	ev.preventDefault();
	    	$('.o_portal_search_panel input').attr('disabled', false);
	    },
	    _onClose: function(ev){
	    	ev.preventDefault();
	    	var modal = document.getElementById('rangemodal');
	    	modal.style.display = "none";
	    },
	});
	
});