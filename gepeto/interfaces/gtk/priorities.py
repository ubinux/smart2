#!/usr/bin/python
from gepeto import *
import gobject, gtk

class GtkPriorities(object):

    def __init__(self):

        self._window = gtk.Window()
        self._window.set_title("Priorities")
        self._window.set_modal(True)
        self._window.set_position(gtk.WIN_POS_CENTER)
        self._window.set_geometry_hints(min_width=600, min_height=400)
        def delete(widget, event):
            gtk.main_quit()
            return True
        self._window.connect("delete-event", delete)

        vbox = gtk.VBox()
        vbox.set_border_width(10)
        vbox.set_spacing(10)
        vbox.show()
        self._window.add(vbox)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.show()
        vbox.add(sw)

        self._treemodel = gtk.ListStore(gobject.TYPE_STRING,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING)
        self._treeview = gtk.TreeView(self._treemodel)
        self._treeview.set_rules_hint(True)
        self._treeview.show()
        sw.add(self._treeview)

        self._namerenderer = gtk.CellRendererText()
        self._namerenderer.set_property("xpad", 3)
        self._namerenderer.set_property("editable", True)
        self._namerenderer.connect("edited", self.rowEdited)
        self._treeview.insert_column_with_attributes(-1, "Package Name",
                                                     self._namerenderer,
                                                     text=0)

        self._aliasrenderer = gtk.CellRendererText()
        self._aliasrenderer.set_property("xpad", 3)
        self._aliasrenderer.set_property("editable", True)
        self._aliasrenderer.connect("edited", self.rowEdited)
        self._treeview.insert_column_with_attributes(-1, "Channel Alias",
                                                     self._aliasrenderer,
                                                     text=1)

        self._priorityrenderer = gtk.CellRendererText()
        self._priorityrenderer.set_property("xpad", 3)
        self._priorityrenderer.set_property("editable", True)
        self._priorityrenderer.connect("edited", self.rowEdited)
        self._treeview.insert_column_with_attributes(-1, "Priority",
                                                     self._priorityrenderer,
                                                     text=2)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(10)
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.show()
        vbox.pack_start(bbox, expand=False)

        button = gtk.Button(stock="gtk-new")
        button.show()
        button.connect("clicked", lambda x: self.newPriority())
        bbox.pack_start(button)

        button = gtk.Button(stock="gtk-delete")
        button.show()
        button.connect("clicked", lambda x: self.delPriority())
        bbox.pack_start(button)

        button = gtk.Button(stock="gtk-close")
        button.show()
        button.connect("clicked", lambda x: gtk.main_quit())
        bbox.pack_start(button)

    def fill(self):
        self._treemodel.clear()
        priorities = sysconf.get("package-priorities", setdefault={})
        prioritieslst = priorities.items()
        prioritieslst.sort()
        for name, pkgpriorities in prioritieslst:
            aliaslst = pkgpriorities.items()
            aliaslst.sort()
            for alias, priority in aliaslst:
                self._treemodel.append((name, alias or "*", str(priority)))

    def show(self):
        self.fill()
        self._window.show()
        gtk.main()
        self._window.hide()

    def newPriority(self):
        name, alias, priority = PriorityCreator().show()
        if name:
            priorities = sysconf.get("package-priorities", setdefault={})
            if name in priorities:
                if alias not in priorities[name]:
                    priorities[name][alias] = int(priority)
                    self.fill()
                else:
                    iface.error("Name/alias pair already exists!")
            else:
                priorities[name] = {alias: int(priority)}
                self.fill()

    def delPriority(self):
        selection = self._treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            name = model.get_value(iter, 0)
            alias = model.get_value(iter, 1)
            if alias == "*":
                alias = ""
            priorities = sysconf.get("package-priorities", setdefault={})
            del priorities[name][alias]
            if not priorities[name]:
                del priorities[name]
            self.fill()

    def rowEdited(self, cell, row, newtext):
        newtext = newtext.strip()
        if cell is self._namerenderer:
            col = 0
        elif cell is self._aliasrenderer:
            col = 1
            if newtext == "*":
                newtext = ""
        else:
            col = 2
        model = self._treemodel
        iter = model.get_iter_from_string(row)
        oldtext = model.get_value(iter, col)
        if newtext != oldtext:
            priorities = sysconf.get("package-priorities", setdefault={})
            if col == 0:
                alias = model.get_value(iter, 1)
                if alias == "*":
                    alias = ""
                priority = model.get_value(iter, 2)
                if not newtext:
                    pass
                elif newtext in priorities and alias in priorities[newtext]:
                    iface.error("Name/alias pair already exists!")
                else:
                    if newtext not in priorities:
                        priorities[newtext] = {alias: int(priority)}
                    else:
                        priorities[newtext][alias] = int(priority)
                    del priorities[oldtext][alias]
                    if not priorities[oldtext]:
                        del priorities[oldtext]
                    model.set_value(iter, col, newtext)
            elif col == 1:
                name = model.get_value(iter, 0)
                priority = model.get_value(iter, 2)
                if newtext in priorities[name]:
                    iface.error("Name/alias pair already exists!")
                else:
                    priorities[name][newtext] = int(priority)
                    del priorities[name][oldtext]
                    model.set_value(iter, col, newtext or "*")
            elif col == 2:
                if newtext:
                    name = model.get_value(iter, 0)
                    alias = model.get_value(iter, 1)
                    if alias == "*":
                        alias = ""
                    try:
                        priorities[name][alias] = int(newtext)
                    except ValueError:
                        iface.error("Invalid priority!")
                    else:
                        model.set_value(iter, col, newtext)

