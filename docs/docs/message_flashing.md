# Message Flashing

Mojito provides a simple message flashing API similar to that in Flask.

# Simple Flashing
Here is an example, equivalent to that in Flask:
```py title="src/main.py"
from mojito import Mojito, flash_message, get_flashed_messages, Jinja2Templates, redirect_to, Request

app = Mojito()
templates = Jinja2Templates(directory="./src/templates")

@app.route('/')
def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.route('/login', methods=['GET', 'POST'])
def login(request: Request):
    error = None
    if request.method == 'POST':
        if (
            request.form['username'] != 'admin' or
            request.form['password'] != 'secret'
            ):
            error = 'Invalid credentials'
        else:
            flash_message('You were successfully logged in')
            return redirect_to(request.url_for('index'))
    return templates.TemplateResponse(request=request, name='index.html', error=error)
```

```html title="src/templates/layout.html"
<!doctype html>
<title>My Application</title>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul class=flashes>
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
{% block body %}{% endblock %}
```

And here is the `login.html` that inherits from `layout.html`:
```html title="src/layouts/login.html"
{% extends "layout.html" %}
{% block body %}
  <h1>Login</h1>
  {% if error %}
    <p class=error><strong>Error:</strong> {{ error }}
  {% endif %}
  <form method=post>
    <dl>
      <dt>Username:
      <dd><input type=text name=username value="{{
          request.form.username }}">
      <dt>Password:
      <dd><input type=password name=password>
    </dl>
    <p><input type=submit value=Login>
  </form>
{% endblock %}
```