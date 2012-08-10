openerp.web_treeviewlinks = function(openerp) {
    var _t = openerp.web._t,
       _lt = openerp.web._lt;
    var QWeb = openerp.web.qweb;

openerp.web.ListView.List = openerp.web.ListView.List.extend({
    render: function () {
        var self = this;
        if (this.$current) {
            this.$current.remove();
        }
        this.$current = this.$_element.clone(true);
        this.$current.empty().append(
            QWeb.render('ListView.rows', _.extend({
                    render_cell: function () {
                        return self.render_cell.apply(self, arguments); }
                }, this)));
        // dodgy hack to get links on things
        this.records.each(function(record){
            var $row = self.$current.find('[data-id=' + record.get('id') + ']');
            for(var i=0, length=self.columns.length; i<length; ++i) {
                if(self.columns[i].type === 'many2one') {
                    var $cell = $row.find((_.str.sprintf('[data-field=%s]', self.columns[i].id)));
                    $cell.html(_.template('<a class="oe_form_uri" href="#" data-model="<%-model%>" data-id="<%-id%>"><%-text%></a>', {
                        text: _.escape(openerp.web.format_value(record.get(self.columns[i].id), self.columns[i], '')),
                        model: self.columns[i].relation,
                        id: record.get(self.columns[i].id)[0]
                    }));
                    $cell.find('a')
                        .unbind('click')
                        .click(function () {
                            var cell = $(this);
                            self.group.view.do_action({
                                type: 'ir.actions.act_window',
                                res_model: cell.attr('data-model'),
                                res_id: parseInt(cell.attr('data-id')),
                                views: [[false, 'page'], [false, 'form']],
                                target: 'current'
                            });
                            return false;
                        });
                }
            }
        });
        this.pad_table_to(5);
    }
});

openerp.web.form.One2ManyList = openerp.web.ListView.List.extend({
    render: function () {
        var self = this;
        if (this.$current) {
            this.$current.remove();
        }
        this.$current = this.$_element.clone(true);
        this.$current.empty().append(
            QWeb.render('ListView.rows', _.extend({
                    render_cell: function () {
                        return self.render_cell.apply(self, arguments); }
                }, this)));
        // dodgy hack to get links on things
        this.records.each(function(record){
            var $row = self.$current.find('[data-id=' + record.get('id') + ']');
            for(var i=0, length=self.columns.length; i<length; ++i) {
                if(self.columns[i].type === 'many2one') {
                    var $cell = $row.find((_.str.sprintf('[data-field=%s]', self.columns[i].id)));
                    $cell.html(_.template('<a class="oe_form_uri" href="#" data-model="<%-model%>" data-id="<%-id%>"><%-text%></a>', {
                        text: _.escape(openerp.web.format_value(record.get(self.columns[i].id), self.columns[i], '')),
                        model: self.columns[i].relation,
                        id: record.get(self.columns[i].id)[0]
                    }));
                    $cell.find('a')
                        .unbind('click')
                        .click(function () {
                            var cell = $(this);
                            self.group.view.do_action({
                                type: 'ir.actions.act_window',
                                res_model: cell.attr('data-model'),
                                res_id: parseInt(cell.attr('data-id')),
                                views: [[false, 'page'], [false, 'form']],
                                target: 'current'
                            });
                            return false;
                        });
                }
            }
        });
        this.pad_table_to(5);
    }
});

};
