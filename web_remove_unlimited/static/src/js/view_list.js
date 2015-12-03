openerp.web_remove_unlimited = function(instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.web.ListView.include({
        /**
        * Called after loading the list view's description, sets up such things
        * as the view table's columns, renders the table itself and hooks up the
        * various table-level and row-level DOM events (action buttons, deletion
        * buttons, selection of records, [New] button, selection of a given
        * record, ...)
        *
        * Sets up the following:
        *
        * * Processes arch and fields to generate a complete field descriptor for each field
        * * Create the table itself and allocate visible columns
        * * Hook in the top-level (header) [New|Add] and [Delete] button
        * * Sets up showing/hiding the top-level [Delete] button based on records being selected or not
        * * Sets up event handlers for action buttons and per-row deletion button
        * * Hooks global callback for clicking on a row
        * * Sets up its sidebar, if any
        *
        * @param {Object} data wrapped fields_view_get result
        * @param {Object} data.fields_view fields_view_get result (processed)
        * @param {Object} data.fields_view.fields mapping of fields for the current model
        * @param {Object} data.fields_view.arch current list view descriptor
        * @param {Boolean} grouped Is the list view grouped
        */
        load_list: function(data) {
            var self = this;
            this.fields_view = data;
            this.name = "" + this.fields_view.arch.attrs.string;

            if (this.fields_view.arch.attrs.colors) {
                this.colors = _(this.fields_view.arch.attrs.colors.split(';')).chain()
                    .compact()
                    .map(function(color_pair) {
                        var pair = color_pair.split(':'),
                            color = pair[0],
                            expr = pair[1];
                        return [color, py.parse(py.tokenize(expr)), expr];
                    }).value();
            }

            if (this.fields_view.arch.attrs.fonts) {
                this.fonts = _(this.fields_view.arch.attrs.fonts.split(';')).chain().compact()
                    .map(function(font_pair) {
                        var pair = font_pair.split(':'),
                            font = pair[0],
                            expr = pair[1];
                        return [font, py.parse(py.tokenize(expr)), expr];
                    }).value();
            }

            this.setup_columns(this.fields_view.fields, this.grouped);

            this.$el.html(QWeb.render(this._template, this));
            this.$el.addClass(this.fields_view.arch.attrs['class']);

            // Head hook
            // Selecting records
            this.$el.find('.oe_list_record_selector').click(function(){
                self.$el.find('.oe_list_record_selector input').prop('checked',
                    self.$el.find('.oe_list_record_selector').prop('checked')  || false);
                var selection = self.groups.get_selection();
                $(self.groups).trigger(
                    'selected', [selection.ids, selection.records]);
            });

            // Add button
            if (!this.$buttons) {
                this.$buttons = $(QWeb.render("ListView.buttons", {'widget':self}));
                if (this.options.$buttons) {
                    this.$buttons.appendTo(this.options.$buttons);
                } else {
                    this.$el.find('.oe_list_buttons').replaceWith(this.$buttons);
                }
                this.$buttons.find('.oe_list_add')
                        .click(this.proxy('do_add_record'))
                        .prop('disabled', this.grouped);
            }

            // Pager
            if (!this.$pager) {
                this.$pager = $(QWeb.render("ListView.pager", {'widget':self}));
                if (this.options.$buttons) {
                    this.$pager.appendTo(this.options.$pager);
                } else {
                    this.$el.find('.oe_list_pager').replaceWith(this.$pager);
                }

                this.$pager
                    .on('click', 'a[data-pager-action]', function () {
                        var $this = $(this);
                        var max_page = Math.floor(self.dataset.size() / self.limit());
                        switch ($this.data('pager-action')) {
                            case 'first':
                                self.page = 0; break;
                            case 'last':
                                self.page = max_page - 1;
                                break;
                            case 'next':
                                self.page += 1; break;
                            case 'previous':
                                self.page -= 1; break;
                        }
                        if (self.page < 0) {
                            self.page = max_page;
                        } else if (self.page > max_page) {
                            self.page = 0;
                        }
                        self.reload_content();
                    }).find('.oe_list_pager_state')
                        .click(function (e) {
                            e.stopPropagation();
                            var $this = $(this);

                            var $select = $('<select>')
                                .appendTo($this.empty())
                                .click(function (e) {e.stopPropagation();})
                                .append('<option value="80">80</option>' +
                                        '<option value="200">200</option>' +
                                        '<option value="500">500</option>' +
                                        '<option value="2000">2000</option>')
                                .change(function () {
                                    var val = parseInt($select.val(), 10);
                                    self._limit = (isNaN(val) ? null : val);
                                    self.page = 0;
                                    self.reload_content();
                                }).blur(function() {
                                    $(this).trigger('change');
                                })
                                .val(self._limit || 'NaN');
                        });
            }

            // Sidebar
            if (!this.sidebar && this.options.$sidebar) {
                this.sidebar = new instance.web.Sidebar(this);
                this.sidebar.appendTo(this.options.$sidebar);
                this.sidebar.add_items('other', _.compact([
                    { label: _t("Export"), callback: this.on_sidebar_export },
                    self.is_action_enabled('delete') && { label: _t('Delete'), callback: this.do_delete_selected }
                ]));
                this.sidebar.add_toolbar(this.fields_view.toolbar);
                this.sidebar.$el.hide();
            }
            //Sort
            if(this.dataset._sort.length){
                if(this.dataset._sort[0].indexOf('-') == -1){
                    this.$el.find('th[data-id=' + this.dataset._sort[0] + ']').addClass("sortdown");
                }else {
                    this.$el.find('th[data-id=' + this.dataset._sort[0].split('-')[1] + ']').addClass("sortup");
                }
            }
            this.trigger('list_view_loaded', data, this.grouped);
        }
    });
};
