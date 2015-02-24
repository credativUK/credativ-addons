openerp.web_view_log = function(instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    /* Extend the Sidebar to add View Log link in the 'More' menu */
    instance.web.Sidebar = instance.web.Sidebar.extend({
        start: function() {
            var self = this;
            this._super(this);
                self.add_items('other', [
                    {   label: _t('View Log'),
                        callback: self.on_click_view_log,
                        classname: 'oe_view_log' },
                ]);
        },
        on_click_view_log: function(item) {
            var self = this;
            var view = this.getParent();
            var ids = view.get_selected_ids();
            if (ids.length === 1) {
                this.dataset.call('perm_read', [ids]).done(function(result) {
                    var dialog = new instance.web.Dialog(this, {
                        title: _.str.sprintf(_t("View Log (%s)"), self.dataset.model),
                        width: 400
                    }, QWeb.render('ViewManagerDebugViewLog', {
                        perm : result[0],
                        format : instance.web.format_value
                    })).open();
                });
            }
        }
    });
};

