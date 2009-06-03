#!/usr/bin/env python
# -*- coding: UTF8 -*-

# Copyright (C) 2009 Daniel Paurat
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# The author may be contacted via:
# email: don.gecko@gmail.com


# imports
try:
    import gtk
    from pysqlite2 import dbapi2 as sqlite
    import gtk.glade
except:
    print "Python bindings for glade, gtk or sqlite are missing"
    print "On a Debian based system (e.g. Ubuntu) try:"
    print "sudo apt-get install python-glade2 python-gtk2 python-pysqlite2"
    exit(1)

import os
from glob import glob
from time import localtime

from SimpleGladeApp import SimpleGladeApp
from SimpleGladeApp import bindtextdomain



app_name = "taskMonkee"
app_version = "0.1"
glade_dir = ""
locale_dir = ""

bindtextdomain(app_name, locale_dir)

# The main window.
# Keeps track of task, which should be done today.
# This includes late tasks and the ones not having a due date.
class Mainwindow(SimpleGladeApp):

    # Create the window and connect to the database
    def __init__(self, path="gui.glade", root="MainWindow", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        # set the application icon
        self.get_widget('MainWindow').set_icon_from_file("monkey.gif")
        # connect to the database
        userhomepath = os.environ['HOME'] + '/'
        filename = userhomepath + '.taskmonkeeDB.sqlite'
        if(len(glob(filename)) == 0):
            self.con = sqlite.connect(filename)
            self.con.execute('CREATE TABLE Tasks(completed BOOLEAN, title STRING, details STRING, duedate INTEGER, no_duedate_flag BOOLEAN)')
            self.con.commit()
        else:
            self.con = sqlite.connect(filename)
        
        # set up the treeview in GUI
        col = gtk.TreeViewColumn("Late", gtk.CellRendererText(), text=1)
        col.set_sort_column_id(1)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Title", gtk.CellRendererText(), text=2)
        col.set_sort_column_id(2)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Completed", gtk.CellRendererText(), text=3)
        col.set_sort_column_id(3)
        self.treeview.append_column(col)
        
        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)
        
        # display todays tasks
        self.get_tasks_and_display()
        
        # grey out the delete button 
        self.get_widget('delete_button').set_sensitive(False)
        #connect to the selection handler (could not do this by glade... so i connect manually)
        selection = self.treeview.get_selection()
        selection.connect('changed', self.on_tree_selection_changed)



    # if some task is selected make the delete button accessable, else not
    def on_tree_selection_changed(self, selection):
        model, select = selection.get_selected()
        #If there is a selection then enable these
        self.get_widget('delete_button').set_sensitive((select != None))



    # This is the 'unselect' method
    def on_treeview_button_press_event(self, widget, event):
        #Get the path at the specific mouse position
        path = widget.get_path_at_pos(int(event.x), int(event.y))
        if (path == None):
            #If we didn't get a path then we don't want anything to be selected.
            selection = widget.get_selection()
            selection.unselect_all()
        


    # Selects todays tasks from the database and refreshes the treeview
    def get_tasks_and_display(self):
        # store contains the data, displayed in the GUI
        # stored are rowid, completed, title and if task is late
        self.store = gtk.ListStore(int, str, str, str)
        self.treeview.set_model(self.store)
        
        # convert time-tuple to an int e.g: (2009, 05, 17) -> 20090517
        tmpTime = localtime()[0:3]
        today = tmpTime[0]*10000 + (tmpTime[1])*100  + tmpTime[2]
        
        # get the tasks from the database
        for task in self.con.execute("SELECT rowid, completed, title, duedate FROM Tasks WHERE (duedate <= %d OR no_duedate_flag == 'True')" %today).fetchall():
            # if task is already late and not completed yet...mark it!
            if (task[3] < today) and (task[1] == 'False'):
                late = '☠' # this is a skull in unicode
            else:
                late = ' '
            # if task is completed, check mark it
            if task[1] == 'True':
                completed = '✔' # this is a check-mark sign in unicode
            else:
                completed = ' '
            
            self.store.append((task[0], late, task[2], completed))



    # add a task to the database and refresh the treeview
    def add_task(self, completed, title, details, duedate, no_duedate_flag):
        self.con.execute("INSERT INTO Tasks(completed, title, details,  duedate, no_duedate_flag) VALUES ('%s', '%s', '%s', '%d', '%s')" %(completed, title, details, duedate, no_duedate_flag) )
        self.con.commit()
        self.get_tasks_and_display()



    # edit a task in the database and refresh the treeview
    def edit_task(self, id, completed, title, details, duedate, no_duedate_flag):
        update_string = "UPDATE Tasks SET completed = '%s', title = '%s', details = '%s',  duedate = %d, no_duedate_flag = '%s' WHERE rowid = %d" %(completed, title, details, duedate, no_duedate_flag, id)
        self.con.execute(update_string)
        self.con.commit()
        self.get_tasks_and_display()



    # if you close the program, disconnect the database and exit
    def on_MainWindow_destroy(self, widget, *args):
        self.con.close()
        exit(0)



    # on double clicking an entry open the Edit dialog
    def on_treeview_row_activated(self, widget, *args):
        iter = self.treeview.get_selection().get_selected()[1]
        id = self.store.get_value(iter, 0)
        Editwindow(self, self, id)



    # open an empty Edit dialog if Add button is clicked
    def on_add_button_clicked(self, widget, *args):
        Editwindow(self, self, -1)



    # on Delete button clicked, get the selected item,
    # delete it from the database and refresh the treeview
    def on_delete_button_clicked(self, widget, *args):
        iter = self.treeview.get_selection().get_selected()[1]
        if iter != None:
            id = self.store.get_value(iter, 0)
            self.con.execute("DELETE FROM Tasks WHERE rowid = %d" %id)
            self.con.commit()
            self.get_tasks_and_display()



    # pop up the upcoming tasks
    def on_upcoming_button_clicked(self, widget, *args):
        Upcomingwindow(self)




