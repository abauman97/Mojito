from typing import Callable, Any, Optional


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


class MoTemplates:
    components: dict[str, Callable[..., HTML]]
    config: dict[str, Any]

    def __init__(self) -> None:
        self.components = {}

    def register_component(self):
        "Should be a wrapper that allows for defining and registering a component."

        # Components should be protected and treated just like routes.
        def wrapper(func: Callable[..., HTML]):
            # Register a component and add it to the routes
            self.components[func.__name__] = func

            return func

        return wrapper

    def component_url(name: str) -> str:
        # Returns the route to the component
        # Used for replacing the component like hx-swap={{ component_url('some_component') }}
        pass

    def component_function(
        self, name: str, id: Optional[str] = None, **kwargs: dict[str, Any]
    ):
        """Looks up and renders a component by name. Component is given the id if it will
        be the target of any actions. The **kwargs are parameters passed to the function
        """
        pass


templates = MoTemplates()


# Template
@templates.register_component()
def base_template() -> HTML:
    pass
