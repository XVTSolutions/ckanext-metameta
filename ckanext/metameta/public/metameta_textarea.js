this.ckan.module('meta_save', function ($, _) {
  return {

    initialize: function () {
        this.el.on('click', this._onClick);    
    },

    _onClick: function(event) {
        $('textarea.metameta').each(function(){
            var str = $(this).val().replace(/[\n\r]/g, '');//remove carriage return
            $(this).val(str);
        });
    }
  };
});

