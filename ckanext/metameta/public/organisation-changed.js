/* Reloads the page when the organisation is changed on the dataset create/edit screen
 */
this.ckan.module('organisation-changed', function ($, _) {
  return {
    currentValue: false,
    options: {
      organizations: $('#field-organizations'),
      currentValue: null
    },
    initialize: function() {
      $.proxyAll(this, /_on/);
      this.options.currentValue = this.options.organizations.val();
      this.options.organizations.on('change', this._onOrganizationChange);
    },
    _onOrganizationChange: function() {
      var value = this.options.organizations.val();
      if (value != this.options.currentValue) {
    	   this.options.organizations.closest('form').submit();
      }
    }
  };
});