class PriorityCreator(object):

    def __init__(self):

        self._window = gtk.Window()
        self._window.set_title("New Package Priority")
        self._window.set_modal(True)
        self._window.set_position(gtk.WIN_POS_CENTER)
        #self._window.set_geometry_hints(min_width=600, min_height=400)
        def delete(widget, event):
            gtk.main_quit()
            return True
        self._window.connect("delete-event", delete)

        vbox = gtk.VBox()
        vbox.set_border_width(10)
        vbox.set_spacing(10)
        vbox.show()
        self._window.add(vbox)

        table = gtk.Table()
        table.set_row_spacings(10)
        table.set_col_spacings(10)
        table.show()
        vbox.pack_start(table)
        
        label = gtk.Label("Package Name:")
        label.set_alignment(1.0, 0.5)
        label.show()
        table.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)

        self._name = gtk.Entry()
        self._name.show()
        table.attach(self._name, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.FILL)

        label = gtk.Label("Channel Alias:")
        label.set_alignment(1.0, 0.0)
        label.show()
        table.attach(label, 0, 1, 1, 2, gtk.FILL, gtk.FILL)

        self._alias = gtk.Entry()
        self._alias.set_text("*")
        self._alias.show()
        table.attach(self._alias, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.FILL)

        label = gtk.Label("Priority:")
        label.set_alignment(1.0, 0.0)
        label.show()
        table.attach(label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)

        self._priority = gtk.SpinButton()
        self._priority.set_width_chars(8)
        self._priority.set_increments(1, 10)
        self._priority.set_numeric(True)
        self._priority.set_range(-100000,+100000)
        self._priority.show()
        align = gtk.Alignment(0.0, 0.5)
        align.show()
        align.add(self._priority)
        table.attach(align, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL)

        sep = gtk.HSeparator()
        sep.show()
        vbox.pack_start(sep, expand=False)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(10)
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.show()
        vbox.pack_start(bbox, expand=False)

        button = gtk.Button(stock="gtk-ok")
        button.show()
        def clicked(x):
            self._result = True
            gtk.main_quit()
        button.connect("clicked", clicked)
        bbox.pack_start(button)

        button = gtk.Button(stock="gtk-cancel")
        button.show()
        button.connect("clicked", lambda x: gtk.main_quit())
        bbox.pack_start(button)

    def show(self):

        self._window.show()

        self._result = False
        while True:
            gtk.main()
            if self._result:
                self._result = False
                name = self._name.get_text().strip()
                if not name:
                    iface.error("No name provided!")
                    continue
                alias = self._alias.get_text().strip()
                if alias == "*":
                    alias = ""
                priority = self._priority.get_value()
                break
            name = alias = priority = None
            break

        self._window.hide()

        return name, alias, priority

# vim:ts=4:sw=4:et
