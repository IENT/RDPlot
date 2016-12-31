from PyQt5 import QtWidgets


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
    def model():
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
        for key in dict_tree:
            child = QtWidgets.QTreeWidgetItem(None, [key])
            self.widget.addTopLevelItem(child)
            self._update_tree_widget(dict_tree[key], child)

    def _update_tree_widget(self, dict_tree, parent):
        if isinstance(dict_tree, dict) == True:
            for key in dict_tree:
                child = QtWidgets.QTreeWidgetItem(parent, [key])
                self._update_tree_widget(dict_tree[key], child)
