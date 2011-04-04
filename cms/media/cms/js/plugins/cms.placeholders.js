/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery, jQuery.ui.core, jQuery.ui.draggable, jQuery.ui.droppable
 *
 * assign Class and CMS namespace */
 var Class = Class || {};
 var CMS = CMS || {};

/*##################################################|*/
/* #CUSTOM APP# */
jQuery(document).ready(function ($) {
	/**
	 * Placeholders
	 * @version: 0.1.1
	 * @description: Handles placeholders when in editmode and adds "lightbox" to toolbar
	 * @public_methods:
	 *	- CMS.Placeholder.addPlugin(url, obj);
	 *	- CMS.Placeholder.editPlugin(placeholder_id, plugin_id);
	 *	- CMS.Placeholder.deletePlugin(placeholder_id, plugin_id);
	 *	- CMS.Placeholder.toggleFrame();
	 *	- CMS.Placeholder.toggleDim();
	 */
	CMS.Placeholders = Class.$extend({

		options: {
			'edit_mode': false,
			'lang': {
				'move_warning': '',
				'delete_request': '',
				'cancel': 'Cancel'
			},
			'urls': {
				'cms_page_move_plugin': '',
				'cms_page_changelist': '',
				'cms_page_change_template': '',
				'cms_page_add_plugin': '',
				'cms_page_remove_plugin': ''
			}
		},

		initialize: function (container, options) {
			// save reference to this class
			var classy = this;
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save placeholder elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.dim = this.wrapper.find('#cms_placeholder-dim');
			this.frame = this.wrapper.find('#cms_placeholder-content');
			this.timer = function () {};
			this.overlay = this.wrapper.find('#cms_placeholder-overlay');
			this.overlayIsHidden = false;
			this.success = this.wrapper.find('#cms_placeholder-success');

			// attach event handling to placeholder buttons and overlay if editmode is active
			if(this.options.edit_mode) {
				this.bars = $('.cms_placeholder-bar');
				this.bars.each(function (index, item) {
					classy._bars.call(classy, item);
				});
				
				// enable dom traversal for cms_placeholder
				this.holders = $('.cms_placeholder');
				this.holders.bind('mouseenter', function (e) {
					classy._holders.call(classy, e.currentTarget);
				});
			}
			
			// setup everything
			this._setup();
		},
		
		_setup: function () {
			// save reference to this class
			var classy = this;
			
			// set default dimm value to false
			this.dim.data('dimmed', false);
			
			// set defailt frame value to true
			this.frame.data('collapsed', true);
			
			// bind overlay event
			this.overlay.bind('mouseleave', function () {
				classy._hideOverlay();
			});
			// this is for testing
			this.overlay.find('.cms_placeholder-overlay_bg').bind('click', function () {
				classy._hideOverlay();
				
				// we need to hide the oberlay and stop the event for a while
				classy.overlay.css('visibility', 'hidden');
				
				// add timer to show element after second mouseenter
				setTimeout(function () {
					classy.overlayIsHidden = true;
				}, 100);
			});
		},
		
		/* this private method controls the buttons on the bar (add plugins) */
		_bars: function (el) {
			// save reference to this class
			var classy = this;
			var bar = $(el);
			
			// attach button event
			var barButton = bar.find('.cms_toolbar-btn');
				barButton.data('collapsed', true).bind('click', function (e) {
					e.preventDefault();
					
					($(this).data('collapsed')) ? classy._showPluginList.call(classy, $(e.currentTarget)) : classy._hidePluginList.call(classy, $(e.currentTarget));
				});
			
			// read and save placeholder bar variables
			var split = bar.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'language': split[0],
					'placeholder_id': split[1],
					'placeholder': split[2]
				};
			
			// attach events to placeholder plugins
			bar.find('.cms_placeholder-subnav li a').bind('click', function (e) {
				e.preventDefault();
				// add type to values
				values.plugin_type = $(this).attr('rel').split('::')[1];
				// try to add a new plugin
				classy.addPlugin.call(classy, classy.options.urls.cms_page_add_plugin, values);
			});
		},
		
		/* this private method shows the overlay when hovering */
		_holders: function (el) {
			// save reference to this class
			var classy = this;
			var holder = $(el);
			
			// show overlay
			this._showOverlay.call(classy, holder);
			
			// set overlay to visible
			if(this.overlayIsHidden === true) {
				this.overlay.css('visibility', 'visible');
				this.overlayIsHidden = false;
			}
			
			// get values
			var split = holder.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'plugin_id': split[0],
					'placeholder': split[1],
					'type': split[2],
					'slot': split[4]
				};

			// attach events to each holder button
			var buttons = this.overlay.find('.cms_placeholder-options li');
				// unbind all button events
				buttons.find('a').unbind('click');
				
				// attach edit event
				buttons.find('a[rel^=edit]').bind('click', function (e) {
					e.preventDefault();
					classy.editPlugin.call(classy, values.placeholder, values.plugin_id);
				});

				// attach move event
				buttons.find('a[rel^=moveup], a[rel^=movedown]').bind('click', function (e) {
					e.preventDefault();
					classy._movePluginPosition.call(classy, $(e.currentTarget).attr('rel'), holder, values);
				});

				// attach delete event
				buttons.find('a[rel^=delete]').bind('click', function (e) {
					e.preventDefault();
					classy.deletePlugin.call(classy, values.placeholder, values.plugin_id, holder);
				});

				// attach delete event
				buttons.find('a[rel^=more]').bind('click', function (e) {
					e.preventDefault();
					classy._morePluginOptions.call(classy, holder, values);
				});
		},
		
		addPlugin: function (url, data) {
			var classy = this;
			// do ajax thingy
			$.ajax({
				'type': 'POST',
				'url': url,
				'data': data,
				'success': function (response) {
					// we get the id back
					classy.editPlugin.call(classy, data.placeholder_id, response);
				},
				'error': function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});
		},
		
		editPlugin: function (placeholder_id, plugin_id) {
			var classy = this;
			var frame = this.frame.find('.cms_placeholder-content_inner');
			
			// show framebox
			CMS.Placeholders.toggleFrame();
			CMS.Placeholders.toggleDim();
			
			// load the template through the data id
			// for that we create an iframe with the specific url
			var iframe = $('<iframe />', {
				'id': 'cms_placeholder-iframe',
				'src': classy.options.urls.cms_page_changelist + placeholder_id + '/edit-plugin/' + plugin_id + '?popup=true&no_preview',
				'style': 'width:100%; height:0; border:none; overflow:auto;',
				'allowtransparency': true,
				'scrollbars': 'no',
				'frameborder': 0
			});
			
			// inject to element
			frame.html(iframe);
			
			// bind load event to injected iframe
			$('#cms_placeholder-iframe').load(function () {
				// set new height and animate
				var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true);
				$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				
				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');

				// add cancel button
				var btn = $(this).contents().find('input[name=_save]');
					btn.addClass('default').css('float', 'none');
				var cancel = $('<input type="submit" name="_cancel" value="' + classy.options.lang.cancel + '" style="margin-left:8px;" />');
					cancel.bind('click', function (e) {
						e.preventDefault();
						// hide frame
						CMS.Placeholders.toggleFrame();
						CMS.Placeholders.toggleDim();
					});
				cancel.insertAfter(btn);

				// do some css changes in template
				$(this).contents().find('#footer').css('padding', 0);
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		},
		
		deletePlugin: function (placeholder_id, plugin_id, plugin) {
			// lets ask if you are sure
			var message = this.options.lang.delete_request;
			var confirmed = confirm(message, true);
			
			// now do ajax
			if(confirmed) {
				$.ajax({
					'type': 'POST',
					'url': this.options.urls.cms_page_remove_plugin,
					'data': { 'plugin_id': plugin_id },
					'success': function () {
						// remove plugin from the dom
						plugin.remove();
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			}
		},
		
		_movePluginPosition: function (dir, plugin, values) {
			// save reference to this class
			var classy = this;
			// get all siblings within the placeholder
			var holders = plugin.siblings('.cms_placeholder').andSelf();
			// get selected index and bound
			var index = holders.index(plugin);
			var bound = holders.length;

			// if the there is only 1 element, we dont need to move anything
			if(bound <= 1) {
				alert(this.options.lang.move_warning);
				return false;
			}

			// create the array
			var array = [];

			holders.each(function (index, item) {
				array.push($(item).attr('class').split('::')[1]);
			});
			// remove current array
			array.splice(index, 1);

			// we need to check the boundary and modify the index if item jups to top or bottom
			if(index <= 0 && dir === 'moveup') {
				index = bound+1;
			} else if(index >= bound-1 && dir === 'movedown') {
				index = -1;
			}
			// add array to new position
			if(dir === 'moveup') array.splice(index-1, 0, values.plugin_id);
			if(dir === 'movedown') array.splice(index+1, 0, values.plugin_id);

			// now lets do the ajax request
			$.ajax({
				'type': 'POST',
				'url': this.options.urls.cms_page_move_plugin,
				'data': { 'ids': array.join('_') },
				'success': refreshPluginPosition,
				'error': function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});

			// lets refresh the elements in the dom as well
			function refreshPluginPosition() {
				if(dir === 'moveup' && index !== bound+1) plugin.insertBefore($(holders[index-1]));
				if(dir === 'movedown' && index !== -1) plugin.insertAfter($(holders[index+1]));
				// move in or out of boundary
				if(dir === 'moveup' && index === bound+1) plugin.insertAfter($(holders[index-2]));
				if(dir === 'movedown' && index === -1) plugin.insertBefore($(holders[index+1]));

				// close overlay
				classy._hideOverlay();

				// show success overlay for a second
				classy.success.css({
					'width': plugin.width()-2,
					'height': plugin.height()-2,
					'left': plugin.offset().left,
					'top': plugin.offset().top
				}).show().fadeOut(1000);
			}
		},

		_morePluginOptions: function (plugin, values) {
			// save reference to this class
			var classy = this;
			// how do we figure out all the placeholder names
			var array = [];
			$('.cms_placeholder-bar').each(function (index, item) {
				array.push($(item).attr('class').split('::')[5]);
			});

			// so whats the current placeholder=
			var current = plugin.attr('class').split('::')[5];

			// lets remove current from array - puke
			var idx = array.indexOf(current);
				array.splice(idx, 1);

			// grab the element
			var more = classy.overlay.find('.cms_placeholder-options_more');
				more.show();

			var list = more.find('ul');

			// we need to stop if the array is empty
			if(array.length) list.html('');

			// loop through the array
			$(array).each(function (index, item) {
				// do some brainfuck
				var text = $('.cms_placeholder-bar[class$="cms_placeholder_slot::' + item + '"]').find('.cms_placeholder-title').text();
				list.append($('<li><a href="">' +text + '</a></li>').data({
					'slot': item,
					'plugin_id': values.plugin_id
				}));
			});

			// now we need to bind events to the elements
			list.find('a').bind('click', function (e) {
				e.preventDefault();
				// save slot var
				var slot = $(this).parent().data('slot');
				// now lets do the ajax request
				$.ajax({
					'type': 'POST',
					'url': classy.options.urls.cms_page_move_plugin,
					'data': { 'placeholder': slot, 'plugin_id': $(this).parent().data('plugin_id') },
					'success': function () {
						refreshPluginPosition(slot);
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			});

			// if request is successfull move the plugin
			function refreshPluginPosition(slot) {
				// lets replace the element
				var els = $('.cms_placeholder[class$="cms_placeholder::' + slot + '"]');
				var length = els.length;

				if(els.length === 0) {
					plugin.insertAfter($('.cms_placeholder-bar[class$="cms_placeholder_slot::' + slot + '"]'));
				} else {
					plugin.insertAfter($(els.toArray()[els.length-1]));
				}

				// show success overlay for a second
				classy.success.css({
					'width': plugin.width()-2,
					'height': plugin.height()-2,
					'left': plugin.offset().left,
					'top': plugin.offset().top
				}).show().fadeOut(1000);

				// we have to assign the new class slot to the moved plugin
				var cls = plugin.attr('class').split('::');
					cls.pop();
					cls.push(slot);
					cls = cls.join('::');
				plugin.attr('class', cls);
			}
		},
		
		_showOverlay: function (holder) {
			// lets place the overlay
			this.overlay.css({
				'width': holder.width()-2,
				'height': holder.height()-2,
				'left': holder.offset().left,
				'top': holder.offset().top
			}).show();
		},
		
		_hideOverlay: function () {
			// hide overlay again
			this.overlay.hide();
			// also hide submenu
			this.overlay.find('.cms_placeholder-options_more').hide();
		},
		
		_showPluginList: function (el) {
			// save reference to this class
			var classy = this;
			var list = el.parent().find('.cms_placeholder-subnav');
				list.show();
			
			// add event to body to hide the list needs a timout for late trigger
			setTimeout(function () {
				$(window).bind('click', function () {
					classy._hidePluginList.call(classy, el);
				});
			}, 100);
			
			el.addClass('cms_toolbar-btn-active').data('collapsed', false);
		},
		
		_hidePluginList: function (el) {
			var list = el.parent().find('.cms_placeholder-subnav');
				list.hide();
			
			// remove the body event
			$(window).unbind('click');
			
			el.removeClass('cms_toolbar-btn-active').data('collapsed', true);
		},
		
		toggleFrame: function () {
			(this.frame.data('collapsed')) ? this._showFrame() : this._hideFrame();
		},
		
		_showFrame: function () {
			var classy = this;
			// show frame
			this.frame.fadeIn();
			// change data information
			this.frame.data('collapsed', false);
			// set dynamic frame position
			var offset = 43;
			var pos = $(window).scrollTop();
			// frame should always have space on top
			this.frame.css('top', pos+offset);
			// make sure that toolbar is visible
			if(this.toolbar.data('collapsed')) CMS.Toolbar._showToolbar();
			// listen to toolbar events
			this.toolbar.bind('cms.toolbar.show cms.toolbar.hide', function (e) {
				(e.handleObj.namespace === 'show.toolbar') ? classy.frame.css('top', pos+offset) : classy.frame.css('top', pos);
			});
		},
		
		_hideFrame: function () {
			// hide frame
			this.frame.fadeOut();
			// change data information
			this.frame.data('collapsed', true);
			// there needs to be a function to unbind the loaded content and reset to loader
			this.frame.find('.cms_placeholder-content_inner')
				.addClass('cms_placeholder-content_loader')
				.html('');
			// remove toolbar events
			this.toolbar.unbind('cms.toolbar.show cms.toolbar.hide');
		},

		toggleDim: function () {
			(this.dim.data('dimmed')) ? this._hideDim() : this._showDim();
		},
		
		_showDim: function () {
			var classy = this;
			// clear timer when initiated within resize event
			clearTimeout(this.timer);
			// attach resize event to window
			$(window).bind('resize', function () {
				classy.dim.css({
					'width': $(window).width(),
					'height': $(window).height()
				});
				classy.frame.css('width', $(window).width());
				// adjust after resizing
				classy.timer = setTimeout(function () {
					classy.dim.css({
						'width': $(window).width(),
						'height': $(document).height()
					});
					classy.frame.css('width', $(window).width());
				}, 100);
			});
			// init dim resize
			$(window).resize();
			// change data information
			this.dim.data('dimmed', true);
			// show dim
			this.dim.stop().fadeIn();
			// add event to dim to hide
			this.dim.bind('click', function () {
				classy.toggleFrame.call(classy);
				classy.toggleDim.call(classy);
			});
		},
		
		_hideDim: function () {
			// unbind resize event
			$(window).unbind('resize');
			// change data information
			this.dim.data('dimmed', false);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
			// remove dim event
			this.dim.unbind('click');
		}
		
	});
});