from mojito import Mojito
from mojito.components.main import HTML, MoComponent
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('./tests/components/'))

test_template = env.get_template('test_template.html', globals={"components": MoComponent.components})

app = Mojito()

components = MoComponent()

@components.register_component()
def component_1():
    return HTML("<p>Component 1</p>")

@app.route('/')
def render_template():
    return test_template.render()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="tests.components.test_components:app", host="localhost", port=8000, reload=True)