/*##################################################|*/
/* #CMS# */

// ensuring django namespace is set correctly
var django = window.django || undefined;

// ensuring jQuery namespace is set correctly
var jQuery = (django) ? django.jQuery : window.jQuery || undefined;

// ensuring Class namespace is set correctly
var Class = window.Class || undefined;

// ensuring CMS namespace is set correctly
var CMS = {
	'$': (jQuery) ? jQuery.noConflict() : undefined,
	'Class': (Class) ? Class.noConflict() : undefined,
	'API': {}
};

/*##################################################|*/
/* #CMS.API# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * CNS.API.Helpers
	 * Multiple helpers used accross all CMS features
	 */
	CMS.API.Helpers = {

		// redirects to a specific url or reloads browser
		reloadBrowser: function (url, timeout) {
			// is there a parent window?
			var parent = (window.parent) ? window.parent : window;
			// add timeout if provided
			parent.setTimeout(function () {
				(url) ? parent.location.href = url : parent.location.reload();
			}, timeout || 0);
		},

		// disable multiple form submissions
		preventSubmit: function () {
			var forms = $('#cms_toolbar').find('form');
			forms.submit(function (e) {
				// show loader
				CMS.API.Toolbar._loader(true);
				// we cannot use disabled as the name action will be ignored
				$('input[type="submit"]').bind('click', function (e) {
					e.preventDefault();
				}).css('opacity', 0.5);
			});
		},

		// fixes csrf behaviour
		csrf: function (csrf_token) {
			$.ajaxSetup({
				beforeSend: function (xhr) {
					// set csrf_token
					xhr.setRequestHeader("X-CSRFToken", csrf_token);
				}
			});
		},

		// handles the tooltip for the plugins
		showTooltip: function (name, id) {
			var tooltip = $('.cms_tooltip');

			// change css and attributes
			tooltip.css('visibility', 'visible')
				.data('plugin_id', id)
				.show()
				.find('span').html(name);

			// attaches move event
			// this sets the correct position for the edit tooltip
			$('body').bind('mousemove.cms', function (e) {
				// so lets figure out where we are
				var offset = 20;
				var bound = $(document).width();
				var pos = e.pageX + tooltip.outerWidth(true) + offset;

				tooltip.css({
					'left': (pos >= bound) ? e.pageX - tooltip.outerWidth(true) - offset : e.pageX + offset,
					'top': e.pageY - 12
				});
			});

			// attach tooltip event for touch devices
			tooltip.bind('touchstart.cms', function () {
				$('#cms_plugin-' + $(this).data('plugin_id')).trigger('dblclick');
			});
		},

		hideTooltip: function () {
			var tooltip = $('.cms_tooltip');

			// change css
			tooltip.css('visibility', 'hidden').hide();

			// unbind events
			$('body').unbind('mousemove.cms');
			tooltip.unbind('touchstart.cms');
		},

		// sends or retrieves a JSON from localStorage or the session if local storage is not available
		setSettings: function (settings) {
			// merge settings
			settings = JSON.stringify($.extend({}, CMS.config.settings, settings));

			// use local storage or session
			if(window.localStorage) {
				// save within local storage
				localStorage.setItem('cms_cookie', settings);
			} else {
				// save within session
				$.ajax({
					'type': 'POST',
					'url': CMS.config.urls.settings,
					'data': {
						'type': 'set',
						'settings': settings
					},
					'success': function (data) {
						console.log('setSettings');
						settings = data;
					},
					'error': function (jqXHR) {
						that.showError(jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText);
					}
				});
			}

			// ensure new settings are returned
			return settings;
		},

		getSettings: function () {
			var settings;

			// use local storage or session
			if(window.localStorage) {
				// get from local storage
				settings = JSON.parse(localStorage.getItem('cms_cookie'));
			} else {
				// get from session
				$.ajax({
					'type': 'POST',
					'url': CMS.config.urls.settings,
					'data': { 'type': 'get' },
					'success': function (data) {
						console.log('getSettings');
						settings = JSON.parse(data);
					},
					'error': function (jqXHR) {
						that.showError(jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText);
					}
				});
			}

			// set settings are not defined, ensure they are
			if(settings === null) settings = this.setSettings(CMS.config.settings);

			// ensure new settings are returned
			return settings;
		},

		// prevents scrolling when another scrollbar is used (for better ux)
		preventScroll: function (disable) {
			// disable
			return false;

			// cancel if scrollbar is not visible
			if($(document).height() <= $(window).height()) return false;

			var scrollTop = $(window).scrollTop();
			var html = $('html');

			if(disable) {
				html.addClass('cms_toolbar-noscroll').css('top',-scrollTop).data('scroll', scrollTop);
			} else {
				html.removeClass('cms_toolbar-noscroll');
				$(window).scrollTop(html.data('scroll'));
			}
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);

// this will be fixed in jQuery 1.6+
(function ( $ ) {
    var filters = $.expr[":"];
    if ( !filters.focus ) {
        filters.focus = function( elem ) {
           return elem === document.activeElement && ( elem.type || elem.href );
        };
    }
})( CMS.$ );
