# Mojito Components
A test to see how well a new component based templating module can be implemented to give
templates power similar to that of Laravels Livewire or .Nets Blazor Server.

## Basic Syntax
Components are python functions (or classes) that return html.

Components can call other components to compose them together.

Use Jinja to render the html and perform loops and conditionals.

Use HTMX to swap parts of the dom with those sent from the server.

Planned Features:
 - Bind variables from the frontend to those on the backend like Livewire
 - Syntax for including components in templates
 - Syntax for composing components together