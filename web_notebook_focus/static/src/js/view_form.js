openerp.web_notebook_focus = function(openerp) {
    var _t = openerp.web._t,
       _lt = openerp.web._lt;

openerp.web.form.WidgetNotebook = openerp.web.form.WidgetNotebook.extend({
    start: function() {
        var self = this;
        this._super.apply(this, arguments);
        this.$element.find('> ul > li').each(function (index, tab_li) {
            var page = self.pages[index],
                id = _.uniqueId(self.element_name + '-');
            page.element_id = id;
            $(tab_li).find('a').attr('href', '#' + id);
        });
        this.$element.find('> div').each(function (index, page) {
            page.id = self.pages[index].element_id;
        });
        this.$element.tabs();
        this.view.on_button_new.add_first(this.do_select_first_visible_tab);
        this.view.on_form_changed.add_last(this.do_select_focued_tab);
        if (openerp.connection.debug) {
            this.do_attach_tooltip(this, this.$element.find('ul:first'), {
                gravity: 's'
            });
        }
    },
    do_select_focued_tab: function() {
        var compute_domain = openerp.web.form.compute_domain;
        for (var i = 0; i < this.pages.length; i++) {
            var page = this.pages[i];
            if (page.modifiers.default_focus) {
                var focus = compute_domain(page.modifiers.default_focus, this.view.fields);
                if (focus === true) {
                    this.$element.tabs('select', page.index);
                    break;
                }
            }
        }
    }
});

};
