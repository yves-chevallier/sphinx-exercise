"""
Replace Pygments for writing highlighted code-block with
traditional LaTeX Listings environment.
"""
from docutils import nodes
from sphinx.util import logging
from sphinx.util.console import colorize
from sphinx.writers.latex import LaTeXTranslator

class MyLaTeXTranslator(LaTeXTranslator):
    def __init__(self, document, builder, theme = None):
        super().__init__(document, builder)

    def visit_literal_block(self, node):
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            self.in_parsed_literal += 1
            self.body.append('\\begin{sphinxalltt}\n')
        else:
            labels = self.hypertarget_to(node)
            if isinstance(node.parent, captioned_literal_block):
                labels += self.hypertarget_to(node.parent)
            if labels and not self.in_footnote:
                self.body.append('\n\\def\\sphinxLiteralBlockLabel{' + labels + '}')

            lang = node.get('language', 'default')
            linenos = node.get('linenos', False)
            highlight_args = node.get('highlight_args', {})
            highlight_args['force'] = node.get('force', False)
            if lang is self.builder.config.highlight_language:
                # only pass highlighter options for original language
                opts = self.builder.config.highlight_options
            else:
                opts = {}

            if self.builder.config.lino_start:
                opts += ',firstnumber=' + self.builder.config.lino_start

            hlcode = '\\begin{lstlisting}[language=%s%s]\n' % (lang,
                ',numbers=left' if self.builder.config.linenos else '',
                 if self.builder.config.linenos else '',
            )
            hlcode += node.rawsource
            hlcode += '\n\\end{lstlisting}'
            self.body.append('\n' + hlcode + '\n')
            raise nodes.SkipNode

def setup(app):
    app.set_translator('latex', MyLaTeXTranslator)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
