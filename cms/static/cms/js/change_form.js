(function($) {
	$(document).ready(function() {
		var new_slug = true;
		if($('#id_slug')[0].value){
			new_slug = false;
		}
		
		if(window.location.href.split("history").length == 1 && window.location.href.split("recover").length==1){
			$.each(["template"], function(i, label){
				var select = $('select#id_'+label);
				select.change(function() {
					var changed = $("#id_slug")[0]._changed;

					if($("#id_title")[0]._changed){
						changed = true;
					}
					var pub = $("#id_published");
					if (pub.length){
						if(pub[0]._changed){
							changed = true;
						}
					}
					if($('iframe').length){
						changed = true;
					}
					var answer = '';
					var array = window.location.href.split('?');
					var query = $.query.set(label, this.options[this.selectedIndex].value).toString();
					if (changed) {
						var question = gettext("Are you sure you want to change the %(field_name)s without saving the page first?");
						answer = confirm(interpolate(question, {
							field_name: select.prev().text().slice(0, -1)
						}, true));
					}else{
						answer = true;
					}

					if (answer) {
						window.location.href = array[0]+query;
					}
				
				});
			});
		}

		$("#id_title").focus();
		
		var template = $.query.get('template');
		if(template) {
			$('#id_template').find("option").each(function() {
				this.selected = template == this.value;
			});
		}
		$("#id_slug").change(function() { this._changed = true; });
		$('#id_title').change(function() {this._changed = true; });
		$('#id_published').change(function() {this._changed = true; });
		$("#id_title").keyup(function() {
			var e = $("#id_slug")[0];
			if (!e._changed && new_slug) {
				var value = this.value;
				if (window.UNIHANDECODER){
					value = UNIHANDECODER.decode(value);
				}
				e.value = URLify(value, 64);
			}
		});
		// saveform event handler
		$('#page_form').submit(function(){
			if($('iframe').length){
				var question = gettext("Not all plugins are saved. Are you sure you want to save the page?\nYou may lose your changes. To prevent that, press 'Cancel' and save every unsaved plugin first.");
				var answer = confirm(question, true);
				if (answer){
					$('iframe').contents().find('#content-main>form').each(function(){
						try{
							this.submit();
						} catch(err) { 
							return false;
						}
					});
					return true;
				}else{
					return false;
				}
			}
		});
		// inline group loader
		$('h2 a').click(function() {
			// reqest content - do it this way, so we can save some time which
			// this operation may need
			var parent = $(this).parent().parent();
			var pathHolder = $(parent).find('div.load');
			if (pathHolder.length) {
				var url = pathHolder.text();
				// load just once
				pathHolder.remove();
				$(parent).find('div.loading').load(url);
			}
			return false;	
		});	
			
	});

	// global functions
	trigger_lang_button = function(e, url) {
		// also make sure that we will display the confirm dialog
		// in case users switch tabs while editing plugins
		var changed = false;
		var question = '';
		var answer = '';

		if($("#id_slug")[0]._changed){
			changed = true;
		}

		if($("#id_title")[0]._changed){
			changed = true;
		}

		var pub = $("#id_published");
		if (pub.length){
			if(pub[0]._changed){
				changed = true;
			}
		}

		if($('iframe').length){
			changed = true;
		}

		if (changed) {
			question = gettext("Are you sure you want to change tabs without saving the page first?");
			answer = confirm(question);
		}else{
			answer = true;
		}

		if (!answer) {
			return false;
		} else {   
			window.location = url;
		}
	}
})(jQuery);
