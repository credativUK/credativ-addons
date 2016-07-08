openerp.web_export_permissions = function(instance) {
    var _t = instance.web._t;
    instance.web.ListView.include({
        load_list: function() {
            var res = this._super.apply(this, arguments);
            if (!this.is_action_enabled('export')) {
                var items = this.sidebar.items["other"];
                for (var i in items) {
                    if (items[i].label == "Export") {
                        items.splice(i, 1);
                        this.sidebar.redraw();
                        break;
                    }
                }
            }
            return res;
        }
    });
};
