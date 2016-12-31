from PyQt5 import QtWidgets


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
        self._model = model

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_qp_expansion_enabled = False

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
                QtWidgets.QTreeWidgetItem.DontShowIndicator
                if self._is_qp_expansion_enabled
                else QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless
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

