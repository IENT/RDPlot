from PyQt5 import QtWidgets

from os.path import join

import model


def get_top_level_items_from_tree_widget(tree_widget):
    for index in range(0, tree_widget.topLevelItemCount()):
        yield tree_widget.topLevelItem(index)

def get_child_items_from_item(item):
    return (item.child(index) for index in range(0, item.childCount()))


class ModelViewError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Model:
    def __init__(self, views=None):
        self._views = []
        if views is not None:
            for view in views:
                self._add_view(view)

    def _update_views(self, *args, **kwargs):
        for view in self._views:
            view._update_view(*args, **kwargs)

    def _add_view(self, view):
        if view in self._views:
            raise ModelViewError((
                "View {} is already observing model {} and thus,"
                " can not be added as view"
            ).format(view, model))
        self._views.append(view)

    def _remove_view(self, view):
        if view not in self._views:
            raise ModelViewError((
                "View {} is not observing model {} and thus,"
                " can not be removed as view"
            ).format(view, model))
        self._views.remove(view)

class View:
    def __init__(self, model=None):
        # Initialize the 'private' property for the setter to work, and
        # use setter afterwards invoking obeserver logic
        self._model = None
        self.model = model

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        if self._model is not None:
            self._model._remove_view(self)
        self._model = model
        self._model._add_view(self)

class DictTreeView(View):
    def __init__(self, tree_widget, model=None):
        super().__init__(model)
        self.widget = tree_widget

    def _update_view(self, dict_tree):
        #TODO rerender the tree is ineffective
        self.widget.clear()

        for key in dict_tree:
            child = QtWidgets.QTreeWidgetItem(None, [key])
            self.widget.addTopLevelItem(child)
            self._update_tree_widget(dict_tree[key], child)

    def _update_tree_widget(self, dict_tree, parent):
        if isinstance(dict_tree, dict) == True:
            for key in dict_tree:
                child = QtWidgets.QTreeWidgetItem(parent, [key])
                self._update_tree_widget(dict_tree[key], child)

    def get_items_by_depth(self, depth):
        output = []
        for item in get_top_level_items_from_tree_widget(self.widget):
            # Note, that the top level equals depth zero, thus, the next level
            # has depth 1
            output.extend(self._get_items_by_depth_rec(item, 1, depth))
        return output

    @classmethod
    def _get_items_by_depth_rec(cls, parent, depth_count, depth):
        if depth_count >= depth:
            return [parent]

        output = []
        for item in get_child_items_from_item(parent):
            output.extend(
                cls._get_items_by_depth_rec(item, depth_count + 1, depth)
            )
        return output

class EncLogTreeView(DictTreeView):
    def __init__(self, widget, model=None, is_qp_expansion_enabled=False):
        super().__init__(widget, model)
        self.is_qp_expansion_enabled = is_qp_expansion_enabled

        self.widget.itemSelectionChanged.connect(self._update_selection)

    def _update_view(self, dict_tree):
        super()._update_view(dict_tree)
        # Alter the qp items of the tree
        self._update_qp_expansion()

    @property
    def is_qp_expansion_enabled(self):
        return self._is_qp_expansion_enabled

    @is_qp_expansion_enabled.setter
    def is_qp_expansion_enabled(self, is_enabled):
        self._is_qp_expansion_enabled = is_enabled
        self._update_qp_expansion()

    def _update_qp_expansion(self):
        #TODO alter selection
        for qp_items in self.get_items_by_depth(2):
            qp_items.setChildIndicatorPolicy(
                QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless
                if self._is_qp_expansion_enabled
                else QtWidgets.QTreeWidgetItem.DontShowIndicator
            )

    def _update_selection(self):
        # Reselect items: All children of selected items are selected
        for item in get_top_level_items_from_tree_widget(self.widget):
            self._select_children_rec(item, item.isSelected())

    def _select_children_rec(self, parent, is_selected):
        for child in get_child_items_from_item(parent):
            if is_selected == True:
                child.setSelected(True)
            self._select_children_rec(child, is_selected or child.isSelected())

    def get_selected_enc_log_keys(self):
        #Get all enc_logs specified by the selection tree
        keys = []
        for sequence_item in get_top_level_items_from_tree_widget(self.widget):
            for config_item in get_child_items_from_item(sequence_item):
                for qp_item in get_child_items_from_item(config_item):
                    # Note, that this is valid, as if a parent item is checked
                    # all sub items are also selected
                    if qp_item.isSelected() == True:
                        sequence = sequence_item.text(0)
                        config = config_item.text(0)
                        qp = qp_item.text(0)
                        keys.append( (sequence, config, qp) )
        return keys

    def _get_open_file_names(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getOpenFileNames(
                self.widget,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/examplLogs",
                "Enocder Logs (*.log)")

            [directory, file_name] = result[0][0].rsplit('/', 1)
            return (directory, file_name)
        except IndexError:
            return
        else:
            #TODO usefull logging
            print("successfully added sequence")
            return

    def _get_folder(self):
        # extract folder and filename
        try:
            result = QtWidgets.QFileDialog.getExistingDirectory(
                self.widget,
                "Open Sequence Encoder Log",
                "/home/ient/Software/rd-plot-gui/examplLogs")
            return result
        except IndexError:
            return
        else:
            #TODO usefull logging
            print("successfully added sequence")
            return

    def add_encoder_log(self):
        directory, file_name = self._get_open_file_names()
        path = join(directory, file_name)

        self.model.add( model.EncLog( path ) )
    def add_sequence(self):
        directory, file_name = self._get_open_file_names()
        path = join(directory, file_name)

        encLogs = list( model.EncLog.parse_directory_for_sequence( path ) )
        self.model.update(encLogs)

    def add_folder(self):
        path = self._get_folder()

        encLogs = list( model.EncLog.parse_directory( path ) )
        self.model.update(encLogs)
