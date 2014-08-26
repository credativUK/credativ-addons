openerp.web_listfield_limit = function(openerp) {
    var _t = openerp.web._t,
       _lt = openerp.web._lt;

openerp.web.form.FieldOne2Many = openerp.web.form.FieldOne2Many.extend({
    load_views: function() {
        var self = this;

        var modes = this.node.attrs.mode;
        modes = !!modes ? modes.split(",") : ["tree"];
        var views = [];
        _.each(modes, function(mode) {
            var view = {
                view_id: false,
                view_type: mode == "tree" ? "list" : mode,
                options: { sidebar : false }
            };
            if (self.field.views && self.field.views[mode]) {
                view.embedded_view = self.field.views[mode];
            }
            if(view.view_type === "list") {
                if (self.modifiers.default_limit) {
                    view.options.limit = self.modifiers.default_limit
                }
                view.options.selectable = self.multi_selection;
                if (self.is_readonly()) {
                    view.options.addable = null;
                    view.options.deletable = null;
                    view.options.isClarkGable = true;
                } else {
                    view.options.deletable = true;
                    view.options.selectable = true;
                    view.options.isClarkGable = true;
                }
            } else if (view.view_type === "form") {
                if (self.is_readonly()) {
                    view.view_type = 'page';
                }
                view.options.not_interactible_on_create = true;
            }
            views.push(view);
        });
        this.views = views;

        this.viewmanager = new openerp.web.ViewManager(this, this.dataset, views, {});
        this.viewmanager.template = 'One2Many.viewmanager';
        this.viewmanager.registry = openerp.web.views.extend({
            list: 'openerp.web.form.One2ManyListView',
            form: 'openerp.web.form.One2ManyFormView',
            page: 'openerp.web.PageView'
        });
        if (this.node.attrs.widget == 'o2m_editable' && !this.is_readonly()) {
            this.viewmanager.registry.map.list = 'openerp.web.form.One2ManyListViewEditable'
        }
        var once = $.Deferred().then(function() {
            self.init_form_last_update.resolve();
        });
        var def = $.Deferred().then(function() {
            self.initial_is_loaded.resolve();
        });
        this.viewmanager.on_controller_inited.add_last(function(view_type, controller) {
            if (view_type == "list") {
                controller.o2m = self;
                if (self.is_readonly())
                    controller.set_editable(false);
            } else if (view_type == "form" || view_type == 'page') {
                if (view_type == 'page' || self.is_readonly()) {
                    $(".oe_form_buttons", controller.$element).children().remove();
                }
                controller.on_record_loaded.add_last(function() {
                    once.resolve();
                });
                controller.on_pager_action.add_first(function() {
                    self.save_any_view();
                });
            } else if (view_type == "graph") {
                self.reload_current_view();
            }
            def.resolve();
        });
        this.viewmanager.on_mode_switch.add_first(function(n_mode, b, c, d, e) {
            $.when(self.save_any_view()).then(function() {
                if(n_mode === "list")
                    $.async_when().then(function() {self.reload_current_view();});
            });
        });
        this.is_setted.then(function() {
            $.async_when().then(function () {
                self.viewmanager.appendTo(self.$element);
            });
        });
        return def;
    }
});

};