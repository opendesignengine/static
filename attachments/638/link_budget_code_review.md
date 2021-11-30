Ground Sphere - Link Budget Code Review

#### Package Structure
The current structure is set up like a standalone application, but given
the purpose of the code, to calculate link budgets, it would see that
this would make more sense as a library. To turn this into a more standard
python library here are some of my thoughts.

The current package structure and naming is non-standard and confusing. Currently
the package name is 'lib' with the subpackage 'calculator' which tells the user
nothing about what the package does or what sort of behavior they should expect.
Renaming the package to `link_budget` lets the user, and whoever is reading
code that uses this library, what the library is about. As such I would reorganize
the package structure as so


```
link_budget/
|
├── docs/
|	├── user_guide.md
|   └── theory.md
|
├── examples/
|   ├── basic_usage.ipynb
|   └── advanced_usage.ipynb	
|
├── link_budget/
|   ├── __init__.py
|	└── link_budget.py
|
├── tests/
|   ├── unit/
|	|	└── test_link_budget.py
|	|
|	└── integration/
|		├── test_case_one.py
|		└── test_case_two.py			 
|
├── README.md
├── setup.py
├── .gitignore
└── LICENCE.txt

```

#### Docs

I typically consider IPython notebooks as a way to have nice, documented examples
so I would place notebooks in the examples, but keep the docs into a standard
documentation format, either, .pdf, .txt, or .md as currently using ODE if I want
to read the documentation on the project to see what its about, I need to download
a notebook file, and fire up `notebook`. I shouldn't have to run a program (other than a browser) just to see some documentation. If this all got moved to github
I could see the case for leaving the docs in .ipynb form because github will render
the notebook.

#### Examples

The current example in example_basic.py doesn't really show me an example of 
anything, this would be a great place for an ipython notebook to walk a new
user of the library through a standard use case and some more advanced options.

#### The Library API
The main class name 'LinkBudgetCalcuator' doesn't seem right to me, why not
just call it 'LinkBudget' because that is what it represents.

Current the 'API' for the library, is instantiate a class, call a million setters,
then call 'run' and hope things are good. I'm not a fan of the fact that the class
on instantiation is effectively in an error state, and there isn't anything guiding
the user to call all of the setters to get things to work. A better approach would
be to package related inputs into their own objects, so that the __init__ function
would look something like

```python
def __init__(self, target, receiver, environment, unit_registry=None)
```

This tells me as a user of the class, a better idea of what type of data the
class is going to be using to calculate the link budget. This also allows
for cleaner looking code, if say I want to calculate the link budget for a lot
of different targets for the same reciever, or vica-versa.

Also, while I am a big fan of pint and unit aware code, I feel like it should
be optional to use the library.

The 'run' function, isn't doing this class any favors. For one, what does run
even mean? Its not really that clear what running a link budget is. Also in
the future, what if the class gets extended into more use cases and there
are different ways to 'run' it? If the __init__ function is changed to
allow for a valid configuration, then we can drop `run` function entirely
and just do the calculation in the __init__ so that usage would look like

```python
link = LinkBudget(target, reciever, environment)
margin = link.margin
```

which is a lot cleaner. If there is a valid case for keeping the link budget
calculation separate from the __init__ function, it should at least be renamed
to what it does 'calculate_link_budget()'

The library is hardcoded to only work on Earth, what if I want to see how my
ground sphere would do on Mars?

Logging for a library this small, seems like overkill, I can never think of
a situation where I would go look at a log file to debug this code instead
of just setting a breakpoint and using a debugger.

File is too long! For what is effectively twenty lines of math we have over 700 
lines of code! Changing the __init__ and getting rid of all the setters and logging
will help, but also the documentation is overly verbose. Lines like

```python
        # Downlink Path Loss dB
        self._downlink_path_loss = -20 * math.log10(4 * math.pi * self._link_distance / self._downlink_wavelength)
```

really dont need the comment `# Downlink Path Loss dB` the code makes it pretty
obvious what is going on here. 

#### Tests

The current set of tests feel like integration tests, which is great, but there
should also be unit tests to make sure each individual piece of math is implemented correctly.

The current way the integration tests are set up means I need to do a fair ammount
of scrolling and hunting around to see what's actually going on. For me the tests
are the ultimate documentation for a library, so I would make readability paramount
here and organize each integration test into it's own separate file. While yes
it may require some rewrite of code, it would make it a lot easier to read. 

Also unittest is fine, but pyTest is more popular and easier to read / use. 

Things like this scare me (found in one of the tests)
```
	# TODO -- change these to correct tolerance assertion
```

I didn't check to see if this test fails, but it should, if the test isn't complete
it should not be committed or at least fail. 