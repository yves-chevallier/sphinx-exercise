
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

1. config-inited
   - Get config parameters, valid them
2.
