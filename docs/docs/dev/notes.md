# In development notes

# Forms with nested data
Form processing already accounts for basic list values but doesn't handle any kind of complex nested data. For example:

```py
class UserRole(BaseModel):
    id: int
    name: str

class User(BaseModel):
    id: int
    name: str
    email: str
    roles: list[UserRole]
```
The `User` contains a list of `UserRole`. 
To represent this the following input name format should be processed into: `list[index].property` and converted into the correct data model.

```html
<form>
    <input name="id" value="1" />
    <input name="name" value="Jacob" />
    <input name="email" value="jacob@email.com" />
    <input name="roles[0].id" value="1" />
    <input name="roles[0].name" value="read" />
    <input name="roles[1].id" value="2" />
    <input name="roles[2].name" value="read" />
</form>
```
