from typing import Callable, Any, Optional
from mojito.routing import AppRouter, Route

class HTML(str):
    # HTML type. Should validate that it is valid html on init
    pass


def view(name: str) -> HTML:
    "Returns a template from a file"
    # Jinja finds a file and renders it. Used when the html is not defined inline in the component
    pass


"""
MoTemplates.components are added as "components" in the global context when rendering.

In a template using {{ component('component_name', id) }} will return a component rendered inside a
<div hx-swap="component_url" hx-trigger="load" hx-target="innerHTML" id="mo-componentName">
    <template html inserted here />
</div>

Swaps/refreshes can be triggered using regular HTMX and component_url() global function
inside of a 
"""

class MoComponent:
    components: dict[str, Callable[..., HTML]] = {}
    config: dict[str, Any]
    router = AppRouter('/mo-component', name="components")

    def register_component(        
        self,
        methods: Optional[list[str]] = ["GET"],
        include_in_schema: bool = True):
        "Should be a wrapper that allows for defining and registering a component."
        def wrapper(func: Callable[..., HTML]):
            self.components[func.__name__] = func
            
            @self.router.route(path="/" + func.__name__, methods=methods, name=func.__name__, include_in_schema=include_in_schema)
            def inner_func(*args: Any, **kwargs: dict[str, Any]):
                return func(*args, **kwargs)
            return inner_func
        return wrapper


    def component_url(name: str) -> str:
        # Returns the route to the component
        # Used for replacing the component like hx-swap={{ component_url('some_component') }}
        pass
