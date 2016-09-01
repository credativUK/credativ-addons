openerp.web_action_permissions = function(instance) {
    instance.web.View.include({
        is_action_enabled: function(action) {
            var res = this._super.apply(this, arguments);
            /* Never permit anything explicitly disallowed by core functionality. */
            if (!res) return res;
            var attrs_extra = this.fields_view.__action_permissions_extra || Object();
            return (action in attrs_extra) ? JSON.parse(attrs_extra[action]) : true;
        }
    });
};
