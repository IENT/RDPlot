class Model:
    def __init__():
        self._observers = []
        
    def _update(self, *args, **kwargs):
        for observer in self._observers:
            observer._update(*args, **kwargs)
    
    def _add_observer(observer):
        if observer in self.observer:
            #TODO usefull exception
            raise Exception()
        self._observers.append(observer)
            
    def _remove_observer(observer):
        if observer not in self._observers:
            #TODO usefull exception
            raise Exception()
        self._observers.remove(observer)
        
class View:
    def __init__(model=None):
        if model is not None:
            self.model = model
            
    @property
    def model():
        return self.model
    
    @model.setter
    def model(model):
        if self._model is not None:
            self._model._remove_observer(self)
        self._model = self._add_observer(self)
        
        
class DictTreeModel(Model, dict)
    def __init__(self, dict_tree=None):
        super().__init__()
        
        #Initialize model by an existing dictionary tree
        if dict_tree is not None:
            self._copy_dict_tree(dict_tree)
    
    def _copy_dict_tree(self, item):
        if isinstance(item, dict):
            for key in item
                self[key] = self.copy_dict_tree( item[key] )
        return dict_tree
            
    def __setitem__(self, key, item):
        self[key] = item
        self._update()
    
class DictTreeView(View):
    def __init__(self, tree_widget, model=None):
        self.widget = tree_widget
        super().__init__(model)

    def _update():
        self._update_tree_widget(self.model, self.widget.root)
        
    def _update_tree_widget(dict_tree, parent)
        for key in dict_tree:
            child = QtWidgets.QTreeWidgetItem(parent, [key])
            self._update_tree(dict_tree[key], child)
