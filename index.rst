
.. raw:: latex

  \definecolor{foobar}{gray}{0.95}
  \sphinxsetup{%
        VerbatimColor={named}{foobar},
         verbatimwithframe=false
  }

Foobar
======

.. note::

   Could I use ``tcolorbox`` to display some code?

It would be better to display code such as this, but with syntax highlight:

.. hint::

    #include <stdio.h>

    int main(int argc, char *argv[])
    {
        printf("hello, world!\n");
    }

This block is ugly, because it is wider than the page.

.. code-block:: c

    #include <stdio.h>

    int main(int argc, char *argv[])
    {
        printf("hello, world!\n");
    }
