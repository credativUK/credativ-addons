openerp.web_one2many_list_fields = function(instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

instance.web_one2many_list_fields.FieldOne2ManyListFields = instance.web.form.FieldOne2Many.extend({
    load_views: function() {
        var self = this;

        var modes = this.node.attrs.mode;
        modes = !!modes ? modes.split(",") : ["tree"];
        var views = [];
        _.each(modes, function(mode) {
            if (! _.include(["list", "tree", "graph", "kanban"], mode)) {
                throw new Error(_.str.sprintf(_t("View type '%s' is not supported in One2Many."), mode));
            }
            var view = {
                view_id: false,
                view_type: mode == "tree" ? "list" : mode,
                options: {}
            };
            if (self.field.views && self.field.views[mode]) {
                view.embedded_view = self.field.views[mode];
            }
            if(view.view_type === "list") {
                _.extend(view.options, {
                    addable: null,
                    selectable: self.multi_selection,
                    sortable: true,
                    import_enabled: false,
                    deletable: true
                });
                if (self.get("effective_readonly")) {
                    _.extend(view.options, {
                        deletable: null,
                        reorderable: false,
                    });
                }
            } else if (view.view_type === "form") {
                if (self.get("effective_readonly")) {
                    view.view_type = 'form';
                }
                _.extend(view.options, {
                    not_interactible_on_create: true,
                });
            } else if (view.view_type === "kanban") {
                _.extend(view.options, {
                    confirm_on_delete: false,
                });
                if (self.get("effective_readonly")) {
                    _.extend(view.options, {
                        action_buttons: false,
                        quick_creatable: false,
                        creatable: false,
                        read_only_mode: true,
                    });
                }
            }
            views.push(view);
        });
        this.views = views;

        this.viewmanager = new instance.web_one2many_list_fields.One2ManyListFieldsViewManager(this, this.dataset, views, {});
        this.viewmanager.o2m = self;
        var once = $.Deferred().done(function() {
            self.init_form_last_update.resolve();
        });
        var def = $.Deferred().done(function() {
            self.initial_is_loaded.resolve();
        });
        this.viewmanager.on("controller_inited", self, function(view_type, controller) {
            controller.o2m = self;
            if (view_type == "list") {
                if (self.get("effective_readonly")) {
                    controller.on('edit:before', self, function (e) {
                        e.cancel = true;
                    });
                    _(controller.columns).find(function (column) {
                        if (!(column instanceof instance.web.list.Handle)) {
                            return false;
                        }
                        column.modifiers.invisible = true;
                        return true;
                    });
                }
            } else if (view_type === "form") {
                if (self.get("effective_readonly")) {
                    $(".oe_form_buttons", controller.$el).children().remove();
                }
                controller.on("load_record", self, function(){
                     once.resolve();
                 });
                controller.on('pager_action_executed',self,self.save_any_view);
            } else if (view_type == "graph") {
                self.reload_current_view()
            }
            def.resolve();
        });
        this.viewmanager.on("switch_mode", self, function(n_mode, b, c, d, e) {
            $.when(self.save_any_view()).done(function() {
                if (n_mode === "list") {
                    $.async_when().done(function() {
                        self.reload_current_view();
                    });
                }
            });
        });
        $.async_when().done(function () {
            self.viewmanager.appendTo(self.$el);
        });
        return def;
    },
});


instance.web_one2many_list_fields.One2ManyListFieldsViewManager = instance.web.form.One2ManyViewManager.extend({
    template: 'One2Many.viewmanager',
    init: function(parent, dataset, views, flags) {
        this._super(parent, dataset, views, _.extend({}, flags, {$sidebar: false}));
        this.registry = this.registry.extend({
            list: 'instance.web_one2many_list_fields.One2ManyListFieldsView',
        });
    },
});

instance.web_one2many_list_fields.One2ManyListFieldsView = instance.web.form.One2ManyListView.extend({
    _template: 'One2Many.listview',
    init: function (parent, dataset, view_id, options) {
        this._super(parent, dataset, view_id, options);
        this.options.ListType = instance.web_one2many_list_fields.One2ManyListFields;
    },
});

instance.web_one2many_list_fields.One2ManyListFields = instance.web.form.One2ManyList.extend({
    pad_table_to: function (count) {
        this._super(count);

        if (this.view.o2m.get('effective_readonly')) {
            return;
        }

        if (!this.view.is_action_enabled('create')) {
            return;
        }

        var $cell = this.$current.find('td.oe_form_field_one2many_list_row_add');

        var lvf = this.view.getParent().getParent();
        var fv = lvf.getParent();

        _.each(lvf.node.children, function(node) {
            if (node.tag == "button") {
                var elem = $('<button>');
                $cell.append(elem);
                var obj = fv.tags_registry.get_object('button');
                node.attrs.class = "oe_edit_only oe_link"
                var w = new (obj)(fv, node);
                w.replace(elem)
                w.$el.css( "padding-left", "10px" )
            }
        });
    }
});

    instance.web.form.widgets.add('one2many_list_fields', 'instance.web_one2many_list_fields.FieldOne2ManyListFields');

};
