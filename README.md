
- Exercises labels are not labels, just text.




## Options

All the exercises are showed where they are

- `declared` Visible where they are declared
- `chapter` Visble at the end of the current chapter
- `gathered` Visible in the `.. exercises::`

```
exercise_location='declared'
```

## .. exercise::

```rst

.. exercise:: name
    :difficulty: 2

    Some question...
```

## .. solution::

Solution only valid inside exercise. Warn if declared somethere else. Only one solution per exercise.

```rst

.. solution::

    A solution


## .. excercises::

Display all excercises there

```rst
Exercises
=========

.. exercises::
    chapters: # Each exercises has its chapter
```

## .. solutions::

Display all available solutions of all exercises.

```rst

Exercises Solutions
===================

.. solutions::
    chapters:
```

## Further...

- [ ] Multiple choice answer
- [ ] Difficulty


## How it works?

```
1. `config-inited(app,config)`
    - Get config parameters, valid them
    - Register name of exercises "Exercise", sections...
2. `builder-inited(app)`
    - Builder object was created
    - n/a
3. `env-get-outdated(app, env, added, changed, removed)`
    - Emitted when source files have changed
4. `env-before-read-docs(app, env, docnames)`
    for docname in docnames:
    5. `event.env-purge-doc(app, env, docname)`
    if doc changed and not removed:
        6. source-read(app, docname, source)
        7. run source parsers: text -> docutils.document (parsers can be added with the app.add_source_parser() API)
        8. apply transforms (by priority): docutils.document -> docutils.document
            - event.doctree-read(app, doctree) is called in the middly of transforms,
            transforms come before/after this event depending on their priority.
    9. (if running in parallel mode, for each process) event.env-merged-info(app, env, docnames, other)
    10. event.env-updated(app, env)
    11. event.env-get-updated(app, env)
    11. event.env-check-consistency(app, env)

    # For builders that output a single page, they are first joined into a single doctree before post-transforms/doctree-resolved
    for docname in docnames:
    12. apply post-transforms (by priority): docutils.document -> docutils.document
    13. event.doctree-resolved(app, doctree, docname)
        - (for any reference node that fails to resolve) event.missing-reference(env, node, contnode)
14. Generate output files
15. event.build-finished(app, exception)
```