# Edit dialog. pops up, if an entry is double clicked.
# Editwindow has two modes, add and edit
class Editwindow(SimpleGladeApp):

    # Create the Window and fill the entries, if in edit mode
    def __init__(self, parent, mainwindow, id, path="gui.glade", root="EditWindow", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        # set the application icon
        self.get_widget('EditWindow').set_icon_from_file("monkey.gif")
        self.parent = parent
        self.mainwindow = mainwindow
        self.id = id
        
        # if in edit mode, get the data of the task and display it
        if self.id >= 0:
            # get title
            title = self.mainwindow.con.execute("SELECT title FROM Tasks WHERE rowid == %d" %self.id).fetchone()[0]
            self.get_widget('TitleField').set_text(title)
            # get details
            details = self.mainwindow.con.execute("SELECT details FROM Tasks WHERE rowid == %d" %self.id).fetchone()[0]
            detailsBuffer = self.get_widget('DetailField').get_buffer()
            detailsBuffer.set_text(details)
            # get due date
            date = self.mainwindow.con.execute("SELECT duedate FROM Tasks WHERE rowid == %d" %self.id).fetchone()[0]
            year = int(str(date)[0:4])
            month = int(str(date)[4:6])
            day = int(str(date)[6:8])
            # set the calendar in the GUI
            self.calendar1.select_month(month-1, year)
            self.calendar1.select_day(day)
            # get completed flag and set the checkbox
            completed = self.mainwindow.con.execute("SELECT completed FROM Tasks WHERE rowid == %d" %self.id).fetchone()[0]
            self.completed_checkbutton.set_active(completed == 'True')
            # get no_duedate flag and set the checkbox
            no_duedate = self.mainwindow.con.execute("SELECT no_duedate_flag FROM Tasks WHERE rowid == %d" %self.id).fetchone()[0]
            self.no_duedate_checkbutton.set_active(no_duedate == 'True')
            # else you are in add mode and want to change the window title
        else:
            self.get_widget('EditWindow').set_title('Add Task')


    # On OK button clicked, check if in add, or edit mode and add or edit the task
    def on_OK_button_clicked(self, widget, *args):
        # if add mode
        if(self.id == -1):
            # get title
            title = self.get_widget('TitleField').get_text()
            # get details
            detailsBuffer = self.get_widget('DetailField').get_buffer()
            start = detailsBuffer.get_start_iter()
            end = detailsBuffer.get_end_iter()
            details = detailsBuffer.get_text(start,end)
            # get due date
            date = self.calendar1.get_date()
            duedate = date[0]*10000 + (date[1]+1)*100  + date[2]
            # dont add empty title
            if title != '':
                # add the task (add_task() adds to the database and refreshes the treeview)
                self.mainwindow.add_task(self.completed_checkbutton.get_active(), title, details, duedate, self.no_duedate_checkbutton.get_active())
        # if in edit mode
        else:
            # get title
            title = self.get_widget('TitleField').get_text()
            # get details
            detailsBuffer = self.get_widget('DetailField').get_buffer()
            start = detailsBuffer.get_start_iter()
            end = detailsBuffer.get_end_iter()
            details = detailsBuffer.get_text(start,end)
            # get duedate
            date = self.calendar1.get_date()
            duedate = date[0]*10000 + (date[1]+1)*100  + date[2]
            # get checkboxes
            completed = self.completed_checkbutton.get_active()
            no_duedate_flag = self.no_duedate_checkbutton.get_active()
            # dont edit, if the title is empty now
            if title != '':
                # edit the task (edit_task() edits the database and refreshes the treeview)
                self.mainwindow.edit_task(self.id, self.completed_checkbutton.get_active(), title, details, duedate, self.no_duedate_checkbutton.get_active())
                # refresh the treeview (in case the parent is the upcoming window)
                self.parent.get_tasks_and_display()
        # close the window
        self.EditWindow.hide()




# display tasks, which are jet to come.
# Tasks, which have a duedate in the future,
# but the 'No completion date' checked are not shown here.
class Upcomingwindow(SimpleGladeApp):

    # Create the window and display the upcoming tasks
    def __init__(self, parent, path="gui.glade", root="UpcomingWindow", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        # set the application icon
        self.get_widget('UpcomingWindow').set_icon_from_file("monkey.gif")
        self.parent = parent
        
        # set up the treeview in GUI
        col = gtk.TreeViewColumn("Completed", gtk.CellRendererText(), text=1)
        col.set_sort_column_id(1)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Title", gtk.CellRendererText(), text=2)
        col.set_sort_column_id(2)
        self.treeview.append_column(col)
        col = gtk.TreeViewColumn("Date", gtk.CellRendererText(), text=3)
        col.set_sort_column_id(4)
        self.treeview.append_column(col)
        
        # display upcoming tasks
        self.get_tasks_and_display()
        
        # grey out the delete button 
        self.get_widget('delete_button').set_sensitive(False)
        #connect to the selection handler (could not do this by glade... so i connect manually)
        selection = self.treeview.get_selection()
        selection.connect('changed', self.on_tree_selection_changed)


    # find all future tasks and display them
    def get_tasks_and_display(self):
        # store contains the data, displayed in the GUI
        # stored are rowid, completed, title date as string and date as integer (for sorting)
        self.store = gtk.ListStore(int, str, str, str, int)
        self.treeview.set_model(self.store)
        
        # convert time-tuple to an int e.g: (2009, 05, 17) -> 20090517
        tmpTime = localtime()[0:3]
        today = tmpTime[0]*10000 + (tmpTime[1])*100  + tmpTime[2]
        
        # select all upcomming tasks which have a concrete due date in the future
        for task in self.parent.con.execute("SELECT rowid, completed, title, duedate FROM Tasks WHERE (duedate > %d AND no_duedate_flag == 'False')" %today).fetchall():
            # build a nice string from the due date e.g: 20090517 -> 17.05.2009
            year = str(task[3])[0:4]
            month = str(task[3])[4:6]
            day = str(task[3])[6:8]
            date = day + "." + month + "." + year
            # set the check mark symbol, if completed
            if task[1] == 'False':
                completed = ' '
            else:
                 completed = '✔'
            # add task to the be displayed
            self.store.append((task[0], completed, task[2], date, task[3]))
        pass



    # if an entry is double clicked, open it in the Edit dialog
    def on_treeview_row_activated(self, widget, *args):
        iter = self.treeview.get_selection().get_selected()[1]
        id = self.store.get_value(iter, 0)
        Editwindow(self, self.parent, id)



    # deletes selected task from the database and refreshes the treeview
    def on_delete_button_clicked(self, widget, *args):
        iter = self.treeview.get_selection().get_selected()[1]
        if iter != None:
            id = self.store.get_value(iter, 0)
            self.parent.con.execute("DELETE FROM Tasks WHERE rowid = %d" %id)
            self.parent.con.commit()
            self.get_tasks_and_display()



    # hide window
    def on_OK_button_clicked(self, widget, *args):
        self.UpcomingWindow.hide()



    # if some task is selected make the delete button accessable, else not
    def on_tree_selection_changed(self, selection):
        model, select = selection.get_selected()
        #If there is a selection then enable these
        self.get_widget('delete_button').set_sensitive((select != None))



    # This is the 'unselect' method
    def on_treeview_button_press_event(self, widget, event):
        #Get the path at the specific mouse position
        path = widget.get_path_at_pos(int(event.x), int(event.y))
        if (path == None):
            #If we didn't get a path then we don't want anything to be selected.
            selection = widget.get_selection()
            selection.unselect_all()


# Start everything up
def main():
    main_window = Mainwindow()
    main_window.run()

if __name__ == "__main__":
    main()
    