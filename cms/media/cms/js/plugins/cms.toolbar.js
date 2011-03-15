/**
 * @author		Angelo Dini
 * @copyright	http://www.divio.ch under the BSD Licence
 * @requires	Classy, jQuery
 *
 * check if classy.js exists */
 if(window['Class'] === undefined) log('classy.js is required!');

/*##################################################|*/
/* #CUSTOM APP# */
(function ($, Class) {
	/**
	 * Toolbar
	 * @version: 0.0.1
	 */
	CMS.Toolbar = Class.$extend({

		options: {
			'page_is_defined': false,
			'edit_mode': false
		},

		initialize: function (container, options) {
			// save reference to this class
			var classy = this;
			// check if only one element is found
			if($(container).length > 2) { log('Toolbar Error: one element expected, multiple elements given.'); return false; }
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save toolbar elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.toolbar.left = this.toolbar.find('.cms_toolbar-left');
			this.toolbar.right = this.toolbar.find('.cms_toolbar-right');
			this.dim = this.wrapper.find('#cms_toolbar-dim');
			
			// bind event to toggle button
			this.toggle = this.wrapper.find('#cms_toolbar-toggle');
			this.toggle.bind('click', function (e) {
				e.preventDefault();
				classy.toggleToolbar();
			});
			
			// csrf security patch
			patchCsrf(jQuery);
			
			this.types = {};
			this.types['anchor'] = function_that_handles_anchors_inserted_into()
			
			// initial setups
			this._setup();
		},
		
		_setup: function () {
			// set if toolbar is visible or not
			($.cookie('CMS_toolbar-collapsed') == 'false') ? this.toolbar.data('collapsed', true) : this.toolbar.data('collapsed', false);
			
			// init scripts
			this.toggleToolbar();
		},
		
		toggleToolbar: function () {
			(this.toolbar.data('collapsed')) ? this._showToolbar() : this._hideToolbar();
		},
		
		_showToolbar: function () {
			var classy = this;
			// add toolbar padding
			var padding = parseInt($(document.body).css('margin-top'));
				setTimeout(function () {
					$(document.body).css('margin-top', (padding+classy.toolbar.height()));
				}, 10);
			// show toolbar
			this.toolbar.show();
			// change data information
			this.toolbar.data('collapsed', false);
			// add class to trigger
			this.toggle.addClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', false, { path:'/', expires:7 });
		},
		
		_hideToolbar: function () {
			// remove toolbar padding
			var padding = parseInt($(document.body).css('margin-top'));
				$(document.body).css('margin-top', (padding-this.toolbar.height()));
			// hide toolbar
			this.toolbar.hide();
			// change data information
			this.toolbar.data('collapsed', true);
			// remove class from trigger
			this.toggle.removeClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', true, { path:'/', expires:7 });
		},
		
		toggleDim: function () {
			(this.toolbar.data('dimmed')) ? this._showDim() : this._hideDim();
		},
		
		_showDim: function () {
			var classy = this;
			// stop window from scrolling
			// $(document.body).css('overflow', 'hidden');
			// attach resize event to window
			$(window).bind('resize', function () {
				classy.dim.css({
					'width': $(document).width(),
					'height': $(document).height(),
				});
			});
			// init dim resize
			$(window).resize();
			// change data information
			this.toolbar.data('dimmed', false);
			// show dim
			this.dim.stop().fadeIn();
		},
		
		_hideDim: function () {
			// retain window from scrolling
			// $(document.body).css('overflow', 'auto');
			// unbind resize event
			$(window).unbind('resize');
			// change data information
			this.toolbar.data('dimmed', true);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
		},
		
		registerItem: function (obj) {
			// error handling
			if(!obj.order) obj.dir = 0;

			// check for internal types
			switch(obj.type) {
				case 'anchor':
					this._registerAnchor(obj);
					break;
				case 'html':
					this._registerHtml(obj);
					break;
				case 'switcher':
					this._registerSwitcher(obj);
					break;
				case 'button':
					this._registerButton(obj);
					break;
				case 'list':
					this._registerList(obj);
					break;
				default:
					// if debug: FAIL LOUD
					// else: fail silently
			}
		},
		
		registerItems: function (items) {
			// make sure an array is passed
			if(typeof(items) != 'object') return false;
			// save reference to this class
			var classy = this;
			// loopp through all items and pass them to single function
			$(items).each(function (index, value) {
				classy.registerItem(value);
			});
		},
		
		registerType: function () {
			log('you want new type?');
		},
		
		_registerAnchor: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_anchor', obj);
			this._injectItem(template, obj.dir, obj.order);
		},
		
		_registerHtml: function (obj) {
			// here we dont need processTemplate cause we create the template
			var template = (obj.html) ? $(obj.html) : $(obj.htmlElement);
			// add order, show item
			template.data('order', obj.order).css('display', 'block');
			// add class if neccessary
			if(obj.class) template.addClass(obj.class);
			// add events
			template.find('.cms_toolbar-btn').bind('click', function (e) {
				e.preventDefault();
				(obj.redirect) ? window.location = obj.redirect : $(this).parentsUntil('form').parent().submit();
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},
		
		_registerSwitcher: function (obj) {
			// save reference to this class
			var classy = this;
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_switcher', obj);
			// should btn be shown?
			var btn = template.find('.cms_toolbar-item_switcher-link span');
			
			// initial setup
			if(obj.state == 'on') {
				btn.data('state', 'on').css('backgroundPosition', '0px -198px');
			} else {
				btn.data('state', 'off').css('backgroundPosition', '-40px -198px');
			}
			
			// add events
			template.find('.cms_toolbar-item_switcher-link').bind('click', function (e) {
				e.preventDefault();
				
				// animate toggle effect and trigger handler
				if(btn.data('state') == 'on') {
					btn.stop().animate({'backgroundPosition': '-40px -198px'}, function () {
						// disable link
						var url = classy._removeUrl(window.location.href, obj.addParameter);
						window.location = classy._insertUrl(url, obj.removeParameter, "")
					});
				} else {
					btn.stop().animate({'backgroundPosition': '0px -198px'}, function () {
						// enable link
						window.location = classy._insertUrl(location.href, obj.addParameter, "");
					});
				}
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},
		
		_registerButton: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_button', obj);
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},
		
		_registerList: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_list', obj);
			
			// here i have to do some crazy shit
			
			
			
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},
		
		_processTemplate: function (class, obj) {
			var template = this.wrapper.find(class).clone();
				template = $('<div>').append(template).clone().remove().html();
			// replace placeholders
			if(obj.title) template = template.replace('[title]', obj.title);
			if(obj.url) template = template.replace('[url]', obj.url);
			template = (obj.token) ? template.replace('[token]', obj.token) : template.replace('[token]', '');
			template = (obj.action) ? template.replace('[action]', obj.action) : template.replace('[action]', '');
			template = (obj.hidden) ? template.replace('[hidden]', obj.hidden) : template.replace('[hidden]', '');
			// back to jquery object
			template = $(template);
			if(obj.class) template.addClass(obj.class);
			if(obj.icon) template.find('.cms_toolbar-btn_right').addClass(obj.icon);
			// add events
			template.find('.cms_toolbar-btn').bind('click', function (e) {
				e.preventDefault();
				(obj.redirect) ? window.location = obj.redirect : $(this).parentsUntil('form').parent().submit();
			});
			// save order remove id and show element
			template.data('order', obj.order)
					.attr('id', '')
					.css('display', 'block');
			
			return template;
		},
		
		_injectItem: function (el, dir, order) {
			// save some vars
			var left = this.toolbar.left;
			var right = this.toolbar.right;
			
			if(dir == 'left') {
				var leftContent = left.find('> *');
					if(!leftContent.length) { left.append(el); return false; }
				
				// and what happens if there is already an element?
				leftContent.each(function (index, item) {
					// sava data from element
					var current = $(item).data('order');
					// inject data when current is lower, repeat till element fits position
					if(order >= current || order == current) el.insertAfter($(item));
				});
			}
			
			if(dir == 'right') {
				var rightContent = right.find('> *');
					if(!rightContent.length) { right.append(el); return false; }
				
				rightContent.each(function (index, item) {
					// save data from element
					var current = $(item).data('order');
					// inject data when current is lower, repeat till element fits position
					if(order >= current || order == current) el.insertAfter($(item));
				});
			}
		},
		
		_insertUrl: function (url, name, value) {
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1); 
			dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			var get_args = false;
			if(url.split("?").length>1) get_args = true;
			if(splits.length > 1){
				var after = "";
				if(splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				url = splits[0] + name;
				if(value) url += "=" + value
				url += "&" + after;
			} else {
				if(get_args) { url = url + "&" + name; } else { url = url + "?" + name; }
				if(value) url += "=" + value;
			}
			if(dash_splits.length>1) url += '#' + dash_splits[1];
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1);
			
			return url;
		},
		
		_removeUrl: function (url, name) {
			var dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			if(splits.length > 1){
				var after = "";
				if (splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				if (splits[0].substr(splits[0].length-2, splits[0].length-1)=="?" || !after) {
					url = splits[0] + after;
				} else {
					url = splits[0] + "&" + after;
				}
			}
			if(url.substr(url.length-1,1) == "?") url = url.substr(0, url.length-1);
			if(dash_splits.length > 1 && dash_splits[1]) url += "#" + dash_splits[1];
			
			return url;
		}

	});
	
	//CMS.Collapse
	// need some awesome show hide effects
	
	// new Toolbar();
})(jQuery, Class);