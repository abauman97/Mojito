# Templates
Templates are [Jinja2 Templates](https://jinja.palletsprojects.com/en/stable/templates/) under the hood with some additional features like support for fragments.

# Additional Features
These are the features on top of the base functionality provided by the Jinja2 templating engine.

## Fragments
**IN DEVELOPMENT**

Also called partials or blocks, fragments allow you to follow the Locality of Behavior design principal that allow you to render out just a *fragment* or partial part of the template, rather than the whole template. 

This is most useful when using libraries such as [HTMX](https://htmx.org/) to swap sections of the DOM at a time rather than the whole page. See Carson Gross' essay on [Template Fragments](https://htmx.org/essays/template-fragments/) for more on using this method.

### Using fragments
Take the following configuration:
```html title="number.jinja"
<html>
    <body>
        <h1>Here's the header!</h1>
        {% block content %}
        <p>The number is: {{ number }}</p>
        {% endblock %}
    </body>
</html>
```
```py title="main.py"
from mojito import Mojito, Request
from mojito.templating import Templates

app = Mojito()
templates = Templates()

@app.route("/")
def index_route(request: Request):
    return templates.TemplateResponse(request, "number.jinja", {"number": 1})

@app.route("/number_2")
def number_two_route(request: Request):
    return templates.TemplateResponse(request, "number.jinja", {"number": 2}, block="content")
```

Making a request to the `/` route will render the entire `number.jinja` template:
```html
<html>
    <body>
        <h1>Here's the header!</h1>
        {% block content %}
        <p>The number is: 1</p>
        {% endblock %}
    </body>
</html>
```
whereas calling the route `/number_2` will only return the block you specified in the TemplateResponse argument `block="content"`:
```html
<p>The number is: 2</p>
```

#### Rendering multiple fragments
Multiple fragments can be returned by passing a list of block names to the `block` argument of the TemplateResponse. This will render each of the named blocks and concatenate them into a single response. This enables easier [out-of-band updates](https://htmx.org/attributes/hx-swap-oob/) with HTMX.

#### Credits
This implementation was based off of the [jinja2-fragments](https://github.com/sponsfreixes/jinja2-fragments) library.